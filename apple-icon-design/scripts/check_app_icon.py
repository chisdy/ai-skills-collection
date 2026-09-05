#!/usr/bin/env python3
"""Check an Apple app icon for spec violations before it reaches App Store Connect.

Accepts one of:
  * an Icon Composer package      Foo.icon/            (icon.json + Assets/)
  * an asset-catalog icon set     AppIcon.appiconset/  (Contents.json + PNGs)
  * a single flattened PNG        icon-1024.png

Usage:
  python3 check_app_icon.py <path> [--platform ios|macos|watchos|tvos|visionos]
                                   [--render OUTDIR] [--json]

  --render OUTDIR   (Icon Composer packages only) run Apple's `ictool` for every
                    platform x appearance the package declares and save PNGs so
                    you can eyeball Default / Dark / Clear / Tinted results.

Exit code 1 when any ERROR is found. Requires only the standard library;
installs Pillow to enable pixel checks (transparency, pre-rounded corners,
grayscale tinted variants).
"""

from __future__ import annotations

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import (HAS_PIL, RENDITIONS, Report, alpha_stats, die, ictool_path,  # noqa: E402
                     is_grayscale, load_json, open_image, read_png_header, render_rendition)

# ---------------------------------------------------------------- constants
# Icon Composer 1.2（独立下载版）接受 "refractivity" / "specular-location"；Xcode 26.6 自带的 1.6 起，
# 只要存在 `features` 键（无论取值）ictool 就报 Could not open。实测见 CHANGELOG。
LEGACY_FEATURES = {"refractivity", "specular-location"}
SQUARE_PLATFORMS = {"iOS", "macOS"}
CIRCLE_PLATFORMS = {"watchOS"}
SHADOW_KINDS = {"neutral", "layer-color", "none"}
MAX_GROUPS = 4          # Icon Composer: "organize the layers into a maximum of four groups"
MAX_LAYERS_PER_GROUP = 4
RASTER_MIN_PX = 1024    # canvas is 1024pt; smaller rasters render small, not scaled

MAC_REQUIRED = {(16, 1), (16, 2), (32, 1), (32, 2), (128, 1), (128, 2), (256, 1), (256, 2), (512, 1), (512, 2)}



# ---------------------------------------------------------------- PNG checks
def check_png_pixels(path: str, rep: Report, *, where: str, expect_px: int | None,
                     marketing: bool, appearance: str | None, platform: str) -> None:
    hdr = read_png_header(path)
    if hdr is None:
        rep.error(where, "不是有效的 PNG（App Icon 只接受 PNG；JPG/TIFF/HEIC 都会被拒）")
        return
    w, h = hdr["width"], hdr["height"]
    if w != h and platform != "tvos":
        rep.error(where, f"非正方形 {w}x{h}px；系统只接受正方形图层，再由系统施加圆角/圆形蒙版")
    if expect_px and (w != expect_px or h != expect_px):
        rep.error(where, f"尺寸 {w}x{h}px，与槽位要求 {expect_px}x{expect_px}px 不符")

    img = open_image(path)
    if img is None:
        if hdr["has_alpha"] and marketing:
            rep.error(where, "1024px App Store 图标含 alpha 通道（ITMS-90717 会拒收）；导出时取消 Alpha 并铺满不透明背景")
        elif hdr["has_alpha"]:
            rep.info(where, "PNG 含 alpha 通道（未安装 Pillow，无法判断是否真有透明像素）")
        return

    st = alpha_stats(img)
    if appearance == "dark":
        if st["fully_opaque"]:
            rep.info(where, "深色变体完全不透明：Xcode 文档建议深色图标用透明背景，让系统的深色底透出来（可接受，但请确认是刻意的）")
    else:
        if st["transparent_corners"]:
            lvl = rep.error if marketing else rep.warn
            lvl(where, "四角透明 = 素材已预先切圆角。系统会自己蒙版；预圆角会让边缘锯齿、干扰高光，App Store 1024 图更会直接被拒")
        elif st["has_transparency"] and marketing:
            rep.error(where, f"1024px App Store 图标含透明像素（min alpha {st['min_alpha']}）；ITMS-90717 会拒收，请铺满不透明背景")
        elif st["has_transparency"]:
            rep.warn(where, "含透明像素；iOS / macOS / watchOS 图标应为满幅不透明的方形图层")

    if appearance == "tinted" and not is_grayscale(img):
        rep.warn(where, "着色（tinted）变体不是灰度图：系统只用它的亮度信息，请提供灰度素材（Xcode：Provide your tinted app icon as a grayscale image）")

    mode = img.mode
    info = img.info
    icc = info.get("icc_profile")
    if not icc and "srgb" not in info and "gamma" not in info:
        rep.info(where, "PNG 未嵌入色彩配置（sRGB / Display P3）；HIG 建议每张图带 color profile，避免跨设备偏色")
    if mode == "P":
        rep.info(where, "索引色（palette）PNG；App Icon 建议使用 24 位 RGB（可含 P3）")


# ---------------------------------------------------------------- .appiconset
def parse_size(s: str) -> float | None:
    m = re.match(r"^\s*([\d.]+)x([\d.]+)\s*$", s or "")
    return float(m.group(1)) if m else None


def parse_scale(s: str) -> int:
    m = re.match(r"^\s*(\d+)x\s*$", s or "1x")
    return int(m.group(1)) if m else 1


def check_appiconset(path: str, rep: Report, platform_hint: str | None) -> None:
    cj = os.path.join(path, "Contents.json")
    if not os.path.exists(cj):
        die(f"{path} 缺少 Contents.json")
    data = load_json(cj)
    images = data.get("images", [])
    if not images:
        rep.error(path, "Contents.json 没有 images 条目")
        return

    seen_mac: set[tuple[int, int]] = set()
    has_dark = has_tinted = has_any_ios = False
    referenced: set[str] = set()

    for entry in images:
        idiom = entry.get("idiom", "")
        plat = entry.get("platform", "")
        size_pt = parse_size(entry.get("size", ""))
        scale = parse_scale(entry.get("scale", "1x"))
        appearance = None
        for ap in entry.get("appearances", []) or []:
            if ap.get("appearance") == "luminosity":
                appearance = ap.get("value")
        fn = entry.get("filename")
        slot = f"{idiom}{'/' + plat if plat else ''} {entry.get('size', '?')}@{scale}x{' ' + appearance if appearance else ''}"

        if idiom == "mac" and size_pt:
            seen_mac.add((int(size_pt), scale))
        if idiom in ("iphone", "ipad", "ios-marketing") or plat == "ios" or idiom == "universal" and plat in ("", "ios"):
            has_any_ios = True
        if appearance == "dark":
            has_dark = True
        if appearance == "tinted":
            has_tinted = True

        if not fn:
            if idiom in ("ios-marketing",) or (size_pt == 1024 and idiom in ("universal", "ios-marketing")):
                rep.error(slot, "1024px App Store 槽位为空；上传 App Store Connect 时会被拒")
            elif idiom == "mac":
                rep.warn(slot, "macOS 槽位为空；macOS 需要提供全部 10 个尺寸（16–512pt @1x/@2x）")
            else:
                rep.info(slot, "槽位为空（若使用 Single Size，其余尺寸由 Xcode 生成，可忽略）")
            continue

        referenced.add(fn)
        fpath = os.path.join(path, fn)
        if not os.path.exists(fpath):
            rep.error(slot, f"Contents.json 引用的文件不存在：{fn}")
            continue

        marketing = (idiom == "ios-marketing") or (size_pt == 1024 and idiom in ("universal", "ios-marketing", "watch-marketing"))
        expect = int(round(size_pt * scale)) if size_pt else None
        plat_guess = platform_hint or ("macos" if idiom == "mac" else "watchos" if idiom.startswith("watch") else "ios")
        check_png_pixels(fpath, rep, where=f"{slot} ({fn})", expect_px=expect, marketing=marketing,
                         appearance=appearance, platform=plat_guess)

    # orphan files
    for f in os.listdir(path):
        if f.lower().endswith(".png") and f not in referenced:
            rep.info(path, f"未被 Contents.json 引用的文件：{f}（会被打进包里但不会被使用）")

    if seen_mac:
        missing = MAC_REQUIRED - seen_mac
        if missing:
            rep.warn(path, "macOS 缺少尺寸槽位：" + ", ".join(f"{s}pt@{sc}x" for s, sc in sorted(missing)))
    if has_any_ios:
        if not has_dark:
            rep.info(path, "未提供 iOS 深色变体：系统会自动生成，但自动结果常常偏灰；建议用 Icon Composer 或提供 dark 变体")
        if not has_tinted:
            rep.info(path, "未提供 iOS 着色（tinted）变体：系统会自动生成；如需保证单色可读性请提供灰度素材")
        rep.info(path, "提示：Xcode 26+ 项目更推荐用 Icon Composer 的 .icon 文件（分层 + 六种外观 + 旧系统自动回退），而不是继续维护 .appiconset")


# ---------------------------------------------------------------- .icon (Icon Composer)
def check_fill(fill, rep: Report, where: str) -> None:
    if not isinstance(fill, dict):
        rep.error(where, "fill 必须是对象（solid / linear-gradient / automatic-gradient）")
        return
    kinds = [k for k in ("solid", "linear-gradient", "automatic-gradient") if k in fill]
    if len(kinds) != 1:
        rep.error(where, f"fill 需且仅需一种类型，当前：{list(fill.keys())}")
        return
    k = kinds[0]
    vals = fill[k] if isinstance(fill[k], list) else [fill[k]]
    if k == "linear-gradient" and len(vals) != 2:
        rep.error(where, f"linear-gradient 必须正好 2 个颜色（当前 {len(vals)}）；三段渐变请折叠为首尾两色")
    for v in vals:
        if not isinstance(v, str) or ":" not in v:
            rep.error(where, f"颜色编码缺少 ':' 分隔（应形如 extended-srgb:r,g,b,a）：{v!r}")
        elif v.split(":", 1)[0] not in ("extended-srgb", "display-p3", "extended-gray", "srgb"):
            rep.warn(where, f"未知色彩空间前缀：{v.split(':', 1)[0]}（已知：extended-srgb / display-p3 / extended-gray）")


def check_specializations(obj: dict, key: str, rep: Report, where: str) -> None:
    if key in obj and f"{key}-specializations" in obj:
        rep.warn(where, f"同时存在 `{key}` 与 `{key}-specializations`：Icon Composer 以 `{key}` 为准，按外观的变体会被静默忽略")


def check_icon_package(path: str, rep: Report, render_dir: str | None) -> None:
    ij = os.path.join(path, "icon.json")
    assets = os.path.join(path, "Assets")
    if not os.path.exists(ij):
        die(f"{path} 缺少 icon.json（.icon 是一个目录包：icon.json + Assets/）")
    try:
        doc = load_json(ij)
    except Exception as exc:  # noqa: BLE001
        rep.error(ij, f"icon.json 不是合法 JSON：{exc}")
        return

    # document level
    if "groups" not in doc:
        rep.error(ij, "缺少必需的 `groups` 数组（ictool: The data couldn't be read because it is missing）")
        groups = []
    else:
        groups = doc["groups"] or []
    if "features" in doc:
        feats = doc.get("features") or []
        bad = [f for f in feats if f not in LEGACY_FEATURES]
        detail = f"（其中 {bad} 在任何版本都无效）" if bad else ""
        rep.error(ij, f"存在 `features` 键 {feats}{detail}：Xcode 26.6 自带的 Icon Composer 1.6 / ictool 对含该键的包一律报 "
                      f"Could not open（旧版 1.2 才接受 refractivity / specular-location）。删除整个 `features` 键，"
                      f"Specular / Refraction 用 group 级 `specular` / 图层 `glass` 控制")
    sp = doc.get("supported-platforms")
    platforms_to_render = ["iOS"]
    if sp is None:
        rep.info(ij, "未声明 supported-platforms（可打开；建议显式声明 squares: iOS/macOS、circles: watchOS）")
    elif isinstance(sp, dict):
        sq = sp.get("squares")
        ci = sp.get("circles")
        if isinstance(sq, list):
            bad = [p for p in sq if p not in SQUARE_PLATFORMS]
            if bad:
                rep.error(ij, f"squares 只能是 iOS / macOS，当前含 {bad}（iPadOS 随 iOS；tvOS / visionOS 不是 Icon Composer 目标）")
            platforms_to_render = [p for p in sq if p in SQUARE_PLATFORMS] or platforms_to_render
        if isinstance(ci, list):
            bad = [p for p in ci if p not in CIRCLE_PLATFORMS]
            if bad:
                rep.error(ij, f"circles 只能是 watchOS，当前含 {bad}")
            if "watchOS" in ci:
                platforms_to_render.append("watchOS")
    if "fill" in doc:
        check_fill(doc["fill"], rep, f"{ij} > fill")
    check_specializations(doc, "fill", rep, ij)
    for spec in doc.get("fill-specializations", []) or []:
        if isinstance(spec, dict) and "value" in spec:
            check_fill(spec["value"], rep, f"{ij} > fill-specializations[{spec.get('appearance', 'default')}]")
    if "fill" not in doc and "fill-specializations" not in doc:
        rep.info(ij, "未设置背景 fill；HIG 建议用实色或渐变背景突出前景，而不是导入自定义背景图")
    cs = doc.get("color-space-for-untagged-svg-colors")
    if cs and cs != "display-p3":
        rep.warn(ij, f"color-space-for-untagged-svg-colors={cs!r}：实测只接受 'display-p3'，其它值会导致无法打开")

    # groups / layers
    if len(groups) > MAX_GROUPS:
        rep.warn(ij, f"共 {len(groups)} 个 group；Icon Composer 建议最多 {MAX_GROUPS} 个，层数越多材质效果越浑浊（WWDC25：less is more）")
    if len(groups) == 0:
        rep.warn(ij, "groups 为空：只会渲染背景，前景图层缺失")
    raster_seen = False
    for gi, g in enumerate(groups):
        gw = f"{ij} > groups[{gi}] {g.get('name', '')}".rstrip()
        layers = g.get("layers", []) or []
        if len(layers) > MAX_LAYERS_PER_GROUP:
            rep.warn(gw, f"该 group 有 {len(layers)} 个 layer；建议 1–4 个")
        if "lighting" in g and g["lighting"] not in ("individual", "combined"):
            rep.error(gw, f"lighting 只能是 individual / combined，当前 {g['lighting']!r}")
        sh = g.get("shadow")
        if isinstance(sh, dict):
            if "kind" not in sh or "opacity" not in sh:
                rep.error(gw, "shadow 需要同时包含 kind 与 opacity")
            elif sh["kind"] not in SHADOW_KINDS:
                rep.error(gw, f"shadow.kind 只能是 {sorted(SHADOW_KINDS)}（UI 里的 Natural/Chromatic/Off），当前 {sh['kind']!r}")
        tr = g.get("translucency")
        if isinstance(tr, dict) and ("enabled" not in tr or "value" not in tr):
            rep.error(gw, "translucency 需要同时包含 enabled 与 value")
        for li, layer in enumerate(layers):
            lw = f"{gw} > layers[{li}] {layer.get('name', '')}".rstrip()
            names = []
            if layer.get("image-name"):
                names.append(layer["image-name"])
            for spec in layer.get("image-name-specializations", []) or []:
                if isinstance(spec, dict) and spec.get("value"):
                    names.append(spec["value"])
            if not names:
                rep.warn(lw, "layer 没有 image-name：不会绘制任何内容")
            for n in names:
                ap = os.path.join(assets, n)
                if not os.path.exists(ap):
                    rep.error(lw, f"Assets/ 中找不到 {n}；ictool 会把它当空图层渲染成功，不会报错")
                    continue
                ext = os.path.splitext(n)[1].lower()
                if ext in (".jpg", ".jpeg", ".heic"):
                    rep.warn(lw, f"{n} 是有损格式；分层素材请用 SVG（矢量）或 PNG（无损）")
                elif ext == ".png":
                    raster_seen = True
                    hdr = read_png_header(ap)
                    if hdr and (hdr["width"] < RASTER_MIN_PX or hdr["height"] < RASTER_MIN_PX):
                        rep.warn(lw, f"{n} 为 {hdr['width']}x{hdr['height']}px；画布是 1024pt，较小的位图按原尺寸渲染而不会放大")
                    img = open_image(ap)
                    if img is not None:
                        st = alpha_stats(img)
                        if img.convert("RGBA").getchannel("A").getextrema()[1] == 0:
                            rep.error(lw, f"{n} 所有像素 alpha = 0，是一张空图；该图层不会绘制任何内容，但 ictool 仍会渲染成功")
                        elif st["fully_opaque"] and (gi > 0 or li > 0 or len(layers) > 1):
                            rep.info(lw, f"{n} 完全不透明；前景图层通常需要透明区域，否则会遮住下面的图层与背景 fill")
                elif ext != ".svg":
                    rep.warn(lw, f"{n} 的格式 {ext} 不是 SVG / PNG")
            if "fill" in layer:
                check_fill(layer["fill"], rep, f"{lw} > fill")
            check_specializations(layer, "fill", rep, lw)
            check_specializations(layer, "image-name", rep, lw)
            pos = layer.get("position")
            if isinstance(pos, dict) and ("scale" not in pos or "translation-in-points" not in pos):
                rep.error(lw, "position 需同时包含 scale 与 translation-in-points")
    if raster_seen:
        rep.info(ij, "使用了 PNG 图层：矢量 SVG 在任何尺寸都清晰；仅在 mesh 渐变等 SVG 无法表达时才用 PNG")

    # orphan assets
    if os.path.isdir(assets):
        used = set()
        for g in groups:
            for layer in g.get("layers", []) or []:
                if layer.get("image-name"):
                    used.add(layer["image-name"])
                for spec in layer.get("image-name-specializations", []) or []:
                    if isinstance(spec, dict) and spec.get("value"):
                        used.add(spec["value"])
        for f in os.listdir(assets):
            if not f.startswith(".") and f not in used:
                rep.info(assets, f"未被引用的素材：{f}")

    if render_dir:
        render_with_ictool(path, platforms_to_render, render_dir, rep)


def render_with_ictool(pkg: str, platforms: list[str], outdir: str, rep: Report) -> None:
    tool = ictool_path()
    if not tool:
        rep.warn(pkg, "找不到 ictool（需要 Xcode 26+ 自带的 Icon Composer.app）；跳过渲染")
        return
    os.makedirs(outdir, exist_ok=True)
    base = os.path.splitext(os.path.basename(pkg.rstrip("/")))[0]
    ok = 0
    for plat in platforms:
        rends = ["Default"] if plat == "watchOS" else RENDITIONS
        for r in rends:
            out = os.path.join(outdir, f"{base}-{plat}-{r}.png")
            good, msg = render_rendition(tool, pkg, out, platform=plat, rendition=r)
            if not good:
                rep.error(f"ictool {plat}/{r}", msg)
                if "Could not open" in msg:
                    break  # the package itself is broken; other renditions will fail identically
            else:
                ok += 1
    rep.info(pkg, f"ictool 渲染完成 {ok} 张 → {outdir}；请逐张检查 Clear / Tinted 下前景是否仍可辨认，"
                  f"再用 preview_icon_sizes.py 看小尺寸")


# ---------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path")
    ap.add_argument("--platform", choices=["ios", "macos", "watchos", "tvos", "visionos"])
    ap.add_argument("--render", metavar="OUTDIR", help="(.icon) 用 ictool 渲染全部外观到目录")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    p = args.path.rstrip("/")
    if not os.path.exists(p):
        die(f"路径不存在：{p}")
    rep = Report()
    if p.endswith(".icon") and os.path.isdir(p):
        check_icon_package(p, rep, args.render)
        title = f"Icon Composer package: {p}"
    elif p.endswith(".appiconset") and os.path.isdir(p):
        check_appiconset(p, rep, args.platform)
        title = f"Asset catalog icon set: {p}"
    elif os.path.isfile(p) and p.lower().endswith(".png"):
        hdr = read_png_header(p)
        expect = 1088 if args.platform == "watchos" and hdr and hdr["width"] == 1088 else 1024
        check_png_pixels(p, rep, where=os.path.basename(p), expect_px=expect, marketing=True,
                         appearance=None, platform=args.platform or "ios")
        title = f"Flattened icon: {p}"
    else:
        die("不支持的输入：请传入 *.icon 目录、*.appiconset 目录或单张 PNG")
    if not HAS_PIL:
        rep.info(p, "未安装 Pillow：pip install pillow 后可检查透明角、灰度变体等像素级问题")
    return rep.emit(as_json=args.json, title=title)


if __name__ == "__main__":
    sys.exit(main())
