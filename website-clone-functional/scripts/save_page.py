#!/usr/bin/env python3
"""内联浏览器路径的落盘助手（仅标准库）：把 MCP 拿到的 collect/features.js / links.js / network.js 结果写成与 crawl_features.py 相同的目录结构。

  python3 save_page.py <features-dir> --page <file> [--links <file>] [--network <file>] [--url <url>] [--admin]

<file> 三种格式自动识别：
  * cursor-ide-browser 的 browser_cdp 大响应落盘文件（{"result": {"type", "value"}}）
  * Playwright MCP 用 collect/_read.js 分片得到的多个 JSON（传多个文件，各含 "chunk" 字段）——用 --page-chunks f1 f2 ...
  * 直接保存的 JSON（内容就是 collect 脚本的返回值）

维护 features/site-map.json（source: inline-browser）与 features/network.json（Performance API 条目标 methodKnown: false）。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import Report, classify_url, now_iso, page_id_for, read_json, write_json  # noqa: E402


def load_payload(path: str | None, chunks: list[str] | None):
    if chunks:
        parts = []
        for f in chunks:
            d = read_json(Path(f))
            if not (isinstance(d, dict) and "chunk" in d):
                raise ValueError(f"{f} 不含 chunk 字段，不是 _read.js 的输出")
            parts.append((d.get("offset", 0), d["chunk"]))
        parts.sort(key=lambda x: x[0])
        return json.loads("".join(c for _, c in parts))
    data = read_json(Path(path))
    if isinstance(data, dict) and "result" in data and isinstance(data["result"], dict) and ("value" in data["result"] or data["result"].get("type")):
        res = data["result"]
        if res.get("type") == "undefined":
            raise ValueError("Runtime.evaluate 返回 undefined：检查 returnByValue 或脚本报错")
        val = res.get("value")
        return json.loads(val) if isinstance(val, str) and val[:1] in "{[" else val
    return data


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("features_dir")
    ap.add_argument("--page", help="features.js 结果文件")
    ap.add_argument("--page-chunks", nargs="+", help="features.js 结果的 _read.js 分片")
    ap.add_argument("--links", help="links.js 结果文件")
    ap.add_argument("--network", help="network.js 结果文件（或 Playwright MCP browser_network_requests 另存的 JSON 数组）")
    ap.add_argument("--url", help="页面 URL（缺省取结果里的 url）")
    ap.add_argument("--admin", action="store_true", help="这是后台页面")
    ap.add_argument("--login-wall", action="store_true", help="这页在登录墙后（用户登录后采到的）")
    args = ap.parse_args()

    rep = Report()
    out = Path(args.features_dir)
    out.mkdir(parents=True, exist_ok=True)
    if not args.page and not args.page_chunks:
        rep.error("args", "需要 --page 或 --page-chunks")
        return rep.emit(False, "save_page")
    try:
        features = load_payload(args.page, args.page_chunks)
    except Exception as e:  # noqa: BLE001
        rep.error("page", str(e))
        return rep.emit(False, "save_page")
    if not isinstance(features, dict) or "pageType" not in features:
        rep.error("page", "不是 collect/features.js 的返回值（缺 pageType）")
        return rep.emit(False, "save_page")

    url = args.url or features.get("url")
    smap_path = out / "site-map.json"
    smap = read_json(smap_path) if smap_path.exists() else {"generatedAt": now_iso(), "origin": url, "source": "inline-browser", "pages": []}
    taken = {p["pageId"] for p in smap["pages"]}
    existing = next((p for p in smap["pages"] if p["url"] == url), None)
    pid = existing["pageId"] if existing else page_id_for(url, taken)
    pdir = out / pid
    features.setdefault("finalUrl", url)
    features.setdefault("httpStatus", None)
    features.setdefault("redirectedToLogin", False)
    features["captureMethod"] = "inline-browser"
    write_json(pdir / "page.json", features)
    written = ["page.json"]

    links = None
    if args.links:
        try:
            links = load_payload(args.links, None)
            write_json(pdir / "links.json", links)
            written.append("links.json")
        except Exception as e:  # noqa: BLE001
            rep.warn("links", str(e))
    write_json(pdir / "probes.json", {"enabled": False, "actions": [], "note": "内联浏览器路径：只读探测由模型手动执行并在此记录"})

    if args.network:
        try:
            net = load_payload(args.network, None)
            npath = out / "network.json"
            ndoc = read_json(npath) if npath.exists() else {"generatedAt": now_iso(), "allowWrites": False, "blocked": 0, "count": 0, "entries": [], "source": "inline-browser"}
            items = net.get("entries", []) if isinstance(net, dict) else net
            for it in items:
                # network.js 条目 或 Playwright MCP browser_network_requests 条目（含 method / status）
                u = it.get("url") or it.get("name")
                if not u:
                    continue
                pu = urlparse(u)
                ndoc["entries"].append(
                    {
                        "page": pid,
                        "trigger": "load",
                        "method": it.get("method") or "GET",
                        "methodKnown": bool(it.get("method")),
                        "url": u,
                        "host": pu.hostname,
                        "path": pu.path,
                        "queryKeys": it.get("queryKeys") or sorted({k.split("=")[0] for k in pu.query.split("&") if k}),
                        "resourceType": "fetch" if (it.get("initiator") in ("fetch", "xmlhttprequest") or "/api/" in u or u.endswith(".json")) else (it.get("resourceType") or "other"),
                        "sameSite": it.get("sameSite", True),
                        "status": it.get("status"),
                        "blocked": False,
                    }
                )
            ndoc["count"] = len(ndoc["entries"])
            write_json(npath, ndoc)
            written.append("network.json(+)")
        except Exception as e:  # noqa: BLE001
            rep.warn("network", str(e))

    ptype = "admin" if args.admin else features.get("pageType") or classify_url(url)
    entry = {
        "url": url,
        "pageId": pid,
        "type": ptype,
        "title": features.get("title"),
        "depth": 0,
        "loginWall": bool(args.login_wall or features.get("loginWall")),
        "httpStatus": None,
        "forms": len(features.get("forms", [])),
        "lists": len(features.get("lists", [])),
        "probes": 0,
        "captureMethod": "inline-browser",
    }
    if existing:
        smap["pages"][smap["pages"].index(existing)] = entry
    else:
        smap["pages"].append(entry)
    smap["generatedAt"] = now_iso()
    write_json(smap_path, smap)
    rep.info(pid, f"{ptype} forms {entry['forms']} lists {entry['lists']} → {', '.join(written)}；site-map.json 现有 {len(smap['pages'])} 页")
    rep.info("next", f"全部页面存完后：python3 analyze_features.py {out}")
    return rep.emit(False, "save_page")


if __name__ == "__main__":
    sys.exit(main())
