#!/usr/bin/env python3
"""Audit SF Symbol usage in Swift / Objective-C / Interface Builder sources.

What it catches (all against Apple's own symbol metadata shipped with macOS in
CoreGlyphs.bundle, so it is exactly as current as the machine's OS):
  * symbol names that don't exist                       -> ERROR (renders nothing)
  * legacy names that were renamed                      -> WARN  (still resolve, but the
                                                            SF Symbols app won't find them;
                                                            the WARN says whether the new
                                                            name is available on your target)
  * symbols newer than your minimum deployment target   -> ERROR (nil image on old OS)
  * restricted Apple-product symbols                    -> INFO  (may only refer to that
                                                            product, may not be modified)
  * `.resizable()` / fixed `.frame` on a symbol image   -> WARN  (drops typographic metrics)
  * icon-only Button labels without accessibilityLabel  -> INFO  (heuristic)

Scope of the two heuristics: they only look at SwiftUI `Image(systemName:)` and the
line right after it. UIKit / AppKit misuse (e.g. `UIImage(systemName:)` drawn into a
fixed-size UIImageView without a SymbolConfiguration) and Interface Builder files are
name-checked but not style-checked — review those by hand with
references/interface-icons.md section 3.

Usage:
  python3 check_symbols.py <dir-or-file ...> [--min-ios 16.0] [--min-macos 13.0]
                           [--min-watchos 9.0] [--min-tvos 16.0] [--min-visionos 1.0]
                           [--metadata /path/to/CoreGlyphs/Resources] [--json]

Exit code 1 when any ERROR is found. Standard library only; must run on macOS
(or point --metadata at a copy of the CoreGlyphs Resources folder).
"""

from __future__ import annotations

import argparse
import json
import os
import plistlib
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import Report, die  # noqa: E402

DEFAULT_METADATA = "/System/Library/CoreServices/CoreGlyphs.bundle/Contents/Resources"
SOURCE_EXT = {".swift", ".m", ".mm", ".h", ".storyboard", ".xib", ".plist"}
SKIP_DIRS = {".git", "Pods", "Carthage", ".build", "DerivedData", "node_modules", ".swiftpm"}

PATTERNS = [
    # (regex, kind)
    (re.compile(r'systemName:\s*"([^"\\]+)"'), "swift"),          # Image / UIImage
    (re.compile(r'systemSymbolName:\s*"([^"\\]+)"'), "swift"),    # NSImage
    (re.compile(r'systemImage:\s*"([^"\\]+)"'), "swift"),         # Label / Button / MenuBarExtra / tabItem
    (re.compile(r'systemImageName:\s*"([^"\\]+)"'), "swift"),     # UIApplicationShortcutIcon
    (re.compile(r'systemImageNamed:\s*@"([^"\\]+)"'), "objc"),
    (re.compile(r'imageWithSystemSymbolName:\s*@"([^"\\]+)"'), "objc"),
    (re.compile(r'<image\s+name="([^"]+)"\s+catalog="system"'), "ib"),
    (re.compile(r'<imageReference[^>]*catalog="system"[^>]*image="([^"]+)"'), "ib"),
]
# `systemName: flag ? "a" : "b"` — both branches are symbol names
TERNARY = re.compile(r'system(?:Name|SymbolName|Image|ImageName):\s*[^"\n]*?\?\s*"([^"\\]+)"\s*:\s*"([^"\\]+)"')
PLATFORM_FLAGS = {"iOS": "min_ios", "macOS": "min_macos", "watchOS": "min_watchos", "tvOS": "min_tvos", "visionOS": "min_visionos"}


def vtuple(v: str) -> tuple[int, ...]:
    return tuple(int(x) for x in re.findall(r"\d+", v)[:3]) or (0,)


def load_plist(path: str):
    try:
        with open(path, "rb") as fh:
            return plistlib.load(fh)
    except Exception:
        # .strings may be OpenStep text; let plutil convert it
        try:
            out = subprocess.check_output(["plutil", "-convert", "json", "-o", "-", path], text=True)
            return json.loads(out)
        except Exception:
            return None


def load_metadata(folder: str):
    avail = load_plist(os.path.join(folder, "name_availability.plist"))
    if not avail or "symbols" not in avail:
        die(f"读不到 {folder}/name_availability.plist；请在 macOS 上运行，或用 --metadata 指向 CoreGlyphs Resources 目录")
    aliases = load_plist(os.path.join(folder, "name_aliases.strings")) or {}
    restrictions = load_plist(os.path.join(folder, "symbol_restrictions.strings")) or {}
    return avail["symbols"], avail.get("year_to_release", {}), aliases, restrictions


def iter_sources(paths: list[str]):
    for p in paths:
        if os.path.isfile(p):
            yield p
            continue
        for root, dirs, files in os.walk(p):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.endswith(".xcassets")]
            for f in files:
                if os.path.splitext(f)[1] in SOURCE_EXT:
                    yield os.path.join(root, f)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="+")
    for plat, flag in PLATFORM_FLAGS.items():
        ap.add_argument("--" + flag.replace("_", "-"), dest=flag, default=None,
                        help=f"{plat} 最低部署版本，如 16.0；不传则不检查该平台可用性")
    ap.add_argument("--metadata", default=DEFAULT_METADATA)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    symbols, year_map, aliases, restrictions = load_metadata(args.metadata)
    targets = {plat: getattr(args, flag) for plat, flag in PLATFORM_FLAGS.items() if getattr(args, flag)}
    rep = Report()
    seen_names: dict[str, int] = {}
    files = 0

    for path in iter_sources(args.paths):
        try:
            text = open(path, "r", encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        files += 1
        lines = text.splitlines()
        for i, line in enumerate(lines, 1):
            where = f"{os.path.relpath(path)}:{i}"
            names_on_line: list[tuple[str, str]] = []  # (name, kind)
            for rx, kind in PATTERNS:
                for m in rx.finditer(line):
                    names_on_line.append((m.group(1), kind))
            for m in TERNARY.finditer(line):
                names_on_line.extend([(m.group(1), "swift"), (m.group(2), "swift")])
            for name, _kind in names_on_line:
                seen_names[name] = seen_names.get(name, 0) + 1
                if name in aliases:
                    new = aliases[name]
                    # Is the new name usable on the caller's deployment targets? If not, renaming
                    # would turn a working (aliased) symbol into a blank one.
                    blockers = []
                    rel_new = year_map.get(str(symbols.get(new, "")), {})
                    for plat, minimum in targets.items():
                        need = rel_new.get(plat)
                        if need and vtuple(need) > vtuple(minimum):
                            blockers.append(f"{plat} {need}+")
                    if blockers:
                        rep.warn(where, f"`{name}` 是旧名称，当前名为 `{new}`，但新名需要 {' / '.join(blockers)}，高于你的部署目标——"
                                        f"请保留旧名（旧名在新系统上仍是有效别名），或用 #available 分支")
                    else:
                        rep.warn(where, f"`{name}` 是旧名称，当前名为 `{new}`；旧名仍可解析，但 SF Symbols app 里搜不到，"
                                        f"新名在当前部署目标可用，建议更新")
                if name in symbols:
                    year = symbols[name]
                    rel = year_map.get(str(year), {})
                    for plat, minimum in targets.items():
                        need = rel.get(plat)
                        if need and vtuple(need) > vtuple(minimum):
                            rep.error(where, f"`{name}` 需要 {plat} {need}+（SF Symbols {year}），但最低部署目标是 {plat} {minimum}；"
                                             f"低版本上返回 nil / 空白。用 #available 分支或换旧符号")
                    if name in restrictions:
                        rep.info(where, f"`{name}` 是受限的 Apple 产品符号：{restrictions[name]} 不能修改、不能用于 app icon / logo")
                elif name not in aliases:
                    rep.error(where, f"`{name}` 不是已知的 SF Symbol 名称（会渲染为空）。在 SF Symbols app 里核对拼写；自定义符号应用 Image(\"name\") 而不是 systemName")

            # heuristics (SwiftUI `Image(systemName:)` only; see module docstring) ----------
            swiftui_image = any(k == "swift" for _n, k in names_on_line) and "systemName" in line
            if swiftui_image:
                window = " ".join(lines[i - 1:i + 1])  # this line + the next (chained modifier)
                if ".resizable()" in window:
                    rep.warn(where, "对 SF Symbol 使用 .resizable()/frame 会丢掉字体度量与 Dynamic Type 缩放；改用 .font(.title) / .imageScale(.large) / .symbolEffect 控制大小")
                before = "\n".join(lines[max(0, i - 5):i - 1])
                around = "\n".join(lines[max(0, i - 2):i + 2])
                if "Button" in before and not any(k in around for k in ("Label(", "accessibilityLabel", "Text(", "help(")):
                    rep.info(where, "疑似仅图标按钮且附近没有 accessibilityLabel / Label；VoiceOver 会读出符号名（如 'square and arrow up'），请补描述")
            if re.search(r'Image\(systemName:\s*"[^"]+"\)\s*\.frame\(', line):
                rep.warn(where, "直接给符号 .frame(width:height:) 不会改变符号大小，只会改变布局框；用 .font / .imageScale")

    if files == 0:
        die("没有找到可扫描的源文件（.swift / .m / .mm / .storyboard / .xib）")
    rep.info("summary", f"扫描 {files} 个文件，发现 {sum(seen_names.values())} 处系统符号引用、{len(seen_names)} 个不同名称"
                        + (f"；部署目标 {targets}" if targets else "；未指定 --min-* 部署目标，跳过可用性检查"))
    return rep.emit(as_json=args.json, title="SF Symbols usage audit")


if __name__ == "__main__":
    sys.exit(main())
