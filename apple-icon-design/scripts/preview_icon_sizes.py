#!/usr/bin/env python3
"""Render a contact sheet that shows how an app icon will actually read on device.

The system never shows your 1024px artwork: it masks it (squircle on iOS /
iPadOS / macOS, circle on watchOS / visionOS), scales it down to 60pt on the
Home Screen, 40pt in Spotlight, 29pt in Settings, and recolours it in dark /
tinted appearances. Fine strokes, thin text and low-contrast details vanish at
those sizes — this sheet makes that visible before a designer or reviewer does.

Usage:
  python3 preview_icon_sizes.py <icon.png | Foo.icon> [-o sheet.png]
                                [--shape squircle|circle] [--sizes 180,120,87,60,40,29]

  * Pass a flattened PNG (any square size, ideally 1024) or an Icon Composer
    package. For a package the script first renders Default / Dark / TintedDark
    with Apple's `ictool` and lays every rendition out on the sheet.
  * Rows: light wallpaper, dark wallpaper, simulated tinted (grayscale + tint)
    and a busy gradient background. Columns: the requested sizes in px (@2x/@3x
    values, e.g. 180 = 60pt@3x iPhone Home Screen, 120 = 40pt@3x Spotlight,
    87 = 29pt@3x Settings, 60 = 20pt@3x notifications).

Requires Pillow (pip install pillow).
"""

from __future__ import annotations

import argparse
import math
import os
import sys
import tempfile

try:
    from PIL import Image, ImageDraw, ImageFont, ImageOps
except ImportError:  # pragma: no cover
    print("需要 Pillow：pip install pillow", file=sys.stderr)
    sys.exit(2)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import ictool_path, render_rendition  # noqa: E402

DEFAULT_SIZES = [180, 120, 87, 60, 40, 29]
LABELS = {180: "60pt@3x 主屏", 120: "40pt@3x Spotlight", 87: "29pt@3x 设置", 80: "40pt@2x", 60: "20pt@3x 通知",
          58: "29pt@2x", 40: "20pt@2x", 29: "29pt@1x", 1024: "App Store"}


def squircle_mask(size: int, exponent: float = 5.0) -> Image.Image:
    """iOS-style superellipse mask (|x|^n + |y|^n = 1, n≈5 approximates the
    Home Screen icon shape closely enough for legibility previews)."""
    scale = 4
    big = size * scale
    mask = Image.new("L", (big, big), 0)
    px = mask.load()
    half = big / 2.0
    for y in range(big):
        ny = abs((y + 0.5) / half - 1.0)
        # solve |x| for this row
        inner = 1.0 - ny ** exponent
        if inner <= 0:
            continue
        xr = inner ** (1.0 / exponent) * half
        x0 = int(round(half - xr))
        x1 = int(round(half + xr))
        for x in range(max(0, x0), min(big, x1)):
            px[x, y] = 255
    return mask.resize((size, size), Image.LANCZOS)


def circle_mask(size: int) -> Image.Image:
    scale = 4
    big = size * scale
    mask = Image.new("L", (big, big), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, big - 1, big - 1), fill=255)
    return mask.resize((size, size), Image.LANCZOS)


def masked(icon: Image.Image, size: int, shape: str) -> Image.Image:
    im = icon.convert("RGBA").resize((size, size), Image.LANCZOS)
    m = circle_mask(size) if shape == "circle" else squircle_mask(size)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(im, (0, 0), m)
    return out


def tinted_sim(icon: Image.Image, tint=(120, 90, 200)) -> Image.Image:
    """Approximate the tinted appearance: luminance only, mapped onto a tint."""
    gray = ImageOps.grayscale(icon.convert("RGB"))
    tint_img = Image.new("RGB", gray.size, tint)
    dark = Image.new("RGB", gray.size, (18, 18, 22))
    out = Image.composite(tint_img, dark, gray)
    out.putalpha(icon.convert("RGBA").getchannel("A"))
    return out


def gradient_bg(w: int, h: int) -> Image.Image:
    bg = Image.new("RGB", (w, h))
    px = bg.load()
    for y in range(h):
        for x in range(w):
            t = (x / max(1, w - 1) + y / max(1, h - 1)) / 2
            px[x, y] = (int(255 * (0.9 - 0.6 * t)), int(255 * (0.5 + 0.4 * math.sin(t * 3))), int(255 * (0.3 + 0.6 * t)))
    return bg


def load_font(size: int):
    for cand in ("/System/Library/Fonts/Hiragino Sans GB.ttc", "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
                 "/System/Library/Fonts/STHeiti Light.ttc", "/System/Library/Fonts/Helvetica.ttc"):
        if os.path.exists(cand):
            try:
                return ImageFont.truetype(cand, size)
            except Exception:  # noqa: BLE001
                pass
    return ImageFont.load_default()


def render_package(pkg: str, tmp: str) -> list[tuple[str, Image.Image]]:
    tool = ictool_path()
    if not tool:
        print("找不到 ictool（Xcode 26+ / Icon Composer.app）；请先在 Icon Composer 里导出 PNG 再传入", file=sys.stderr)
        sys.exit(2)
    out = []
    for r in ("Default", "Dark", "TintedDark", "ClearLight"):
        f = os.path.join(tmp, f"{r}.png")
        good, msg = render_rendition(tool, pkg, f, platform="iOS", rendition=r)
        if not good:
            print(f"ictool {r} 失败：{msg}", file=sys.stderr)
            if "Could not open" in msg:
                break
            continue
        out.append((r, Image.open(f).convert("RGBA")))
    return out


def build_sheet(variants: list[tuple[str, Image.Image]], sizes: list[int], shape: str) -> Image.Image:
    font = load_font(13)
    small = load_font(11)
    pad = 16
    cell_w = max(sizes) + pad
    label_w = 150
    rows: list[tuple[str, str, Image.Image | None]] = []  # (row label, bg kind, icon)
    for name, im in variants:
        rows.append((f"{name} · 浅色壁纸", "light", im))
        rows.append((f"{name} · 深色壁纸", "dark", im))
        if name in ("Default", "ClearLight"):
            rows.append((f"{name} · 复杂壁纸", "busy", im))
        if name == "Default" and len(variants) == 1:
            # flattened PNG only: approximate what the system's tinted appearance does to it
            rows.append(("Tinted 模拟 · 深色", "dark", tinted_sim(im)))
    row_h = max(sizes) + pad + 18
    w = label_w + cell_w * len(sizes) + pad
    h = 40 + row_h * len(rows)
    sheet = Image.new("RGB", (w, h), (245, 245, 247))
    d = ImageDraw.Draw(sheet)
    d.text((pad, 10), f"App Icon 小尺寸预览 · 蒙版={shape} · 系统会自行施加圆角/圆形，勿在素材里预切",
           fill=(60, 60, 67), font=font)
    for r, (label, kind, im) in enumerate(rows):
        y0 = 40 + r * row_h
        bg_color = {"light": (240, 240, 245), "dark": (28, 28, 30)}.get(kind)
        if kind == "busy":
            sheet.paste(gradient_bg(w - label_w, row_h), (label_w, y0))
        else:
            d.rectangle((label_w, y0, w, y0 + row_h), fill=bg_color)
        d.rectangle((0, y0, label_w, y0 + row_h), fill=(250, 250, 252))
        d.text((pad, y0 + row_h // 2 - 8), label, fill=(30, 30, 30), font=font)
        for c, s in enumerate(sizes):
            x = label_w + c * cell_w + pad // 2
            y = y0 + (row_h - 18 - s) // 2
            icon = masked(im, s, shape)
            sheet.paste(icon, (x, y), icon)
    for c, s in enumerate(sizes):
        x = label_w + c * cell_w + pad // 2
        d.text((x, 26), f"{s}px {LABELS.get(s, '')}", fill=(90, 90, 95), font=small)
    return sheet


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path")
    ap.add_argument("-o", "--output", default=None)
    ap.add_argument("--shape", choices=["squircle", "circle"], default="squircle",
                    help="iOS/iPadOS/macOS 用 squircle；watchOS/visionOS 用 circle")
    ap.add_argument("--sizes", default=",".join(map(str, DEFAULT_SIZES)))
    args = ap.parse_args()

    sizes = [int(s) for s in args.sizes.split(",") if s.strip()]
    p = args.path.rstrip("/")
    with tempfile.TemporaryDirectory() as tmp:
        if p.endswith(".icon") and os.path.isdir(p):
            variants = render_package(p, tmp)
            if not variants:
                return 1
        else:
            im = Image.open(p).convert("RGBA")
            if im.width != im.height:
                print(f"警告：{im.width}x{im.height} 不是正方形，预览会被拉伸", file=sys.stderr)
            variants = [("Default", im)]
        sheet = build_sheet(variants, sizes, args.shape)
    out = args.output or os.path.splitext(os.path.basename(p))[0] + "-preview.png"
    sheet.save(out)
    print(f"已生成 {out}（{sheet.width}x{sheet.height}）。检查项：29–40px 下主形状是否仍可辨认；"
          f"Tinted 行中前景与背景是否还有明暗差；深色壁纸上边缘是否消失。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
