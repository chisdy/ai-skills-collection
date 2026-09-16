#!/usr/bin/env python3
"""用 Playwright 全量采集一个或多个页面，落盘为「采集契约目录」。

  capture/
    site.json                      页面索引、采集参数
    assets/                        素材下载（download_assets.py 生成，站点级共享）
    <page-id>/
      manifest.json                URL、视口、采集方式(script)、产出文件清单、告警
      dom.html                     渲染后的 DOM（去 script / 埋点属性）
      styles/NN-<name>.css         每张样式表的 cssText（跨域被拦的用 fetch 取回）
      styles.json                  样式表索引、@media 断点、@keyframes 名
      computed.json                主视口可见元素的计算样式 + boundingBox
      computed.<w>.json            其他视口
      tokens.json                  :root 变量、@font-face、颜色 / 字号 / 间距 / 圆角 / 阴影频次
      animations.json              @keyframes、animation / transition 元素、getAnimations、滚动显现 diff
      hover.json                   hover 态样式差异（CDP CSS.forcePseudoState）
      libs.json                    识别到的框架 / 动画库 / CSS 框架 / 图标库
      icons.json + icons/*.svg     图标清单与内联 SVG 文件
      sections.json / sections.<w>.json  区块切分
      links.json                   同域链接（--follow-nav 用）
      assets.json                  素材 URL 清单（只列不下载）
      screenshots/<w>.png          各视口全页截图；sections/NN.png 主视口区块裁片（需要 Pillow）

用法：
  python capture_site.py <url | site-map.json> -o capture/
      [--viewports 1440x900,768x1024,390x844] [--follow-nav] [--max-pages 8]
      [--no-hover] [--no-assets] [--no-screenshots] [--storage-state state.json]
      [--wait 800] [--timeout 45000] [--max-elements 1500] [--headed] [--json]

site-map.json：website-clone 的 discover_site.py 输出（{"pages":[{"url":..}]}）或任何 {"pages":[...]} / ["url", ...]。
所有页面内提取逻辑都在 collect/*.js，与内联浏览器路径共用；本脚本只负责起浏览器、滚动、注入、截图、落盘。
退出码：任一页面采集失败为 1。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import HAS_PIL, Report, load_collect_script, now_iso, page_id_for, parse_viewports, read_json, require_playwright, write_json  # noqa: E402

COLLECTORS_PRIMARY = ["dom", "styles", "tokens", "libs", "icons", "assets", "links", "computed", "sections"]
COLLECTORS_SECONDARY = ["computed", "sections"]
HOVER_PROPS = [
    "color",
    "background-color",
    "border-top-color",
    "border-top-style",
    "border-top-width",
    "box-shadow",
    "transform",
    "opacity",
    "text-decoration-line",
    "outline-color",
    "outline-style",
    "filter",
    "background-image",
    "border-radius",
    "scale",
    "translate",
]
# 这些属性只在对应的 style 不为 none 时才有意义，否则只是 currentColor 的回显
HOVER_GUARD = {"border-top-color": "border-top-style", "outline-color": "outline-style"}


def parse_pages(source: str) -> list[str]:
    p = Path(source)
    if p.exists() and p.suffix == ".json":
        data = read_json(p)
        if isinstance(data, list):
            return [x if isinstance(x, str) else x["url"] for x in data]
        pages = data.get("pages", [])
        return [x if isinstance(x, str) else x["url"] for x in pages]
    if not re.match(r"^https?://", source):
        source = "http://" + source
    return [source]


def auto_scroll(page, step_ratio: float = 0.8, pause_ms: int = 220, max_steps: int = 60) -> int:
    """按视口高度滚动到底以触发懒加载与滚动动画，再回到顶部。返回滚动步数。"""
    steps = 0
    last = -1
    for _ in range(max_steps):
        pos = page.evaluate("() => { window.scrollBy(0, Math.round(window.innerHeight * %s)); return window.scrollY; }" % step_ratio)
        page.wait_for_timeout(pause_ms)
        steps += 1
        height = page.evaluate("() => document.documentElement.scrollHeight - window.innerHeight")
        if pos == last or pos >= height - 2:
            break
        last = pos
    page.evaluate("() => window.scrollTo(0, 0)")
    page.wait_for_timeout(500)
    return steps


def goto(page, url: str, timeout: int, wait_extra: int, rep: Report, where: str) -> None:
    try:
        page.goto(url, wait_until="networkidle", timeout=timeout)
    except Exception as e:  # noqa: BLE001 - networkidle 可能因长轮询永不触发
        msg = str(e)
        if "Timeout" not in type(e).__name__ and "timeout" not in msg.lower():
            raise RuntimeError(f"打开页面失败：{msg.splitlines()[0][:200]}") from e
        rep.warn(where, f"networkidle 未在 {timeout}ms 内到达，改按 load 继续（长轮询 / 埋点心跳常见，不影响采集）")
        try:
            page.wait_for_load_state("load", timeout=timeout)
        except Exception:  # noqa: BLE001
            pass
    page.wait_for_timeout(wait_extra)


def run_collector(page, name: str, rep: Report, where: str, options: dict | None = None):
    if options:
        page.evaluate("(o) => { window.__wcOptions = o; }", options)
    try:
        return page.evaluate(load_collect_script(name))
    except Exception as e:  # noqa: BLE001
        rep.error(where, f"collect/{name}.js 执行失败：{type(e).__name__}: {str(e)[:200]}")
        return None


def save_styles(page, styles: dict, out: Path, rep: Report, where: str) -> list[dict]:
    sdir = out / "styles"
    sdir.mkdir(parents=True, exist_ok=True)
    index = []
    for i, sheet in enumerate(styles.get("sheets", [])):
        href = sheet.get("href")
        base = re.sub(r"[^A-Za-z0-9._-]+", "-", Path(urlparse(href).path).name if href else f"inline-{sheet.get('ownerTag') or 'style'}") or "sheet"
        fname = f"{i:02d}-{base[:60]}"
        if not fname.endswith(".css"):
            fname += ".css"
        text = sheet.get("cssText")
        fetched = False
        if sheet.get("blocked") and href:
            try:
                resp = page.request.get(href, timeout=20000)
                if resp.ok:
                    text = resp.text()
                    fetched = True
                else:
                    rep.warn(where, f"跨域样式表 {href} fetch 失败 HTTP {resp.status}")
            except Exception as e:  # noqa: BLE001
                rep.warn(where, f"跨域样式表 {href} fetch 失败：{type(e).__name__}")
        if text is not None:
            header = f"/* source: {href or 'inline <' + str(sheet.get('ownerTag')) + '>'}{' (fetched, CSSOM blocked)' if fetched else ''} */\n"
            (sdir / fname).write_text(header + text, encoding="utf-8")
        index.append({**{k: v for k, v in sheet.items() if k != "cssText"}, "file": f"styles/{fname}" if text is not None else None, "fetched": fetched})
    return index


def hover_sample(page, animations: dict, rep: Report, where: str, limit: int = 32) -> dict:
    """对带 transition 的元素（以及可见的 a / button）用 CDP 强制 :hover，记录样式差异。"""
    targets = []
    seen = set()
    for t in (animations or {}).get("transitionElements", []):
        if t["path"] not in seen:
            seen.add(t["path"])
            targets.append(t["path"])
    extra = page.evaluate(
        """() => {
        const cssPath = (el) => { const parts = []; while (el && el.nodeType === 1 && el !== document.documentElement) { let part = el.tagName.toLowerCase(); if (el.id && /^[A-Za-z][\\w-]*$/.test(el.id)) { parts.unshift('#' + el.id); break; } const parent = el.parentElement; if (parent) { const same = Array.from(parent.children).filter((c) => c.tagName === el.tagName); if (same.length > 1) part += `:nth-of-type(${same.indexOf(el) + 1})`; } parts.unshift(part); el = parent; } return parts.join(' > '); };
        return Array.from(document.querySelectorAll('a[href], button, [role=button], .card, [class*=card]')).filter((e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; }).slice(0, 80).map(cssPath);
    }"""
    )
    for p in extra:
        if p not in seen:
            seen.add(p)
            targets.append(p)
    targets = targets[:limit]
    result = {"method": None, "sampled": 0, "changed": [], "unchanged": 0, "errors": 0}
    if not targets:
        return result

    snapshot_js = """(sel) => {
        const el = document.querySelector(sel); if (!el) return null;
        const PROPS = %s;
        const grab = (e) => { const cs = getComputedStyle(e); const o = {}; for (const p of PROPS) o[p] = cs.getPropertyValue(p); return o; };
        const out = { self: grab(el), children: {} };
        Array.from(el.querySelectorAll('*')).slice(0, 30).forEach((c, i) => { out.children[i + ':' + c.tagName.toLowerCase()] = grab(c); });
        return out;
    }""" % json.dumps(HOVER_PROPS)

    def diff_one(b: dict, a: dict, prefix: str, changes: dict) -> None:
        for k, v in a.items():
            if b.get(k) == v:
                continue
            guard = HOVER_GUARD.get(k)
            if guard and a.get(guard, "none") == "none" and b.get(guard, "none") == "none":
                continue
            changes[f"{prefix}{k}"] = [b.get(k), v]

    def diff(before, after):
        changes: dict = {}
        if not before or not after:
            return changes
        diff_one(before["self"], after["self"], "", changes)
        for ck, cv in after["children"].items():
            diff_one(before["children"].get(ck, {}), cv, f"{ck} ", changes)
        return changes

    client = None
    try:
        client = page.context.new_cdp_session(page)
        client.send("DOM.enable")
        client.send("CSS.enable")
        doc = client.send("DOM.getDocument", {"depth": 0})
        root_id = doc["root"]["nodeId"]
        result["method"] = "cdp:CSS.forcePseudoState"
    except Exception as e:  # noqa: BLE001
        rep.warn(where, f"CDP 不可用（{type(e).__name__}），hover 采样降级为 page.hover()")
        client = None
        result["method"] = "page.hover"

    for sel in targets:
        try:
            before = page.evaluate(snapshot_js, sel)
            if before is None:
                continue
            if client:
                node = client.send("DOM.querySelector", {"nodeId": root_id, "selector": sel})
                nid = node.get("nodeId")
                if not nid:
                    continue
                client.send("CSS.forcePseudoState", {"nodeId": nid, "forcedPseudoClasses": ["hover"]})
                page.wait_for_timeout(320)  # 等过渡完成
                after = page.evaluate(snapshot_js, sel)
                client.send("CSS.forcePseudoState", {"nodeId": nid, "forcedPseudoClasses": []})
            else:
                page.hover(sel, timeout=2000)
                page.wait_for_timeout(320)
                after = page.evaluate(snapshot_js, sel)
                page.mouse.move(0, 0)
            page.wait_for_timeout(120)
            result["sampled"] += 1
            ch = diff(before, after)
            if ch:
                result["changed"].append({"path": sel, "changes": ch})
            else:
                result["unchanged"] += 1
        except Exception:  # noqa: BLE001
            result["errors"] += 1
    if client:
        try:
            client.detach()
        except Exception:  # noqa: BLE001
            pass
    return result


def crop_sections(shot_path: Path, sections: dict, out_dir: Path, dpr: float) -> int:
    if not HAS_PIL:
        return 0
    from PIL import Image  # type: ignore

    out_dir.mkdir(parents=True, exist_ok=True)
    img = Image.open(shot_path)
    n = 0
    for s in sections.get("sections", []):
        r = s["rect"]
        box = (int(r["x"] * dpr), int(r["y"] * dpr), int((r["x"] + r["w"]) * dpr), int((r["y"] + r["h"]) * dpr))
        box = (max(0, box[0]), max(0, box[1]), min(img.width, box[2]), min(img.height, box[3]))
        if box[2] - box[0] < 4 or box[3] - box[1] < 4:
            continue
        img.crop(box).save(out_dir / f"{s['index']:02d}-{s['kindGuess']}.png")
        n += 1
    return n


def capture_page(browser, url: str, page_dir: Path, viewports: list[dict], args, rep: Report, storage_state) -> dict:
    where = url
    page_dir.mkdir(parents=True, exist_ok=True)
    (page_dir / "screenshots").mkdir(exist_ok=True)
    manifest = {"url": url, "pageId": page_dir.name, "captureMethod": "script", "tool": "playwright-python", "capturedAt": now_iso(), "viewports": viewports, "files": [], "warnings": []}
    links_result = None
    for vi, vp in enumerate(viewports):
        primary = vi == 0
        ctx = browser.new_context(viewport=vp, device_scale_factor=1, locale=args.locale, storage_state=storage_state, user_agent=None, reduced_motion="no-preference")
        page = ctx.new_page()
        page.set_default_timeout(args.timeout)
        goto(page, url, args.timeout, args.wait, rep, where)
        w = vp["width"]
        if primary:
            run_collector(page, "animations", rep, where)  # phase=before，滚动前的快照
        steps = auto_scroll(page)
        if primary:
            anim = run_collector(page, "animations", rep, where)  # phase=after，含 scrollReveal diff
            if anim is not None:
                write_json(page_dir / "animations.json", anim)
                manifest["files"].append("animations.json")
            for name in COLLECTORS_PRIMARY:
                data = run_collector(page, name, rep, where, {"maxElements": args.max_elements} if name == "computed" else None)
                if data is None:
                    continue
                if name == "dom":
                    (page_dir / "dom.html").write_text(data["doctype"] + "\n" + data["html"], encoding="utf-8")
                    manifest["files"].append("dom.html")
                    manifest["title"] = data.get("title")
                    manifest["lang"] = data.get("lang")
                    manifest["meta"] = data.get("meta")
                elif name == "styles":
                    data["sheets"] = save_styles(page, data, page_dir, rep, where)
                    write_json(page_dir / "styles.json", data)
                    manifest["files"] += ["styles.json", "styles/"]
                elif name == "icons":
                    idir = page_dir / "icons"
                    idir.mkdir(exist_ok=True)
                    for ic in data.get("inline", []):
                        (idir / f"{ic['id']}.svg").write_text(ic["markup"], encoding="utf-8")
                        ic["file"] = f"icons/{ic['id']}.svg"
                    for sp in data.get("sprites", []):
                        if sp.get("symbolMarkup"):
                            (idir / f"{sp['id']}.svg").write_text(sp["symbolMarkup"], encoding="utf-8")
                            sp["file"] = f"icons/{sp['id']}.svg"
                    write_json(page_dir / "icons.json", data)
                    manifest["files"] += ["icons.json", "icons/"]
                elif name == "links":
                    links_result = data
                    write_json(page_dir / "links.json", data)
                    manifest["files"].append("links.json")
                else:
                    write_json(page_dir / f"{name}.json", data)
                    manifest["files"].append(f"{name}.json")
                    if name == "computed" and data.get("truncated"):
                        rep.warn(where, f"computed.json 达到上限 {args.max_elements} 个元素，已截断；需要更多用 --max-elements")
                    if name == "sections":
                        sections_primary = data
            if not args.no_hover:
                hover = hover_sample(page, anim, rep, where)
                write_json(page_dir / "hover.json", hover)
                manifest["files"].append("hover.json")
                if hover.get("method") == "page.hover":
                    manifest["warnings"].append("hover 采样用了 page.hover() 降级路径")
        else:
            for name in COLLECTORS_SECONDARY:
                data = run_collector(page, name, rep, where, {"maxElements": max(400, args.max_elements // 2)} if name == "computed" else None)
                if data is not None:
                    write_json(page_dir / f"{name}.{w}.json", data)
                    manifest["files"].append(f"{name}.{w}.json")
        if not args.no_screenshots:
            shot = page_dir / "screenshots" / f"{w}.png"
            try:
                page.screenshot(path=str(shot), full_page=True, animations="disabled", caret="hide")
                manifest["files"].append(f"screenshots/{w}.png")
                if primary and "sections_primary" in locals() and sections_primary:
                    n = crop_sections(shot, sections_primary, page_dir / "screenshots" / "sections", 1.0)
                    if n:
                        manifest["files"].append("screenshots/sections/")
                    elif not HAS_PIL:
                        manifest["warnings"].append("未安装 Pillow，跳过区块裁片")
            except Exception as e:  # noqa: BLE001
                rep.warn(where, f"{w}px 截图失败：{type(e).__name__}")
        manifest.setdefault("scrollSteps", {})[str(w)] = steps
        ctx.close()
    write_json(page_dir / "manifest.json", manifest)
    return {"url": url, "pageId": page_dir.name, "title": manifest.get("title"), "links": links_result}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", help="URL 或 site-map.json")
    ap.add_argument("-o", "--out", default="capture", help="输出目录（默认 ./capture）")
    ap.add_argument("--viewports", default="1440x900,768x1024,390x844", help="逗号分隔的 WxH，第一个为主视口")
    ap.add_argument("--follow-nav", action="store_true", help="从首个页面的主导航抽同域链接继续采集")
    ap.add_argument("--max-pages", type=int, default=8)
    ap.add_argument("--no-hover", action="store_true")
    ap.add_argument("--no-assets", action="store_true", help="不调用 download_assets.py")
    ap.add_argument("--no-screenshots", action="store_true")
    ap.add_argument("--storage-state", help="Playwright storage state JSON（登录态）")
    ap.add_argument("--wait", type=int, default=800, help="页面加载后额外等待 ms")
    ap.add_argument("--timeout", type=int, default=45000)
    ap.add_argument("--max-elements", type=int, default=1500)
    ap.add_argument("--locale", default="zh-CN")
    ap.add_argument("--headed", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    sync_playwright = require_playwright()
    rep = Report()
    try:
        viewports = parse_viewports(args.viewports)
    except ValueError as e:
        rep.error("args", str(e))
        return rep.emit(args.json, "capture_site")
    urls = parse_pages(args.source)
    if not urls:
        rep.error("args", "没有可采集的 URL")
        return rep.emit(args.json, "capture_site")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    storage_state = args.storage_state if args.storage_state else None

    taken: set[str] = set()
    pages_done = []
    t0 = time.time()
    with sync_playwright() as pw:
        try:
            browser = pw.chromium.launch(headless=not args.headed)
        except Exception as e:  # noqa: BLE001
            rep.error("playwright", f"启动 Chromium 失败：{e}\n运行 `playwright install chromium`")
            return rep.emit(args.json, "capture_site")
        queue = list(urls)
        seen_urls = set()
        while queue and len(pages_done) < args.max_pages:
            url = queue.pop(0)
            if url in seen_urls:
                continue
            seen_urls.add(url)
            page_dir = out / page_id_for(url, taken)
            try:
                info = capture_page(browser, url, page_dir, viewports, args, rep, storage_state)
            except Exception as e:  # noqa: BLE001
                rep.error(url, f"采集失败：{type(e).__name__}: {str(e)[:300]}")
                continue
            pages_done.append({k: v for k, v in info.items() if k != "links"})
            rep.info(url, f"→ {page_dir}")
            if args.follow_nav and info.get("links"):
                origin = urlparse(url).netloc
                for lk in info["links"].get("links", []):
                    if lk.get("sameOrigin") and lk.get("inMainNav") and urlparse(lk["url"]).netloc == origin and lk["url"] not in seen_urls:
                        queue.append(lk["url"])
                hints = info["links"].get("spaHints", {})
                if info["links"].get("sameOrigin", 0) < 3 and (hints.get("emptyRoot") or hints.get("moduleScripts")):
                    rep.warn(url, "同域链接极少且像 SPA：导航可能在交互后才渲染，考虑加大 --wait 或用内联浏览器手动展开菜单后再采")
        browser.close()

    write_json(
        out / "site.json",
        {
            "generatedAt": now_iso(),
            "source": args.source,
            "viewports": viewports,
            "options": {k: v for k, v in vars(args).items() if k not in ("json",)},
            "pages": pages_done,
            "elapsedSec": round(time.time() - t0, 1),
        },
    )
    rep.info("site", f"{len(pages_done)} 个页面 → {out / 'site.json'}（{round(time.time() - t0, 1)}s）")

    if not args.no_assets and pages_done:
        import subprocess

        cmd = [sys.executable, str(Path(__file__).with_name("download_assets.py")), str(out)]
        rep.info("assets", "运行 " + " ".join(cmd[1:]))
        r = subprocess.run(cmd, capture_output=True, text=True)
        for line in (r.stdout or "").splitlines():
            if line.startswith("[ERROR]"):
                rep.warn("assets", line[8:].strip())
        if r.returncode not in (0, 1):
            rep.warn("assets", f"download_assets.py 退出码 {r.returncode}：{(r.stderr or '')[:200]}")
    rep.info("next", f"python analyze_capture.py {out} -o {out / 'blueprint.md'}")
    return rep.emit(args.json, "capture_site")


if __name__ == "__main__":
    sys.exit(main())
