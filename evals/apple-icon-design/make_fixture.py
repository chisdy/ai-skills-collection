#!/usr/bin/env python3
"""Generate the binary assets of fixture-repo/ for the apple-icon-design evals.

The text files (Swift sources, Contents.json, icon.json, SVG, README) are committed;
the PNG / JPG files are produced here so the repository stays free of binaries.
Every image embeds a deliberate defect that one of the skill's scripts must catch:

  Assets.xcassets/AppIcon.appiconset/
    AppIcon-1024.png   RGBA, pre-rounded corners, baked drop shadow + gloss, thin
                       strokes, "TICKETS" text  -> ITMS-90717, 预圆角, 烘入效果, 细线, 文字
    mac-*@1x.png       same artwork; six mac slots present, four @2x slots missing
    Icon-60@3x.png     orphan file not referenced by Contents.json
  Assets.xcassets/MenuBarIcon.imageset/
    menubar.png        24x24 opaque, colourful, @1x only, not template
  AppIcon.icon/Assets/
    ticket.png         512x512 fully transparent (empty layer, undersized raster)
    bg.jpg             lossy background image

Usage:  python3 make_fixture.py            (writes into ./fixture-repo, needs Pillow)
"""
from __future__ import annotations

import os
import sys

try:
    from PIL import Image, ImageDraw
except ImportError:  # pragma: no cover
    print("需要 Pillow：pip install pillow", file=sys.stderr)
    sys.exit(2)

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixture-repo")


def icon(size: int, rounded: bool = True, text: bool = True) -> Image.Image:
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    r = int(size * 0.22)
    # baked drop shadow
    d.rounded_rectangle((int(size * 0.02), int(size * 0.04), size - int(size * 0.02), size - 1), r, fill=(0, 0, 0, 90))
    d.rounded_rectangle((0, 0, size - 1, size - 1), r if rounded else 0, fill=(38, 120, 230, 255))
    # gloss highlight
    d.ellipse((-size * 0.2, -size * 0.6, size * 1.2, size * 0.45), fill=(255, 255, 255, 70))
    # thin-line ticket glyph
    d.rectangle((size * 0.3, size * 0.36, size * 0.7, size * 0.64), outline=(255, 255, 255, 255), width=max(1, size // 180))
    for i in range(6):
        y = size * 0.40 + i * size * 0.04
        d.line((size * 0.34, y, size * 0.66, y), fill=(255, 255, 255, 255), width=max(1, size // 400))
    if text:
        d.text((size * 0.36, size * 0.70), "TICKETS", fill=(255, 255, 255, 255))
    return im


def main() -> None:
    ais = os.path.join(ROOT, "Assets.xcassets", "AppIcon.appiconset")
    os.makedirs(ais, exist_ok=True)
    icon(1024).save(os.path.join(ais, "AppIcon-1024.png"))
    for s, sc in [(16, 1), (32, 1), (32, 2), (128, 1), (256, 1), (512, 1)]:
        icon(s * sc).save(os.path.join(ais, f"mac-{s}@{sc}x.png"))
    icon(180).save(os.path.join(ais, "Icon-60@3x.png"))

    mb = os.path.join(ROOT, "Assets.xcassets", "MenuBarIcon.imageset")
    os.makedirs(mb, exist_ok=True)
    im = Image.new("RGBA", (24, 24), (38, 120, 230, 255))
    d = ImageDraw.Draw(im)
    d.ellipse((4, 4, 19, 19), fill=(255, 90, 60, 255))
    d.rectangle((11, 6, 12, 12), fill=(255, 255, 255, 255))
    im.save(os.path.join(mb, "menubar.png"))

    ic = os.path.join(ROOT, "AppIcon.icon", "Assets")
    os.makedirs(ic, exist_ok=True)
    Image.new("RGBA", (512, 512), (0, 0, 0, 0)).save(os.path.join(ic, "ticket.png"))
    Image.new("RGB", (1024, 1024), (38, 120, 230)).save(os.path.join(ic, "bg.jpg"), quality=80)
    print(f"fixture 二进制素材已生成 → {ROOT}")


if __name__ == "__main__":
    main()
