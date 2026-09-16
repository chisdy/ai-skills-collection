#!/usr/bin/env python3
"""把采集到的素材 URL 下载到本地（仅标准库）。

读取 capture/<page>/assets.json（collect/assets.js 的输出，可多份），下载图片 / 背景图 / 视频 poster / 字体 / favicon，
写到 capture/assets/，并生成 capture/assets/manifest.json（URL → 本地路径、状态、大小、Content-Type）。
data: URI 会被解码成文件。脚本与样式表默认不下载（复刻不会原样复用它们），--include 可加。

用法：
  python3 download_assets.py <capture-dir> [--include script,stylesheet] [--max-mb 20] [--workers 8] [--json]
  python3 download_assets.py <assets.json> -o <out-dir>

内联浏览器路径也用它：把 Runtime.evaluate 拿到的 assets.js 结果存成 capture/<page>/assets.json 即可。
退出码：有下载失败的关键素材（image / font）为 1。
"""

from __future__ import annotations

import argparse
import base64
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import Report, human_bytes, read_json, safe_filename, write_json  # noqa: E402

DEFAULT_TYPES = {"image", "image-srcset", "background-image", "mask-image", "video-poster", "font", "favicon", "og-image", "manifest"}
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36 website-clone-visual/1.0"
EXT_BY_MIME = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/webp": ".webp",
    "image/gif": ".gif",
    "image/svg+xml": ".svg",
    "image/avif": ".avif",
    "font/woff2": ".woff2",
    "font/woff": ".woff",
    "font/ttf": ".ttf",
    "font/otf": ".otf",
    "application/font-woff2": ".woff2",
    "application/font-woff": ".woff",
    "video/mp4": ".mp4",
    "video/webm": ".webm",
    "text/css": ".css",
    "application/javascript": ".js",
    "text/javascript": ".js",
}


def collect_assets(paths: list[Path], types: set[str]) -> dict[str, dict]:
    merged: dict[str, dict] = {}
    for p in paths:
        data = read_json(p)
        for a in data.get("assets", []):
            if a.get("type") not in types:
                continue
            url = a["url"]
            if url not in merged:
                merged[url] = dict(a)
                merged[url]["pages"] = []
            merged[url]["pages"].append(str(p.parent.name))
    return merged


def save_data_uri(url: str, out_dir: Path) -> tuple[Path, int, str]:
    m = re.match(r"^data:([^;,]+)?(;base64)?,(.*)$", url, re.S)
    if not m:
        raise ValueError("无法解析 data URI")
    mime, is_b64, payload = m.group(1) or "application/octet-stream", bool(m.group(2)), m.group(3)
    raw = base64.b64decode(payload) if is_b64 else bytes(payload, "utf-8")
    ext = EXT_BY_MIME.get(mime, "")
    name = "datauri-" + safe_filename("data:" + mime + ":" + str(len(raw)) + ":" + payload[:64], ext)
    path = out_dir / name
    path.write_bytes(raw)
    return path, len(raw), mime


def fetch(url: str, out_dir: Path, max_bytes: int, referer: str | None) -> dict:
    t0 = time.time()
    if url.startswith("data:"):
        path, size, mime = save_data_uri(url, out_dir)
        return {"url": url[:80] + "…", "local": str(path.relative_to(out_dir.parent)), "status": 200, "bytes": size, "contentType": mime, "ms": int((time.time() - t0) * 1000)}
    req = Request(url, headers={"User-Agent": UA, "Accept": "*/*", **({"Referer": referer} if referer else {})})
    with urlopen(req, timeout=30) as resp:  # noqa: S310 - 目标 URL 来自用户指定站点
        ctype = (resp.headers.get("Content-Type") or "").split(";")[0].strip().lower()
        length = resp.headers.get("Content-Length")
        if length and int(length) > max_bytes:
            return {"url": url, "status": resp.status, "error": f"超过大小上限 {human_bytes(max_bytes)}（{human_bytes(int(length))}）", "contentType": ctype}
        data = resp.read(max_bytes + 1)
        if len(data) > max_bytes:
            return {"url": url, "status": resp.status, "error": f"超过大小上限 {human_bytes(max_bytes)}", "contentType": ctype}
        ext = EXT_BY_MIME.get(ctype, "")
        name = safe_filename(url, ext)
        if ext and not name.lower().endswith(ext) and "." not in Path(name).suffix:
            name += ext
        path = out_dir / name
        path.write_bytes(data)
        return {"url": url, "local": str(path.relative_to(out_dir.parent)), "status": resp.status, "bytes": len(data), "contentType": ctype, "ms": int((time.time() - t0) * 1000)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", help="capture 目录（递归找 */assets.json）或单个 assets.json")
    ap.add_argument("-o", "--out", help="输出目录（默认 <capture>/assets）")
    ap.add_argument("--include", default="", help="额外下载的类型，逗号分隔：script,stylesheet,video,audio,embed")
    ap.add_argument("--max-mb", type=float, default=20)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    src = Path(args.source)
    if src.is_dir():
        sources = sorted(src.glob("*/assets.json"))
        out_dir = Path(args.out) if args.out else src / "assets"
    else:
        sources = [src]
        out_dir = Path(args.out) if args.out else src.parent / "assets"
    rep = Report()
    if not sources:
        rep.error(str(src), "没找到 assets.json；先运行 capture_site.py 或把 collect/assets.js 的结果存到 capture/<page>/assets.json")
        return rep.emit(args.json, "download_assets")
    types = set(DEFAULT_TYPES) | {t.strip() for t in args.include.split(",") if t.strip()}
    assets = collect_assets(sources, types)
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / "manifest.json"
    manifest = read_json(manifest_path) if manifest_path.exists() else {"generatedAt": None, "items": {}}
    referer = None
    for p in sources:
        try:
            referer = read_json(p).get("url")
            break
        except Exception:
            pass

    todo = [u for u in assets if u not in manifest["items"] or "error" in manifest["items"][u]]
    rep.info("plan", f"{len(assets)} 个素材（{len(todo)} 个待下载，{len(assets) - len(todo)} 个已存在）→ {out_dir}")
    max_bytes = int(args.max_mb * 1024 * 1024)
    failed_key = 0
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(fetch, u, out_dir, max_bytes, referer): u for u in todo}
        for fut in as_completed(futs):
            u = futs[fut]
            meta = assets[u]
            try:
                r = fut.result()
            except Exception as e:  # noqa: BLE001
                r = {"url": u, "error": f"{type(e).__name__}: {e}"}
            r["type"] = meta.get("type")
            r["pages"] = meta.get("pages")
            if meta.get("alt"):
                r["alt"] = meta["alt"]
            if meta.get("family"):
                r["family"] = meta["family"]
            manifest["items"][u] = r
            if "error" in r:
                lvl = rep.error if meta.get("type") in ("image", "font", "background-image") else rep.warn
                lvl(u[:120], r["error"])
                if meta.get("type") in ("image", "font", "background-image"):
                    failed_key += 1
    manifest["generatedAt"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    ok = [v for v in manifest["items"].values() if "local" in v]
    manifest["summary"] = {"total": len(manifest["items"]), "downloaded": len(ok), "bytes": sum(v.get("bytes", 0) for v in ok), "failed": len(manifest["items"]) - len(ok)}
    write_json(manifest_path, manifest)
    rep.info("done", f"下载 {manifest['summary']['downloaded']} 个，共 {human_bytes(manifest['summary']['bytes'])}；失败 {manifest['summary']['failed']}；清单 {manifest_path}")
    if failed_key:
        rep.warn("copyright", "下载的图片 / 字体是原站素材，交付前在蓝图的素材清单里标注版权风险，由用户决定替换")
    return rep.emit(args.json, "download_assets")


if __name__ == "__main__":
    sys.exit(main())
