#!/usr/bin/env python3
"""把采集契约目录提炼成「复刻蓝图」blueprint.md（仅标准库）。

输入：capture/（含 site.json 与多个 <page-id>/），或单个 <page-id>/ 目录。
输出：Markdown 蓝图 —— 先全站（token、断点、字体、库、图标、素材），再逐页（区块清单、响应式变化、动画、hover）。
蓝图是模型复刻时首先要读的文件；原始 computed.json 等只在写某个区块时按需查。

用法：
  python3 analyze_capture.py capture/ [-o capture/blueprint.md] [--max-sections 40] [--json capture/blueprint.json]

如果先运行过 map_icons.py（生成 capture/icons-map.json），图标一节会带上 Lucide / Heroicons 候选。
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import Report, read_json, write_json  # noqa: E402


# ---------- 颜色 ----------
def rgb_to_hex(value: str) -> str:
    m = re.match(r"rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)", value)
    if not m:
        return value
    r, g, b = (int(m.group(i)) for i in (1, 2, 3))
    a = m.group(4)
    hx = f"#{r:02x}{g:02x}{b:02x}"
    if a is not None and float(a) < 1:
        return f"{hx} / {float(a):.2f}"
    return hx


def luminance(value: str) -> float | None:
    m = re.match(r"rgba?\((\d+),\s*(\d+),\s*(\d+)", value)
    if not m:
        return None
    r, g, b = (int(m.group(i)) / 255 for i in (1, 2, 3))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def saturation(value: str) -> float | None:
    m = re.match(r"rgba?\((\d+),\s*(\d+),\s*(\d+)", value)
    if not m:
        return None
    r, g, b = (int(m.group(i)) / 255 for i in (1, 2, 3))
    mx, mn = max(r, g, b), min(r, g, b)
    return 0.0 if mx == 0 else (mx - mn) / mx


def is_transparent(value: str) -> bool:
    m = re.match(r"rgba\(\d+,\s*\d+,\s*\d+,\s*([\d.]+)\)", value)
    return bool(m) and float(m.group(1)) == 0


def color_role(value: str, rank: int, lum: float | None) -> str:
    if lum is None:
        return ""
    sat = saturation(value) or 0
    if lum > 0.92:
        return "背景 / 表面"
    if lum < 0.2:
        return "正文 / 深色"
    if sat < 0.25:
        return "灰度（次要文字 / 边框）"
    if rank <= 6:
        return "主色候选"
    return "辅助色"


# ---------- 载入 ----------
def load_pages(root: Path) -> tuple[list[dict], Path]:
    if (root / "manifest.json").exists():  # 单页目录
        return [{"pageId": root.name, "dir": root, "manifest": read_json(root / "manifest.json")}], root.parent
    pages = []
    for d in sorted(p for p in root.iterdir() if p.is_dir() and (p / "manifest.json").exists()):
        m = read_json(d / "manifest.json")
        if not isinstance(m, dict) or "captureMethod" not in m:  # assets/manifest.json 不是页面
            continue
        pages.append({"pageId": d.name, "dir": d, "manifest": m})
    return pages, root


def maybe(page_dir: Path, name: str):
    p = page_dir / name
    return read_json(p) if p.exists() else None


def px(v) -> str:
    return f"{v}px" if isinstance(v, (int, float)) else str(v)


def md_table(headers: list[str], rows: list[list]) -> str:
    esc = lambda s: str(s).replace("|", "\\|").replace("\n", " ")  # noqa: E731
    out = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    for r in rows:
        out.append("| " + " | ".join(esc(c) for c in r) + " |")
    return "\n".join(out)


# ---------- 站点级合并 ----------
def merge_tokens(pages: list[dict]) -> dict:
    custom: dict[str, str] = {}
    resolved: dict[str, str] = {}
    colors, sizes, weights, families, spacing, radii, shadows, gaps = Counter(), Counter(), Counter(), Counter(), Counter(), Counter(), Counter(), Counter()
    font_faces = {}
    for p in pages:
        t = maybe(p["dir"], "tokens.json")
        if not t:
            continue
        for k, v in t.get("customProperties", {}).items():
            custom.setdefault(k, v)
        for k, v in t.get("customPropertiesResolved", {}).items():
            resolved.setdefault(k, v)
        for c in t.get("colors", []):
            colors[c["value"]] += c["count"]
        for c in t.get("fontSizes", []):
            sizes[c["value"]] += c["count"]
        for c in t.get("fontWeights", []):
            weights[c["value"]] += c["count"]
        for c in t.get("fontFamilies", []):
            families[c["value"]] += c["count"]
        for c in t.get("spacing", []):
            spacing[c["value"]] += c["count"]
        for c in t.get("gaps", []):
            gaps[c["value"]] += c["count"]
        for c in t.get("radii", []):
            radii[c["value"]] += c["count"]
        for c in t.get("shadows", []):
            shadows[c["value"]] += c["count"]
        for f in t.get("fontFaces", []):
            font_faces.setdefault((f.get("family"), f.get("weight"), f.get("style")), f)
    return {
        "custom": custom,
        "resolved": resolved,
        "colors": colors,
        "sizes": sizes,
        "weights": weights,
        "families": families,
        "spacing": spacing,
        "gaps": gaps,
        "radii": radii,
        "shadows": shadows,
        "fontFaces": list(font_faces.values()),
    }


def merge_breakpoints(pages: list[dict]) -> list[tuple[str, int]]:
    c: Counter = Counter()
    for p in pages:
        s = maybe(p["dir"], "styles.json")
        for mq in (s or {}).get("mediaQueries", []):
            c[mq["condition"]] += mq["ruleCount"]
    return sorted(c.items(), key=lambda kv: -kv[1])


def merge_libs(pages: list[dict]) -> dict:
    det: dict[str, dict] = {}
    fonts, generator = set(), None
    for p in pages:
        libs = maybe(p["dir"], "libs.json")
        if not libs:
            continue
        for d in libs.get("detected", []):
            det.setdefault(d["name"], {**d, "pages": []})["pages"].append(p["pageId"])
        fonts.update(libs.get("fontLinks", []))
        generator = generator or libs.get("generator")
    return {"detected": list(det.values()), "fontLinks": sorted(fonts), "generator": generator}


def merge_icons(pages: list[dict]) -> dict:
    inline: dict[str, dict] = {}
    fonts: dict[str, dict] = {}
    sprites: dict[str, dict] = {}
    images: dict[str, dict] = {}
    for p in pages:
        ic = maybe(p["dir"], "icons.json")
        if not ic:
            continue
        for e in ic.get("inline", []):
            x = inline.setdefault(e["hash"], {**e, "pages": [], "totalCount": 0})
            x["pages"].append(p["pageId"])
            x["totalCount"] += e["count"]
            x.setdefault("file", e.get("file"))
            x["file"] = x["file"] and f"{p['pageId']}/{e.get('file')}" if e.get("file") and x["pages"][0] == p["pageId"] else x.get("file")
        for e in ic.get("fonts", []):
            x = fonts.setdefault(e["classes"] + "|" + str(e.get("ligature")), {**e, "pages": [], "totalCount": 0})
            x["pages"].append(p["pageId"])
            x["totalCount"] += e["count"]
        for e in ic.get("sprites", []):
            x = sprites.setdefault(e["href"], {**e, "pages": [], "totalCount": 0})
            x["pages"].append(p["pageId"])
            x["totalCount"] += e["count"]
        for e in ic.get("images", []):
            images.setdefault(e["src"], {**e, "pages": []})["pages"].append(p["pageId"])
    return {"inline": list(inline.values()), "fonts": list(fonts.values()), "sprites": list(sprites.values()), "images": list(images.values())}


def semantic_hint(occ: dict) -> str:
    parts = [occ.get("ariaLabel"), occ.get("title"), occ.get("dataIcon")]
    host = (occ.get("hostText") or "").strip()
    if host and len(host) <= 24:
        parts.append(host)
    if occ.get("hostHref"):
        parts.append(occ["hostHref"])
    cls = " ".join(c for c in (occ.get("classes", "") + " " + occ.get("hostClasses", "")).split() if not re.match(r"^(w-|h-|size-|text-|flex|inline|block|mr-|ml-|shrink)", c))
    if cls:
        parts.append(cls[:60])
    return " · ".join(str(x) for x in parts if x)


# ---------- 逐页 ----------
def section_rows(page: dict, viewports: list[int]) -> list[list]:
    primary = maybe(page["dir"], "sections.json") or {"sections": []}
    others = {w: maybe(page["dir"], f"sections.{w}.json") for w in viewports[1:]}
    rows = []
    for s in primary["sections"]:
        lay = s.get("layout") or {}
        layout = lay.get("mode", "flow")
        if lay.get("columns"):
            layout += f" ×{lay['columns']}"
        if lay.get("gap") and lay.get("gap") not in ("normal", "0px", "normal normal"):
            layout += f", gap {lay['gap']}"
        if lay.get("gridTemplateColumns"):
            layout += f" (`{lay['gridTemplateColumns'][:40]}`)"
        resp = []
        for w, data in others.items():
            if not data:
                continue
            match = next((x for x in data["sections"] if x["path"] == s["path"]), None)
            if match:
                ml = match.get("layout") or {}
                col = ml.get("columns")
                resp.append(f"{w}: {ml.get('mode', 'flow')}{' ×' + str(col) if col else ''} h{match['rect']['h']}")
        st = s.get("style", {})
        bg = st.get("backgroundColor", "")
        bg_s = "" if bg in ("rgba(0, 0, 0, 0)", "transparent", "") else rgb_to_hex(bg)
        counts = s.get("counts", {})
        content = ", ".join(f"{k} {v}" for k, v in counts.items() if v and k in ("links", "buttons", "images", "forms", "inputs", "listItems"))
        shot = f"screenshots/sections/{s['index']:02d}-{s['kindGuess']}.png"
        rows.append(
            [
                s["index"],
                s["kindGuess"],
                f"`{s['tag']}`" + (f" `{s['classes'][:40]}`" if s.get("classes") else ""),
                (s.get("heading") or {}).get("text", "")[:40],
                f"{s['rect']['w']}×{s['rect']['h']} @y{s['rect']['y']}",
                layout,
                (st.get("padding") or "")[:32],
                bg_s,
                content,
                "; ".join(resp),
                shot,
            ]
        )
    return rows


def animation_section(page: dict) -> str:
    a = maybe(page["dir"], "animations.json")
    h = maybe(page["dir"], "hover.json")
    if not a:
        return "_未采集_"
    out = []
    kf = a.get("keyframes", {})
    if kf:
        out.append("**@keyframes**\n")
        for name, frames in kf.items():
            used = [e for e in a.get("animatedElements", []) if name in (e.get("animationName") or "")]
            usage = (
                f"（{len(used)} 个元素：{', '.join(sorted(set(e['classes'].split()[0] if e['classes'] else e['tag'] for e in used))[:4])}"
                + (f"，{used[0]['duration']} {used[0]['timingFunction'][:40]} delay {used[0]['delay']} ×{used[0]['iterationCount']}" if used else "")
                + "）"
                if used
                else "（未在可见元素上使用）"
            )
            out.append(f"- `{name}` {usage}")
            for f in frames:
                out.append(f"  - `{f['keyText']}` → `{f['style']}`")
    tr = a.get("transitionElements", [])
    if tr:
        groups: dict[tuple, list] = defaultdict(list)
        for t in tr:
            groups[(t["property"], t["duration"], t["timingFunction"])].append(t)
        out.append("\n**transition**（按属性 / 时长 / 曲线分组）\n")
        for (prop, dur, tf), items in sorted(groups.items(), key=lambda kv: -len(kv[1]))[:12]:
            names = sorted(set((i["classes"].split()[0] if i["classes"] else i["tag"]) for i in items))
            out.append(f"- `{prop}` {dur} `{tf[:48]}` — {len(items)} 个元素：{', '.join(names[:6])}")
    sr = a.get("scrollReveal") or []
    if sr:
        out.append("\n**滚动显现**（滚动前后状态变化，复刻用 IntersectionObserver 加 class）\n")
        cls_added = Counter(c for x in sr for c in x.get("classesAdded", []))
        out.append(f"- {len(sr)} 个元素在滚动后变化；新增 class：{dict(cls_added)}")
        for x in sr[:6]:
            out.append(f"- `{x['path']}`：opacity {x['before']['opacity']}→{x['after']['opacity']}，transform `{x['before']['transform'][:40]}`→`{x['after']['transform'][:20]}`")
    elif a.get("revealCandidates"):
        out.append(f"\n滚动显现：未检测到状态变化（{a['revealCandidates']} 个候选元素在首屏就已可见，或动画库在采集前已完成）。")
    wa = a.get("webAnimations", [])
    if wa:
        kinds = Counter(w["type"] for w in wa)
        out.append(f"\n**Web Animations API**：`document.getAnimations()` 共 {len(wa)} 个（{dict(kinds)}）；JS 驱动动画（GSAP / Motion）会出现在这里而不在 @keyframes 里。")
    out.append(f"\n`prefers-reduced-motion` 规则：{a.get('prefersReducedMotionRuleCount', 0)} 条{'，复刻时保留' if a.get('prefersReducedMotionRuleCount') else '，原站没有——复刻时仍建议加上'}。")
    if h and h.get("sampled"):
        out.append(f"\n**hover 态**（{h['method']}，采样 {h['sampled']} 个，{len(h['changed'])} 个有变化）\n")
        for c in h["changed"][:14]:
            ch = "; ".join(f"{k}: `{v[0]}`→`{v[1]}`" for k, v in list(c["changes"].items())[:4])
            out.append(f"- `{c['path'][-60:]}` — {ch}")
    return "\n".join(out)


def responsive_notes(page: dict, viewports: list[int]) -> str:
    primary = maybe(page["dir"], "computed.json")
    notes = []
    for w in viewports[1:]:
        other = maybe(page["dir"], f"computed.{w}.json")
        if not primary or not other:
            continue
        by_path = {e["path"]: e for e in other["elements"]}
        hidden = [e for e in primary["elements"] if e["path"] not in by_path and e["tag"] in ("nav", "aside", "div", "ul", "section")]
        changed_display = []
        for e in primary["elements"]:
            o = by_path.get(e["path"])
            if not o:
                continue
            d1, d2 = e["styles"].get("display"), o["styles"].get("display")
            if d1 != d2:
                changed_display.append((e["path"], d1, d2))
            g1, g2 = e["styles"].get("grid-template-columns"), o["styles"].get("grid-template-columns")
            if g1 and g2 and g1.count(" ") != g2.count(" "):
                changed_display.append((e["path"], f"grid {g1.count(' ') + 1} 列", f"grid {g2.count(' ') + 1} 列"))
        body = other.get("body", {})
        tail = lambda s, n: s if len(s) <= n else "…" + s[-n:]  # noqa: E731
        notes.append(
            f"- **{w}px**：文档高 {other['viewport']['documentHeight']}px（主视口 {primary['viewport']['documentHeight']}px）；body 字号 {body.get('fontSize')}；隐藏了 {len(hidden)} 个块级元素"
            + (f"（如 `{tail(hidden[0]['path'], 50)}`）" if hidden else "")
            + (f"；布局变化 {len(changed_display)} 处：" + "; ".join(f"`{tail(p, 44)}` {a}→{b}" for p, a, b in changed_display[:4]) if changed_display else "")
        )
    return "\n".join(notes) if notes else "_只采了一个视口_"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("capture", help="capture 目录或单个页面目录")
    ap.add_argument("-o", "--out", help="蓝图输出路径（默认 <capture>/blueprint.md）")
    ap.add_argument("--json", help="同时输出结构化 JSON 到此路径")
    ap.add_argument("--max-sections", type=int, default=40)
    args = ap.parse_args()

    rep = Report()
    root = Path(args.capture)
    if not root.exists():
        rep.error(str(root), "目录不存在")
        return rep.emit(False, "analyze_capture")
    pages, site_root = load_pages(root)
    if not pages:
        rep.error(str(root), "没找到任何 <page>/manifest.json；先运行 capture_site.py 或按 capture-guide 用内联浏览器落盘")
        return rep.emit(False, "analyze_capture")
    site = maybe(site_root, "site.json") or {}
    viewports = [v["width"] for v in (site.get("viewports") or pages[0]["manifest"].get("viewports") or [{"width": 1440}])]
    out_path = Path(args.out) if args.out else site_root / "blueprint.md"

    tokens = merge_tokens(pages)
    bps = merge_breakpoints(pages)
    libs = merge_libs(pages)
    icons = merge_icons(pages)
    icon_map = maybe(site_root, "icons-map.json")
    icon_map_by_id = {i["id"]: i for i in (icon_map or {}).get("icons", [])}
    assets_manifest = maybe(site_root / "assets", "manifest.json")

    md: list[str] = []
    md.append(f"# 复刻蓝图 — {pages[0]['manifest'].get('url', '')}\n")
    md.append(
        f"采集方式：{', '.join(sorted(set(p['manifest'].get('captureMethod', '?') for p in pages)))}；页面 {len(pages)} 个；视口 {' / '.join(str(v) + 'px' for v in viewports)}；生成于 {site.get('generatedAt', pages[0]['manifest'].get('capturedAt', ''))}\n"
    )
    md.append("怎么用：先照第 1–4 节落 token、断点、字体与图标方案，再按第 6 节逐页逐区块复刻；数值一律以 `computed.json` / `sections.json` 为准，截图只用来确认观感。\n")

    # 1 页面
    md.append("## 1. 页面清单\n")
    rows = []
    for p in pages:
        m = p["manifest"]
        sec = maybe(p["dir"], "sections.json") or {}
        comp = maybe(p["dir"], "computed.json") or {}
        rows.append(
            [
                f"`{p['pageId']}`",
                m.get("url", ""),
                (m.get("title") or "")[:40],
                sec.get("count", "?"),
                comp.get("count", "?"),
                (comp.get("viewport") or {}).get("documentHeight", "?"),
                "; ".join(m.get("warnings", []))[:60],
            ]
        )
    md.append(md_table(["目录", "URL", "标题", "区块", "可见元素", "文档高", "告警"], rows) + "\n")

    # 2 token
    md.append("## 2. 设计 Token\n")
    if tokens["custom"]:
        md.append("**原站 `:root` 自定义属性**（直接沿用命名，写进 CSS 变量或 Tailwind `@theme`）\n")
        md.append(
            md_table(
                ["变量", "声明值", "解析值"],
                [[f"`{k}`", f"`{v[:60]}`", f"`{tokens['resolved'].get(k, '')[:60]}`" if tokens["resolved"].get(k, "") != v else ""] for k, v in list(tokens["custom"].items())[:80]],
            )
            + "\n"
        )
    else:
        md.append("原站没有 `:root` 自定义属性，下面的频次统计就是 token 的来源；命名由你定。\n")
    md.append("**颜色**（按加权出现频次；hex 为近似值，透明度另列）\n")
    color_rows = []
    for i, (val, cnt) in enumerate([kv for kv in tokens["colors"].most_common(24) if not is_transparent(kv[0])][:20], 1):
        color_rows.append([i, f"`{rgb_to_hex(val)}`", f"`{val}`", cnt, color_role(val, i, luminance(val))])
    md.append(md_table(["#", "hex", "原值", "权重", "角色猜测"], color_rows) + "\n")
    md.append("**字体**\n")
    md.append(md_table(["font-family（计算值）", "出现"], [[f"`{k[:80]}`", v] for k, v in tokens["families"].most_common(6)]) + "\n")
    if tokens["fontFaces"]:
        md.append(
            md_table(["@font-face family", "weight", "style", "src"], [[f["family"], f.get("weight") or "", f.get("style") or "", (f.get("src") or "")[:80]] for f in tokens["fontFaces"][:12]]) + "\n"
        )
    if libs["fontLinks"]:
        md.append("字体服务链接：" + "、".join(f"`{u}`" for u in libs["fontLinks"]) + "\n")
    sizes = sorted(((float(re.sub(r"[^\d.]", "", k) or 0), k, v) for k, v in tokens["sizes"].items()), key=lambda x: x[0])
    md.append("**字号阶梯**：" + "、".join(f"`{k}`×{v}" for _, k, v in sizes) + "\n")
    md.append("**字重**：" + "、".join(f"`{k}`×{v}" for k, v in tokens["weights"].most_common()) + "\n")
    sp = sorted(((float(re.sub(r"[^\d.]", "", k) or 0), k, v) for k, v in tokens["spacing"].items() if v >= 2), key=lambda x: x[0])
    md.append("**间距阶梯**（padding / margin，出现 ≥2 次）：" + "、".join(f"`{k}`×{v}" for _, k, v in sp[:24]) + "\n")
    if tokens["gaps"]:
        md.append("**gap**：" + "、".join(f"`{k}`×{v}" for k, v in tokens["gaps"].most_common(8)) + "\n")
    if tokens["radii"]:
        md.append("**圆角**：" + "、".join(f"`{k}`×{v}" for k, v in tokens["radii"].most_common(8)) + "\n")
    if tokens["shadows"]:
        md.append("**阴影**\n" + "\n".join(f"- `{k}` ×{v}" for k, v in tokens["shadows"].most_common(6)) + "\n")

    # 3 断点
    md.append("## 3. 断点与响应式\n")
    if bps:
        md.append(md_table(["@media 条件", "规则数"], [[f"`{c}`", n] for c, n in bps[:16]]) + "\n")
        widths = sorted({int(x) for c, _ in bps for x in re.findall(r"(\d{3,4})px", c)})
        if widths:
            md.append("断点宽度：" + "、".join(f"{w}px" for w in widths) + "。移动优先还是桌面优先看条件里 min-width / max-width 哪个多。\n")
    else:
        md.append("样式表里没有 @media（可能是 Tailwind 等把断点编进了 class，或样式被跨域拦截）。\n")

    # 4 库
    md.append("## 4. 原站技术栈与动画库\n")
    if libs["detected"]:
        md.append(md_table(["库 / 框架", "类别", "证据", "页面"], [[d["name"], d["category"], f"`{str(d['evidence'])[:70]}`", len(d["pages"])] for d in libs["detected"]]) + "\n")
        cats = {d["category"] for d in libs["detected"]}
        hints = []
        if "animation" in cats:
            hints.append("原站有 JS 动画库：滚动显现可用 IntersectionObserver 复刻，复杂时间线选 GSAP 或 Motion（见 references/animations.md）")
        if "carousel" in cats:
            hints.append("有轮播：用 Swiper / Embla，不要手写")
        if "smooth-scroll" in cats:
            hints.append("有平滑滚动库（Lenis / Locomotive）：这是观感的一部分，复刻时要么同样引入，要么明确告知用户放弃")
        if "3d" in cats:
            hints.append("有 Three.js：3D 场景不在像素复刻范围，按截图做静态替代并告知")
        if hints:
            md.append("\n".join(f"- {h}" for h in hints) + "\n")
    else:
        md.append("未识别到已知库；页面可能是纯手写 CSS / JS。\n")
    if libs.get("generator"):
        md.append(f"`<meta name=generator>`：{libs['generator']}\n")

    # 5 图标
    md.append("## 5. 图标清单\n")
    total_icons = len(icons["inline"]) + len(icons["fonts"]) + len(icons["sprites"]) + len(icons["images"])
    md.append(
        f"共 {total_icons} 个唯一图标：内联 SVG {len(icons['inline'])}、icon-font {len(icons['fonts'])}、精灵图 {len(icons['sprites'])}、图片 {len(icons['images'])}。"
        + ("已加载 `icons-map.json` 的映射候选。" if icon_map else "运行 `map_icons.py capture/` 可生成 Lucide / Heroicons 候选。")
        + "\n"
    )
    rows = []
    for e in sorted(icons["inline"], key=lambda x: -x["totalCount"]):
        occ = e["occurrences"][0] if e.get("occurrences") else {}
        mp = icon_map_by_id.get(e["id"], {})
        rows.append(
            [
                f"`{e['id']}`",
                "inline-svg" + (" stroke" if e.get("strokeBased") else " fill"),
                e["totalCount"],
                ",".join(sorted(set(e.get("sizes", [])))[:3]),
                semantic_hint(occ)[:70],
                mp.get("recommended") or mp.get("note") or ", ".join(mp.get("keywords", [])[:4]),
                e.get("file") or "",
            ]
        )
    for e in sorted(icons["fonts"], key=lambda x: -x["totalCount"]):
        occ = e["occurrences"][0] if e.get("occurrences") else {}
        mp = icon_map_by_id.get(e["id"], {})
        rows.append(
            [
                f"`{e['id']}`",
                f"icon-font {e['family']}",
                e["totalCount"],
                ",".join(sorted(set(e.get("sizes", [])))[:3]),
                (f"`{e['classes'][:40]}` " + (e.get("ligature") or "") + " " + semantic_hint(occ))[:70],
                mp.get("recommended") or ", ".join(mp.get("keywords", [])[:4]),
                "",
            ]
        )
    for e in icons["sprites"]:
        occ = e["occurrences"][0] if e.get("occurrences") else {}
        mp = icon_map_by_id.get(e["id"], {})
        rows.append(
            [
                f"`{e['id']}`",
                "svg-sprite" + ("" if e.get("symbolFound") else "（symbol 不在 DOM）"),
                e["totalCount"],
                ",".join(sorted(set(e.get("sizes", [])))[:3]),
                (e["href"] + " " + semantic_hint(occ))[:70],
                mp.get("recommended") or "",
                e.get("file") or "",
            ]
        )
    for e in icons["images"]:
        mp = icon_map_by_id.get(e["id"], {})
        rows.append([f"`{e['id']}`", "img", 1, f"{e['size']['w']}x{e['size']['h']}", (e.get("alt") or e["src"].rsplit("/", 1)[-1])[:70], mp.get("recommended") or "", e["src"][:60]])
    if rows:
        md.append(md_table(["id", "类型", "次数", "尺寸", "语义线索", "映射建议", "文件 / 来源"], rows[:80]) + "\n")
    md.append(
        "规则：全部换成所选图标库（Lucide / Heroicons / Iconify）的等价符号，映射表交用户确认；确实找不到等价的才用 `icons/*.svg` 内联。stroke 类图标优先 Lucide / Heroicons outline，fill 类优先 Heroicons solid / Phosphor fill。\n"
    )

    # 6 素材
    md.append("## 6. 素材清单\n")
    if assets_manifest:
        items = assets_manifest.get("items", {})
        by_type: Counter = Counter(v.get("type") for v in items.values())
        failed = [v for v in items.values() if "error" in v]
        md.append(f"已下载 {assets_manifest.get('summary', {}).get('downloaded', 0)} 个到 `assets/`（{dict(by_type)}），失败 {len(failed)} 个。\n")
        if failed:
            md.append("失败：\n" + "\n".join(f"- `{v['url'][:90]}` — {v['error']}" for v in failed[:10]) + "\n")
        fonts = [v for v in items.values() if v.get("type") == "font"]
        if fonts:
            md.append("字体文件：" + "、".join(f"`{v.get('family', '?')}`" + ("（404）" if "error" in v else "") for v in fonts[:8]) + "\n")
    else:
        md.append("尚未下载：`python3 download_assets.py capture/`。\n")
    md.append("**版权提示**：图片、字体、文案、Logo 是原站资产。学习 / 自用之外的场景，交付前在此逐项标注替换方案（自有素材、免版权图库、开源字体）。\n")

    # 7 逐页
    md.append("## 7. 逐页区块\n")
    for p in pages:
        m = p["manifest"]
        md.append(f"### `{p['pageId']}` — {m.get('title') or m.get('url')}\n")
        md.append(f"URL：{m.get('url')}　截图：`{p['pageId']}/screenshots/{viewports[0]}.png`（其余视口同目录）\n")
        rows = section_rows(p, viewports)
        if len(rows) > args.max_sections:
            rep.warn(p["pageId"], f"区块 {len(rows)} 个，只列前 {args.max_sections} 个")
            rows = rows[: args.max_sections]
        md.append(md_table(["#", "类型", "元素", "标题", "尺寸@y", "布局", "padding", "背景", "内容", "其他视口", "裁片"], rows) + "\n")
        md.append("**响应式变化**\n\n" + responsive_notes(p, viewports) + "\n")
        md.append("**动画与交互态**\n\n" + animation_section(p) + "\n")
        comp = maybe(p["dir"], "computed.json")
        if comp and comp.get("truncated"):
            md.append(f"> computed.json 在 {comp['count']} 个元素处截断，长页面深处的元素样式需重新采集（`--max-elements`）。\n")
        st = maybe(p["dir"], "styles.json")
        if st and st.get("blockedHrefs"):
            fetched = [s for s in st["sheets"] if s.get("fetched")]
            md.append(f"> {len(st['blockedHrefs'])} 张跨域样式表被 CSSOM 拦截，其中 {len(fetched)} 张已 fetch 回 `styles/`。\n")

    # 8 复刻顺序
    md.append("## 8. 建议的复刻顺序\n")
    md.append(
        "1. 建 token 层：第 2 节的变量 / 颜色 / 字号 / 间距 / 圆角 / 阴影 → CSS 变量或 `@theme`；字体按第 2 节 `@font-face` 与字体服务链接接入（版权见第 6 节）。\n2. 第 3 节断点 → 容器宽度与媒体查询（或 Tailwind screens）。\n3. 第 5 节图标 → 选库、确认映射表，先把图标组件层搭好。\n4. 按第 7 节每页从上到下逐区块实现：布局模式与列数、padding、背景来自表格；具体元素尺寸 / 字号 / 颜色查该页 `computed.json`（按 path 检索）。\n5. 动画：`@keyframes` 原样搬；transition 按分组写到对应选择器；滚动显现用 IntersectionObserver 切 class；hover 态照 hover.json；全部包在 `prefers-reduced-motion` 之外。\n6. 跑 `compare_pages.py` 对照原站，差异 > 阈值的区块回到第 4 步。\n"
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(md), encoding="utf-8")
    rep.info("blueprint", f"→ {out_path}（{len(pages)} 页，{sum(len(section_rows(p, viewports)) for p in pages)} 个区块，{total_icons} 个图标）")
    if args.json:
        write_json(
            Path(args.json),
            {
                "pages": [p["pageId"] for p in pages],
                "viewports": viewports,
                "tokens": {k: (dict(v) if isinstance(v, Counter) else v) for k, v in tokens.items()},
                "breakpoints": bps,
                "libs": libs,
                "icons": icons,
            },
        )
        rep.info("json", f"→ {args.json}")
    if not icon_map and total_icons:
        rep.info("next", f"python3 map_icons.py {site_root} 生成图标映射候选后重跑本脚本")
    return rep.emit(False, "analyze_capture")


if __name__ == "__main__":
    sys.exit(main())
