#!/usr/bin/env python3
"""内联浏览器路径的落盘助手（仅标准库）：把 MCP 拿到的 collect/*.js 结果写成与 capture_site.py 相同的契约文件。

三种输入：
  --from-cdp <file>        cursor-ide-browser 的 browser_cdp 大响应落盘文件（{"result": {"type", "value"}}）
  --from-chunks <f1> <f2>  Playwright MCP 用 _read.js 分片得到的多个 JSON（各含 "chunk" 字段），按顺序拼接
  --from-json <file>       任何直接保存的 JSON（内容就是 collect 脚本的返回值）

  python3 save_result.py <name> <page-dir> --from-cdp ~/.cursor/browser-logs/cdp-response-Runtime.evaluate-....json
  python3 save_result.py dom capture/index --from-json /tmp/dom.json

<name> 是 collect 脚本名：dom / styles / computed / tokens / animations / hover / libs / icons / sections / assets / links。
可加 --viewport 768 把 computed / sections 存成 computed.768.json；--screenshot <png> 会把截图复制到 screenshots/<viewport>.png。
按 name 做与脚本路径一致的展开：dom → dom.html；styles → styles.json + styles/*.css；icons → icons.json + icons/*.svg。
同时维护 manifest.json（captureMethod: inline-browser）。
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import Report, read_json, write_json  # noqa: E402


def load_payload(args) -> object:
    if args.from_cdp:
        data = read_json(Path(args.from_cdp))
        if isinstance(data, dict) and "result" in data:
            res = data["result"]
            if isinstance(res, dict) and "value" in res:
                val = res["value"]
                return json.loads(val) if isinstance(val, str) and val[:1] in "{[" else val
            if isinstance(res, dict) and res.get("type") == "undefined":
                raise ValueError("Runtime.evaluate 返回 undefined：表达式没有返回值，检查是否漏了 returnByValue 或脚本报错")
        raise ValueError("不是 browser_cdp 的落盘格式（期望 {result: {value}}）")
    if args.from_chunks:
        parts = []
        for f in args.from_chunks:
            d = read_json(Path(f))
            if isinstance(d, dict) and "chunk" in d:
                parts.append((d.get("offset", 0), d["chunk"]))
            else:
                raise ValueError(f"{f} 不含 chunk 字段，不是 _read.js 的输出")
        parts.sort(key=lambda x: x[0])
        return json.loads("".join(c for _, c in parts))
    return read_json(Path(args.from_json))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("name")
    ap.add_argument("page_dir")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--from-cdp")
    src.add_argument("--from-chunks", nargs="+")
    src.add_argument("--from-json")
    ap.add_argument("--viewport", type=int, help="非主视口时给宽度，computed / sections 会带后缀")
    ap.add_argument("--screenshot", help="把这张截图复制为 screenshots/<viewport>.png")
    ap.add_argument("--url", help="页面 URL（manifest 用；缺省从结果里的 url 字段取）")
    args = ap.parse_args()

    rep = Report()
    page_dir = Path(args.page_dir)
    page_dir.mkdir(parents=True, exist_ok=True)
    try:
        data = load_payload(args)
    except Exception as e:  # noqa: BLE001
        rep.error(args.name, str(e))
        return rep.emit(False, "save_result")

    name = args.name
    written: list[str] = []
    if name == "dom" and isinstance(data, dict) and "html" in data:
        (page_dir / "dom.html").write_text((data.get("doctype") or "<!DOCTYPE html>") + "\n" + data["html"], encoding="utf-8")
        written.append("dom.html")
    elif name == "styles" and isinstance(data, dict):
        sdir = page_dir / "styles"
        sdir.mkdir(exist_ok=True)
        for i, sheet in enumerate(data.get("sheets", [])):
            href = sheet.get("href")
            base = re.sub(r"[^A-Za-z0-9._-]+", "-", Path(urlparse(href).path).name if href else f"inline-{sheet.get('ownerTag') or 'style'}") or "sheet"
            fname = f"{i:02d}-{base[:60]}" + ("" if base.endswith(".css") else ".css")
            if sheet.get("cssText") is not None:
                (sdir / fname).write_text(f"/* source: {href or 'inline'} */\n" + sheet["cssText"], encoding="utf-8")
                sheet["file"] = f"styles/{fname}"
            elif sheet.get("blocked") and href:
                rep.warn("styles", f"跨域样式表被拦：用 browser_navigate 打开 {href} 抄回 {sdir / fname}")
            sheet.pop("cssText", None)
        write_json(page_dir / "styles.json", data)
        written += ["styles.json", "styles/"]
    elif name == "icons" and isinstance(data, dict):
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
        written += ["icons.json", "icons/"]
    else:
        suffix = f".{args.viewport}" if args.viewport and name in ("computed", "sections") else ""
        write_json(page_dir / f"{name}{suffix}.json", data)
        written.append(f"{name}{suffix}.json")

    if args.screenshot:
        (page_dir / "screenshots").mkdir(exist_ok=True)
        dst = page_dir / "screenshots" / f"{args.viewport or 'primary'}.png"
        shutil.copyfile(args.screenshot, dst)
        written.append(str(dst.relative_to(page_dir)))

    mpath = page_dir / "manifest.json"
    manifest = (
        read_json(mpath)
        if mpath.exists()
        else {"pageId": page_dir.name, "captureMethod": "inline-browser", "tool": "mcp", "capturedAt": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "viewports": [], "files": [], "warnings": []}
    )
    url = args.url or (data.get("url") if isinstance(data, dict) else None)
    if url:
        manifest.setdefault("url", url)
    if isinstance(data, dict) and name == "dom":
        manifest["title"] = data.get("title")
        manifest["lang"] = data.get("lang")
    if args.viewport and not any(v.get("width") == args.viewport for v in manifest["viewports"]):
        manifest["viewports"].append({"width": args.viewport})
    for w in written:
        if w not in manifest["files"]:
            manifest["files"].append(w)
    write_json(mpath, manifest)
    rep.info(name, f"→ {', '.join(written)}；manifest 已更新")
    return rep.emit(False, "save_result")


if __name__ == "__main__":
    sys.exit(main())
