#!/usr/bin/env python3
"""Check custom glyph assets that the system recolours as template images:
macOS menu bar extras (status items), Home Screen quick action icons, custom
tab bar / toolbar glyphs, watch complication images.

A template image only contributes its alpha channel; the system paints the
shape in the right colour for light / dark menu bars, selection, tint. That is
why these assets must be (a) marked as template in the asset catalog or via
`isTemplate`, (b) monochrome, (c) the right point size, and (d) either vector
or supplied at @1x and @2x.

Usage:
  python3 check_template_images.py <Assets.xcassets | Foo.imageset ...>
        [--kind menubar|quickaction|tabbar|toolbar|complication|generic]
        [--filter REGEX]   only imagesets whose path matches (default: all)
        [--json]

Examples:
  python3 check_template_images.py MyApp/Assets.xcassets --kind menubar --filter "MenuBar|Status"
  python3 check_template_images.py MyApp/Assets.xcassets/QuickAction-New.imageset --kind quickaction

Exit code 1 when any ERROR is found. Standard library only; Pillow enables the
monochrome / transparency checks.
"""

from __future__ import annotations

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import HAS_PIL, Report, alpha_stats, die, is_monochrome, load_json, open_image, read_png_header  # noqa: E402

KIND_SPECS = {
    # kind: (max_pt_height, recommended (lo, hi) for the glyph's longer side, note)
    "menubar": (22, (16, 18), "菜单栏 extra 工作区固定 22pt 高（菜单栏本身 24pt）；圆形图形 16–18pt 与系统图标视觉重量一致"),
    "quickaction": (35, (35, 35), "主屏快捷操作图标模板为 35x35pt，单色 template"),
    "tabbar": (30, (23, 25), "Tab Bar 常规尺寸：圆形 25pt / 方形 23pt；紧凑（横屏 iPhone）圆形 18pt / 方形 17pt；优先用 SF Symbols"),
    "toolbar": (28, (24, 28), "Toolbar / Navigation Bar 图形约 24pt（命中区 ≥ 28pt）；优先用 SF Symbols"),
    "complication": (None, None, "复杂功能图像尺寸随表壳与模板变化，见 HIG Complications 表；线宽 ≥ 2pt；透明区域决定着色"),
    "generic": (None, None, "通用模板图：单色 + template 渲染意图"),
}


def find_imagesets(paths: list[str], pattern: re.Pattern | None):
    for p in paths:
        p = p.rstrip("/")
        if p.endswith(".imageset") and os.path.isdir(p):
            if not pattern or pattern.search(p):
                yield p
            continue
        for root, dirs, _files in os.walk(p):
            for d in list(dirs):
                full = os.path.join(root, d)
                if d.endswith(".imageset") and (not pattern or pattern.search(full)):
                    yield full
            dirs[:] = [d for d in dirs if not d.endswith((".imageset", ".appiconset", ".symbolset", ".colorset"))]


def scale_of(entry: dict) -> int:
    m = re.match(r"(\d+)x", entry.get("scale", "") or "")
    return int(m.group(1)) if m else 0  # 0 == vector / single-scale


def check_imageset(path: str, kind: str, rep: Report) -> None:
    cj = os.path.join(path, "Contents.json")
    if not os.path.exists(cj):
        rep.error(path, "缺少 Contents.json")
        return
    data = load_json(cj)
    props = data.get("properties", {}) or {}
    images = data.get("images", []) or []
    name = os.path.basename(path)
    max_pt, rec, note = KIND_SPECS[kind]

    intent = props.get("template-rendering-intent")
    if intent != "template":
        if kind in ("menubar", "quickaction", "complication"):
            rep.warn(name, "Contents.json 未设置 \"template-rendering-intent\": \"template\"；除非代码里对每个 NSImage 设了 isTemplate = true，"
                           "否则深色菜单栏 / 选中态 / 快捷操作菜单里颜色不会跟随系统")
        else:
            rep.info(name, "未标记为 template；系统组件（Tab Bar / Toolbar）会自动按 template 着色，自定义视图里请自行确认")

    scales = set()
    vector = False
    for e in images:
        fn = e.get("filename")
        if not fn:
            continue
        fp = os.path.join(path, fn)
        ext = os.path.splitext(fn)[1].lower()
        sc = scale_of(e)
        wc = e.get("width-class")
        where = f"{name}/{fn}"
        if not os.path.exists(fp):
            rep.error(where, "Contents.json 引用的文件不存在")
            continue
        if ext in (".pdf", ".svg"):
            vector = True
            if not props.get("preserves-vector-representation"):
                rep.info(name, "矢量素材未开启 preserves-vector-representation：Xcode 会在构建时栅格化为固定尺寸，运行时放大会模糊")
            continue
        if ext != ".png":
            rep.warn(where, f"格式 {ext}：模板图请用 PDF / SVG（矢量）或 PNG（@1x+@2x）")
            continue
        scales.add(sc or 1)
        hdr = read_png_header(fp)
        if not hdr:
            rep.error(where, "PNG 读取失败")
            continue
        s = sc or 1
        w_pt, h_pt = hdr["width"] / s, hdr["height"] / s
        if max_pt and h_pt > max_pt:
            rep.error(where, f"高 {h_pt:g}pt（{hdr['height']}px @{s}x）超过 {kind} 的上限 {max_pt}pt，会被裁切或缩放")
        if rec:
            lo, hi = rec
            if kind == "tabbar" and wc == "compact":
                lo, hi = 17, 18
            longer = max(w_pt, h_pt)
            if longer < lo - 3 or longer > hi + 3:
                rep.warn(where, f"图形 {w_pt:g}x{h_pt:g}pt，{kind} 推荐约 {lo}–{hi}pt（{note}）")
        if kind == "menubar" and (hdr["width"] != hdr["height"]) and abs(w_pt - h_pt) > 6:
            rep.info(where, f"非正方形 {w_pt:g}x{h_pt:g}pt：菜单栏项可以是非方形，但请用 variableLength 并确认与相邻系统图标间距")
        img = open_image(fp)
        if img is not None:
            st = alpha_stats(img)
            if st["fully_opaque"]:
                rep.error(where, "整张图不透明：模板图靠 alpha 决定形状，不透明的图会渲染成一个实心方块")
            if not is_monochrome(img):
                if intent == "template":
                    rep.warn(where, "标记为 template 但素材是彩色的：颜色会被忽略，说明素材不是按模板图设计的（应为纯黑 + 透明，用不透明度表达层次）")
                else:
                    rep.info(where, "彩色素材且未标记 template：全彩菜单栏/快捷图标需要有充分理由，HIG 倾向单色模板以适配浅/深色菜单栏")
        elif hdr["color_type"] in (0, 2, 3) and not hdr["has_alpha"]:
            rep.error(where, "PNG 无 alpha 通道：模板图必须用透明区域定义形状")

    if not vector and scales and scales != {1, 2} and kind != "complication":
        missing = {1, 2} - scales
        if missing:
            rep.warn(name, f"PNG 只提供了 @{sorted(scales)}x；macOS 需要 @1x 与 @2x（或改用单个 PDF/SVG 并开启 preserves-vector-representation）")
    if not images:
        rep.error(name, "imageset 为空")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--kind", choices=sorted(KIND_SPECS), default="menubar")
    ap.add_argument("--filter", default=None, help="只检查路径匹配该正则的 imageset")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    pattern = re.compile(args.filter) if args.filter else None
    rep = Report()
    count = 0
    for iset in find_imagesets(args.paths, pattern):
        count += 1
        check_imageset(iset, args.kind, rep)
    if count == 0:
        die("没有找到 .imageset（检查路径或 --filter）")
    rep.info("summary", f"检查了 {count} 个 imageset（kind={args.kind}）。{KIND_SPECS[args.kind][2]}")
    if not HAS_PIL:
        rep.info("summary", "未安装 Pillow：pip install pillow 后可检查单色与透明度")
    return rep.emit(as_json=args.json, title="Template image audit")


if __name__ == "__main__":
    sys.exit(main())
