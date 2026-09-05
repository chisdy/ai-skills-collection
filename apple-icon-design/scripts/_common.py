"""Shared helpers for the apple-icon-design check scripts.

Only the standard library is required. Pillow is optional: when it is
available pixel-level checks run, otherwise the scripts fall back to reading
PNG headers and say which checks were skipped.
"""

from __future__ import annotations

import json
import os
import struct
import subprocess
import sys
from dataclasses import dataclass, field

try:  # optional dependency
    from PIL import Image  # type: ignore

    HAS_PIL = True
except Exception:  # pragma: no cover
    Image = None  # type: ignore
    HAS_PIL = False


@dataclass
class Finding:
    level: str  # ERROR / WARN / INFO
    where: str
    message: str


@dataclass
class Report:
    findings: list[Finding] = field(default_factory=list)

    def error(self, where: str, msg: str) -> None:
        self.findings.append(Finding("ERROR", where, msg))

    def warn(self, where: str, msg: str) -> None:
        self.findings.append(Finding("WARN", where, msg))

    def info(self, where: str, msg: str) -> None:
        self.findings.append(Finding("INFO", where, msg))

    @property
    def errors(self) -> int:
        return sum(1 for f in self.findings if f.level == "ERROR")

    @property
    def warnings(self) -> int:
        return sum(1 for f in self.findings if f.level == "WARN")

    def emit(self, as_json: bool = False, title: str = "") -> int:
        """Print the report and return a process exit code (1 if any ERROR)."""
        if as_json:
            print(json.dumps([f.__dict__ for f in self.findings], ensure_ascii=False, indent=2))
        else:
            if title:
                print(f"== {title} ==")
            order = {"ERROR": 0, "WARN": 1, "INFO": 2}
            for f in sorted(self.findings, key=lambda x: order[x.level]):
                print(f"[{f.level}] {f.where}: {f.message}")
            print(f"-- {self.errors} error(s), {self.warnings} warning(s), "
                  f"{len(self.findings) - self.errors - self.warnings} info")
            if not HAS_PIL:
                print("-- Pillow 未安装，像素级检查（alpha 角、单色、灰度）已跳过：pip install pillow")
        return 1 if self.errors else 0


def read_png_header(path: str) -> dict | None:
    """Return width/height/color_type/has_alpha for a PNG without Pillow."""
    try:
        with open(path, "rb") as fh:
            sig = fh.read(8)
            if sig != b"\x89PNG\r\n\x1a\n":
                return None
            length, ctype = struct.unpack(">I4s", fh.read(8))
            if ctype != b"IHDR":
                return None
            w, h, depth, color_type, _, _, _ = struct.unpack(">IIBBBBB", fh.read(13))
            # color types: 0 gray, 2 rgb, 3 palette, 4 gray+alpha, 6 rgba
            has_alpha = color_type in (4, 6)
            # tRNS chunk also means transparency for palette / rgb images
            fh.read(4)  # crc
            while True:
                head = fh.read(8)
                if len(head) < 8:
                    break
                length, ctype = struct.unpack(">I4s", head)
                if ctype == b"tRNS":
                    has_alpha = True
                    break
                if ctype == b"IDAT":
                    break
                fh.seek(length + 4, os.SEEK_CUR)
            return {"width": w, "height": h, "color_type": color_type, "has_alpha": has_alpha}
    except Exception:
        return None


def open_image(path: str):
    if not HAS_PIL:
        return None
    try:
        return Image.open(path)
    except Exception:
        return None


def alpha_stats(img) -> dict:
    """Describe transparency: any transparent pixel, transparent corners, and
    whether the whole image is opaque."""
    rgba = img.convert("RGBA")
    w, h = rgba.size
    a = rgba.getchannel("A")
    lo, hi = a.getextrema()
    corner_px = [a.getpixel((0, 0)), a.getpixel((w - 1, 0)), a.getpixel((0, h - 1)), a.getpixel((w - 1, h - 1))]
    return {
        "has_transparency": lo < 255,
        "fully_opaque": lo == 255,
        "transparent_corners": all(p < 128 for p in corner_px),
        "min_alpha": lo,
    }


def is_monochrome(img, tolerance: int = 24) -> bool:
    """True when every non-transparent pixel shares (roughly) one colour, which
    is what a template image should look like."""
    rgba = img.convert("RGBA")
    small = rgba.resize((min(64, rgba.width), min(64, rgba.height)))
    colors = set()
    for r, g, b, a in small.getdata():
        if a < 32:
            continue
        colors.add((r // tolerance, g // tolerance, b // tolerance))
        if len(colors) > 2:
            return False
    return True


def is_grayscale(img, tolerance: int = 12) -> bool:
    rgba = img.convert("RGBA")
    small = rgba.resize((min(96, rgba.width), min(96, rgba.height)))
    for r, g, b, a in small.getdata():
        if a < 32:
            continue
        if max(r, g, b) - min(r, g, b) > tolerance:
            return False
    return True


def load_json(path: str):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    sys.exit(code)


# ---------------------------------------------------------------- ictool (Icon Composer renderer)
RENDITIONS = ["Default", "Dark", "ClearLight", "ClearDark", "TintedLight", "TintedDark"]
TINT_ARGS = ["--tint-color", "0.55", "--tint-strength", "0.8"]  # a mid-hue tint at 80 %, like a user-picked colour


def ictool_path() -> str | None:
    """Path to the `ictool` bundled with the Icon Composer.app inside the selected Xcode (26+)."""
    try:
        dev = subprocess.check_output(["xcode-select", "-p"], text=True).strip()
    except Exception:
        return None
    cand = os.path.join(os.path.dirname(dev), "Applications", "Icon Composer.app", "Contents", "Executables", "ictool")
    return cand if os.path.exists(cand) else None


def render_rendition(tool: str, pkg: str, out: str, *, platform: str = "iOS", rendition: str = "Default",
                     size: int = 512, scale: int = 2) -> tuple[bool, str]:
    """Render one platform x appearance of an Icon Composer package to a PNG.

    Returns (ok, message). `message` is ictool's own output on failure — "Could not
    open" means the package itself is broken and every other rendition will fail
    the same way, so callers can stop early.
    """
    cmd = [tool, pkg, "--export-image", "--output-file", out, "--platform", platform,
           "--rendition", rendition, "--width", str(size), "--height", str(size), "--scale", str(scale)]
    if rendition.startswith("Tinted"):
        cmd += TINT_ARGS
    res = subprocess.run(cmd, capture_output=True, text=True)
    msg = (res.stdout or res.stderr).strip() or f"exit {res.returncode}"
    return res.returncode == 0, msg
