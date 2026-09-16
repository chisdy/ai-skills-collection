#!/usr/bin/env python3
"""原站 vs 复刻页的校验：像素差异、区块 boundingBox 偏差、404 资源、字体回退。

  python compare_pages.py <原站 URL> <本地 URL> [-o compare/] [--viewports 1440x900,768x1024,390x844]
                          [--threshold 3] [--section-tolerance 8] [--map pages.json] [--json]

多页：--map pages.json 形如 [{"original": "https://site/", "local": "http://localhost:5173/"}, ...]；给了 --map 时前两个位置参数可省略为 "-"。
输出：compare/<page>/<w>.original.png、<w>.local.png、<w>.diff.png（热力图）与 compare/compare-report.md。

级别：
  ERROR  像素差异 > threshold%，或本地页有 4xx/5xx 资源，或标题字体回退到系统字体
  WARN   像素差异 > threshold/2，或区块 boundingBox 偏差 > section-tolerance px，或区块数量不一致
  INFO   其余

需要 Playwright；像素对比需要 Pillow（没有则只做区块 / 资源 / 字体检查并 WARN）。
无 Python 时的降级：用内联浏览器对两边各截一张图肉眼比，再对两边各跑一次 collect/sections.js 比 rect。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import HAS_PIL, Report, load_collect_script, now_iso, page_id_for, parse_viewports, read_json, require_playwright, write_json  # noqa: E402

FONT_PROBE = """() => {
  const pick = (sel) => { const el = document.querySelector(sel); if (!el) return null; const cs = getComputedStyle(el); return { family: cs.fontFamily, size: cs.fontSize, weight: cs.fontWeight }; };
  const fonts = [];
  try { document.fonts.forEach((f) => fonts.push({ family: f.family.replace(/^["']|["']$/g, ''), status: f.status, weight: f.weight })); } catch (e) {}
  return { body: pick('body'), h1: pick('h1'), h2: pick('h2'), p: pick('p'), a: pick('a'), button: pick('button'), fonts, height: document.documentElement.scrollHeight };
}"""


def settle(page, timeout: int) -> None:
    try:
        page.wait_for_load_state("networkidle", timeout=timeout)
    except Exception:  # noqa: BLE001
        pass
    # 滚到底触发懒加载 / 滚动显现，再回顶
    page.evaluate(
        """async () => { const step = Math.max(300, window.innerHeight * 0.8); for (let y = 0; y < document.documentElement.scrollHeight; y += step) { window.scrollTo(0, y); await new Promise(r => setTimeout(r, 120)); } window.scrollTo(0, 0); await new Promise(r => setTimeout(r, 400)); }"""
    )


def open_page(browser, url: str, vp: dict, timeout: int, collect_failures: bool):
    ctx = browser.new_context(viewport=vp, device_scale_factor=1, reduced_motion="reduce")
    page = ctx.new_page()
    failures: list[dict] = []
    if collect_failures:
        page.on("response", lambda r: failures.append({"url": r.url, "status": r.status, "type": r.request.resource_type}) if r.status >= 400 else None)
        page.on("requestfailed", lambda r: failures.append({"url": r.url, "status": None, "error": r.failure, "type": r.resource_type}))
    page.goto(url, wait_until="load", timeout=timeout)
    settle(page, timeout)
    return ctx, page, failures


def pixel_diff(a_path: Path, b_path: Path, out_path: Path, tolerance: int = 24) -> dict:
    from PIL import Image, ImageChops  # type: ignore

    a = Image.open(a_path).convert("RGB")
    b = Image.open(b_path).convert("RGB")
    w = max(a.width, b.width)
    h = max(a.height, b.height)
    if (a.width, a.height) != (w, h):
        canvas = Image.new("RGB", (w, h), (255, 0, 255))
        canvas.paste(a, (0, 0))
        a = canvas
    if (b.width, b.height) != (w, h):
        canvas = Image.new("RGB", (w, h), (255, 0, 255))
        canvas.paste(b, (0, 0))
        b = canvas
    diff = ImageChops.difference(a, b).convert("L")
    mask = diff.point(lambda v: 255 if v > tolerance else 0)
    hist = mask.histogram()
    changed = hist[255]
    total = w * h
    pct = changed / total * 100 if total else 0
    # 热力图：原图灰度 + 红色差异
    base = a.convert("L").convert("RGB").point(lambda v: int(v * 0.55 + 100))
    red = Image.new("RGB", (w, h), (230, 40, 40))
    heat = Image.composite(red, base, mask)
    heat.save(out_path)
    # 差异集中在哪些行（按 100px 带统计），帮助定位区块
    bands = []
    band_h = 100
    for y in range(0, h, band_h):
        strip = mask.crop((0, y, w, min(h, y + band_h)))
        c = strip.histogram()[255]
        if c:
            bands.append({"y": y, "h": min(band_h, h - y), "pct": round(c / (w * min(band_h, h - y)) * 100, 2)})
    bands.sort(key=lambda x: -x["pct"])
    return {
        "pct": round(pct, 3),
        "changedPixels": changed,
        "size": [w, h],
        "sizeOriginal": [Image.open(a_path).width, Image.open(a_path).height],
        "sizeLocal": [Image.open(b_path).width, Image.open(b_path).height],
        "hotBands": bands[:6],
        "heatmap": str(out_path),
    }


def match_sections(orig: dict, local: dict) -> list[dict]:
    o = orig.get("sections", [])
    loc = local.get("sections", [])
    rows = []
    used = set()
    for s in o:
        best, best_score = None, 1e9
        for j, t in enumerate(loc):
            if j in used:
                continue
            score = (
                abs(s["rect"]["y"] - t["rect"]["y"]) + (0 if s["kindGuess"] == t["kindGuess"] else 300) + (0 if (s.get("heading") or {}).get("text") == (t.get("heading") or {}).get("text") else 80)
            )
            if score < best_score:
                best, best_score = j, score
        if best is None:
            rows.append({"original": s, "local": None})
            continue
        used.add(best)
        t = loc[best]
        rows.append(
            {"original": s, "local": t, "dx": t["rect"]["x"] - s["rect"]["x"], "dy": t["rect"]["y"] - s["rect"]["y"], "dw": t["rect"]["w"] - s["rect"]["w"], "dh": t["rect"]["h"] - s["rect"]["h"]}
        )
    for j, t in enumerate(loc):
        if j not in used:
            rows.append({"original": None, "local": t})
    return rows


def first_family(f: str | None) -> str:
    if not f:
        return ""
    return f.split(",")[0].strip().strip('"').strip("'")


def compare_pair(browser, original: str, local: str, viewports: list[dict], out_dir: Path, args, rep: Report) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    result = {"original": original, "local": local, "viewports": {}}
    for vp in viewports:
        w = vp["width"]
        where = f"{urlparse(local).path or '/'} @{w}"
        try:
            ctx_o, page_o, _ = open_page(browser, original, vp, args.timeout, False)
            ctx_l, page_l, failures = open_page(browser, local, vp, args.timeout, True)
        except Exception as e:  # noqa: BLE001
            rep.error(where, f"打开页面失败：{str(e).splitlines()[0][:160]}")
            continue
        shot_o = out_dir / f"{w}.original.png"
        shot_l = out_dir / f"{w}.local.png"
        page_o.screenshot(path=str(shot_o), full_page=True, animations="disabled", caret="hide")
        page_l.screenshot(path=str(shot_l), full_page=True, animations="disabled", caret="hide")
        vres: dict = {"screenshots": {"original": str(shot_o), "local": str(shot_l)}}

        if HAS_PIL:
            d = pixel_diff(shot_o, shot_l, out_dir / f"{w}.diff.png")
            vres["pixel"] = d
            lvl = rep.error if d["pct"] > args.threshold else rep.warn if d["pct"] > args.threshold / 2 else rep.info
            hot = "；差异最集中：" + ", ".join(f"y{b['y']}–{b['y'] + b['h']} {b['pct']}%" for b in d["hotBands"][:3]) if d["hotBands"] else ""
            size_note = "" if d["sizeOriginal"] == d["sizeLocal"] else f"；页面尺寸不同 原 {d['sizeOriginal'][0]}×{d['sizeOriginal'][1]} / 本地 {d['sizeLocal'][0]}×{d['sizeLocal'][1]}"
            lvl(where, f"像素差异 {d['pct']}%（阈值 {args.threshold}%）{size_note}{hot} → {Path(d['heatmap']).name}")
        else:
            rep.warn(where, "未安装 Pillow，跳过像素差异；两张截图已保存，请肉眼比对")

        try:
            sec_o = page_o.evaluate(load_collect_script("sections"))
            sec_l = page_l.evaluate(load_collect_script("sections"))
            rows = match_sections(sec_o, sec_l)
            vres["sections"] = rows
            if sec_o["count"] != sec_l["count"]:
                rep.warn(where, f"区块数量不一致：原 {sec_o['count']} / 本地 {sec_l['count']}")
            off = [r for r in rows if r.get("local") and r.get("original") and max(abs(r["dx"]), abs(r["dy"]), abs(r["dw"]), abs(r["dh"])) > args.section_tolerance]
            for r in off[:8]:
                s = r["original"]
                rep.warn(
                    where,
                    f"区块 #{s['index']} {s['kindGuess']}「{(s.get('heading') or {}).get('text', '')[:20]}」偏差 dx {r['dx']} dy {r['dy']} dw {r['dw']} dh {r['dh']}（原 {s['rect']['w']}×{s['rect']['h']} @y{s['rect']['y']}）",
                )
            missing = [r["original"] for r in rows if r.get("original") and not r.get("local")]
            for s in missing[:5]:
                rep.warn(where, f"原站区块 #{s['index']} {s['kindGuess']}「{(s.get('heading') or {}).get('text', '')[:20]}」在本地没有对应区块")
            if not off and not missing and sec_o["count"] == sec_l["count"]:
                rep.info(where, f"{sec_o['count']} 个区块位置尺寸均在 ±{args.section_tolerance}px 内")
        except Exception as e:  # noqa: BLE001
            rep.warn(where, f"区块对比失败：{type(e).__name__}")

        fails_by_url: dict[str, dict] = {}
        for f in failures:
            if (f.get("status") and f["status"] >= 400) or f.get("error"):
                fails_by_url.setdefault(f["url"], f)  # 同一 URL 的 404 与 ERR_ABORTED 只报一次
        fails = list(fails_by_url.values())
        vres["resourceFailures"] = fails
        for f in fails[:10]:
            (rep.error if f.get("type") in ("document", "stylesheet", "script", "image", "font") else rep.warn)(where, f"本地资源 {f.get('status') or f.get('error')}：{f['url'][:120]}")

        try:
            fo = page_o.evaluate(FONT_PROBE)
            fl = page_l.evaluate(FONT_PROBE)
            vres["fonts"] = {"original": fo, "local": fl}
            for key in ("body", "h1", "h2", "p", "button"):
                a, b = fo.get(key), fl.get(key)
                if a and b:
                    if first_family(a["family"]).lower() != first_family(b["family"]).lower():
                        (rep.error if key in ("h1", "body") else rep.warn)(where, f"{key} 字体族不同：原 `{first_family(a['family'])}` / 本地 `{first_family(b['family'])}`")
                    elif a["size"] != b["size"] or a["weight"] != b["weight"]:
                        rep.warn(where, f"{key} 字号 / 字重不同：原 {a['size']} {a['weight']} / 本地 {b['size']} {b['weight']}")
            bad_fonts = [f for f in fl.get("fonts", []) if f["status"] == "error"]
            for f in bad_fonts[:5]:
                rep.error(where, f"本地字体加载失败（回退到系统字体）：{f['family']} {f['weight']}")
            if abs(fo["height"] - fl["height"]) > 40:
                rep.warn(where, f"文档高度差 {fl['height'] - fo['height']}px（原 {fo['height']} / 本地 {fl['height']}）——通常是某个区块 padding 或内容缺失")
        except Exception as e:  # noqa: BLE001
            rep.warn(where, f"字体检查失败：{type(e).__name__}")

        result["viewports"][str(w)] = vres
        ctx_o.close()
        ctx_l.close()
    return result


def write_report(out: Path, results: list[dict], rep: Report, args) -> Path:
    md = [f"# 复刻校验报告\n\n生成于 {now_iso()}；阈值 像素 {args.threshold}% / 区块 ±{args.section_tolerance}px\n"]
    md.append(
        f"**结论**：{rep.errors} 个阻塞项（ERROR）、{rep.warnings} 个重要项（WARN）。{'先修 ERROR 再回到区块复刻。' if rep.errors else '可以交付；WARN 按优先级处理。' if rep.warnings else '通过。'}\n"
    )
    for r in results:
        md.append(f"## {r['local']}\n\n原站：{r['original']}\n")
        rows = []
        for w, v in r["viewports"].items():
            px = v.get("pixel") or {}
            secs = v.get("sections") or []
            off = sum(1 for s in secs if s.get("local") and s.get("original") and max(abs(s["dx"]), abs(s["dy"]), abs(s["dw"]), abs(s["dh"])) > args.section_tolerance)
            rows.append([w, f"{px.get('pct', 'n/a')}%", f"{len(secs)}（偏差 {off}）", len(v.get("resourceFailures") or []), Path(px["heatmap"]).name if px else "—"])
        md.append("| 视口 | 像素差异 | 区块（超差） | 资源失败 | 热力图 |\n|---|---|---|---|---|\n" + "\n".join("| " + " | ".join(str(c) for c in row) + " |" for row in rows) + "\n")
        for w, v in r["viewports"].items():
            secs = [s for s in (v.get("sections") or []) if s.get("original") and s.get("local")]
            if secs:
                md.append(f"<details><summary>{w}px 区块对照</summary>\n\n| # | 类型 | 标题 | 原 rect | dx | dy | dw | dh |\n|---|---|---|---|---|---|---|---|")
                for s in secs:
                    o = s["original"]
                    flag = " ⚠" if max(abs(s["dx"]), abs(s["dy"]), abs(s["dw"]), abs(s["dh"])) > args.section_tolerance else ""
                    md.append(
                        f"| {o['index']} | {o['kindGuess']} | {(o.get('heading') or {}).get('text', '')[:24]} | {o['rect']['w']}×{o['rect']['h']} @y{o['rect']['y']} | {s['dx']} | {s['dy']} | {s['dw']} | {s['dh']}{flag} |"
                    )
                md.append("\n</details>\n")
    md.append("## 全部发现\n")
    for f in rep.findings:
        md.append(f"- **{f.level}** `{f.where}` {f.message}")
    path = out / "compare-report.md"
    path.write_text("\n".join(md) + "\n", encoding="utf-8")
    return path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("original", nargs="?", default="-")
    ap.add_argument("local", nargs="?", default="-")
    ap.add_argument("-o", "--out", default="compare")
    ap.add_argument("--map", help="多页映射 JSON：[{original, local}, ...]")
    ap.add_argument("--viewports", default="1440x900,768x1024,390x844")
    ap.add_argument("--threshold", type=float, default=3.0, help="像素差异 ERROR 阈值（百分比）")
    ap.add_argument("--section-tolerance", type=int, default=8)
    ap.add_argument("--timeout", type=int, default=45000)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    sync_playwright = require_playwright()
    rep = Report()
    pairs = []
    if args.map:
        for item in read_json(Path(args.map)):
            pairs.append((item["original"], item["local"]))
    if args.original != "-" and args.local != "-":
        pairs.insert(0, (args.original, args.local))
    if not pairs:
        rep.error("args", "需要 <原站 URL> <本地 URL> 或 --map pages.json")
        return rep.emit(args.json, "compare_pages")
    viewports = parse_viewports(args.viewports)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    if not HAS_PIL:
        rep.warn("env", "未安装 Pillow：pip install pillow 后可得到像素差异与热力图")

    results = []
    taken: set[str] = set()
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for original, local in pairs:
            pid = page_id_for(local, taken)
            results.append(compare_pair(browser, original, local, viewports, out / pid, args, rep))
        browser.close()
    write_json(
        out / "compare.json", {"generatedAt": now_iso(), "threshold": args.threshold, "sectionTolerance": args.section_tolerance, "results": results, "findings": [f.__dict__ for f in rep.findings]}
    )
    report = write_report(out, results, rep, args)
    rep.info("report", f"→ {report}")
    return rep.emit(args.json, "compare_pages")


if __name__ == "__main__":
    sys.exit(main())
