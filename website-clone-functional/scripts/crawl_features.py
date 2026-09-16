#!/usr/bin/env python3
"""用 Playwright 逐页采集功能特征与网络请求，落盘到 features/。

  features/
    site-map.json                 发现到的页面（自带 BFS 或外部传入）
    network.json                  所有 XHR / fetch / document 请求：方法、路径、query 键、请求体键、状态、响应 JSON 形状；被拦截的标 blocked
    summary.json                  采集参数、页面数、拦截统计
    <page-id>/page.json           collect/features.js 的输出
    <page-id>/links.json          collect/links.js 的输出
    <page-id>/probes.json         只读交互探测（Tab / 排序 / 分页 / 筛选）触发的请求

用法：
  python crawl_features.py <url | site-map.json> -o features/ [--max-pages 20] [--max-depth 3]
      [--storage-state state.json] [--admin-url https://site/admin] [--no-probe] [--wait 800] [--timeout 45000] [--json]
      [--allow-writes]   ← 仅自有 / 测试站点！

安全默认（合规要求）：
  * 所有非 GET / HEAD / OPTIONS 请求被 page.route 拦截并 abort，记录为 blocked——采集不会在目标站产生任何写操作
  * 不提交表单、不点击注册 / 下单 / 评论 / 收藏 / 关注 / 删除等写按钮；字段从 DOM 静态读取
  * 只读探测仅限：Tab 切换、排序下拉、分页下一页、筛选单选 / 复选 —— 且发生在拦截生效的前提下
  * --allow-writes 关闭拦截，只在用户明确声明目标是自有 / 测试站点时使用；开启时脚本会打印醒目警告并写入 summary.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from collections import deque
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import Report, classify_url, load_collect_script, now_iso, page_id_for, read_json, require_playwright, same_site, write_json  # noqa: E402

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
SKIP_LINK_RE = re.compile(r"(logout|signout|sign-out|log-out|退出|delete|remove|unsubscribe|\.(pdf|zip|jpg|jpeg|png|gif|svg|webp|mp4|mp3|css|js|xml|ico)(\?|$)|^mailto:|^tel:|^javascript:)", re.I)
SENSITIVE_KEYS = re.compile(r"(password|passwd|pwd|token|secret|authorization|cookie|session|card|cvv|ssn|身份证|密码)", re.I)
MAX_BODY = 4000


def parse_source(source: str) -> tuple[list[dict], bool]:
    p = Path(source)
    if p.exists() and p.suffix == ".json":
        data = read_json(p)
        pages = data if isinstance(data, list) else data.get("pages", [])
        return [x if isinstance(x, dict) else {"url": x} for x in pages], True
    if not re.match(r"^https?://", source):
        source = "https://" + source
    return [{"url": source, "type": classify_url(source), "depth": 0}], False


def shape_of(obj, depth: int = 0):
    """响应 JSON 的顶层形状：对象给键（与值类型），数组给长度与首项形状。递归两层。"""
    if depth > 2:
        return type(obj).__name__
    if isinstance(obj, dict):
        return {k: (shape_of(v, depth + 1) if isinstance(v, (dict, list)) else type(v).__name__) for k, v in list(obj.items())[:25]}
    if isinstance(obj, list):
        return {"__array__": len(obj), "item": shape_of(obj[0], depth + 1) if obj else None}
    return type(obj).__name__


def redact(obj):
    if isinstance(obj, dict):
        return {k: ("***" if SENSITIVE_KEYS.search(k) else redact(v)) for k, v in obj.items()}
    if isinstance(obj, list):
        return [redact(x) for x in obj[:10]]
    if isinstance(obj, str) and len(obj) > 200:
        return obj[:200] + "…"
    return obj


class NetworkLog:
    def __init__(self, allow_writes: bool):
        self.entries: list[dict] = []
        self.allow_writes = allow_writes
        self.blocked = 0
        self.current_page: str | None = None
        self.current_trigger: str = "load"
        self.self_tested = False

    def attach(self, page):
        page.route("**/*", self._route)
        page.on("response", self._on_response)
        page.on("requestfailed", self._on_failed)

    def _route(self, route):
        req = route.request
        if req.method not in SAFE_METHODS and not self.allow_writes:
            self.blocked += 1
            self.entries.append(self._entry(req, status=None, blocked=True))
            route.abort("blockedbyclient")
            return
        route.continue_()

    def _entry(self, req, status, blocked=False) -> dict:
        u = urlparse(req.url)
        body_keys = None
        body_sample = None
        if req.method not in SAFE_METHODS:
            try:
                raw = req.post_data
                if raw:
                    try:
                        parsed = json.loads(raw)
                        body_keys = list(parsed.keys())[:30] if isinstance(parsed, dict) else ["<array>"]
                        body_sample = redact(parsed) if isinstance(parsed, dict) else None
                    except Exception:  # noqa: BLE001
                        body_keys = [k for k in re.findall(r"(?:^|&)([^=&]+)=", raw)][:30]
            except Exception:  # noqa: BLE001
                pass
        return {
            "page": self.current_page,
            "trigger": self.current_trigger,
            "method": req.method,
            "url": req.url,
            "host": u.hostname,
            "path": u.path,
            "queryKeys": sorted({k for k in re.findall(r"(?:^|&)([^=&]+)=", u.query)}) if u.query else [],
            "resourceType": req.resource_type,
            "sameSite": same_site(req.url, self.current_page or req.url),
            "status": status,
            "blocked": blocked,
            "bodyKeys": body_keys,
            "bodySample": body_sample,
            "time": round(time.time(), 3),
        }

    def _on_response(self, resp):
        req = resp.request
        if req.resource_type not in ("xhr", "fetch", "document") and not re.search(r"\.json(\?|$)|/api/|/graphql|/v\d+/", req.url):
            return
        e = self._entry(req, resp.status)
        ctype = (resp.headers.get("content-type") or "").split(";")[0].strip()
        e["contentType"] = ctype
        if "json" in ctype or re.search(r"\.json(\?|$)", req.url):
            try:
                body = resp.body()
                e["responseBytes"] = len(body)
                data = json.loads(body[:2_000_000])
                e["responseShape"] = shape_of(data)
                sample = data[0] if isinstance(data, list) and data else data
                e["responseSample"] = redact(sample) if isinstance(sample, (dict, list)) else sample
                if isinstance(e.get("responseSample"), dict):
                    e["responseSample"] = dict(list(e["responseSample"].items())[:20])
            except Exception:  # noqa: BLE001
                pass
        elif req.resource_type == "document":
            e["redirected"] = resp.status in (301, 302, 303, 307, 308)
            e["location"] = resp.headers.get("location")
        self.entries.append(e)

    def _on_failed(self, req):
        if req.method in SAFE_METHODS and req.resource_type in ("xhr", "fetch"):
            self.entries.append({**self._entry(req, None), "failed": req.failure})


def collect_page(page, url: str, out_dir: Path, args, net: NetworkLog, rep: Report) -> tuple[dict | None, dict | None, dict]:
    net.current_page = url
    net.current_trigger = "load"
    try:
        resp = page.goto(url, wait_until="networkidle", timeout=args.timeout)
    except Exception as e:  # noqa: BLE001
        if "Timeout" in type(e).__name__ or "timeout" in str(e).lower():
            rep.warn(url, "networkidle 超时，按 load 继续")
            try:
                page.wait_for_load_state("load", timeout=args.timeout)
            except Exception:  # noqa: BLE001
                pass
            resp = None
        else:
            raise
    page.wait_for_timeout(args.wait)
    final_url = page.url
    status = resp.status if resp else None
    # 滚动一遍触发懒加载与无限滚动的首批请求
    page.evaluate(
        """async () => { const step = Math.max(300, innerHeight * 0.8); for (let y = 0; y < document.documentElement.scrollHeight && y < 12000; y += step) { scrollTo(0, y); await new Promise(r => setTimeout(r, 150)); } scrollTo(0, 0); }"""
    )
    page.wait_for_timeout(300)

    if not net.self_tested:
        # 拦截器自检：向目标站自己的 origin 发一个不存在路径的 POST，必须被 abort（不会到达服务器）
        net.current_trigger = "self-test"
        outcome = page.evaluate(
            """async () => { try { const r = await fetch('/__website-clone-probe__', { method: 'POST', body: '{}' }); return 'reached:' + r.status; } catch (e) { return 'aborted'; } }"""
        )
        net.current_trigger = "load"
        net.self_tested = True
        if outcome == "aborted" and not args.allow_writes:
            rep.info("safety", "拦截器自检通过：POST 被 abort，未到达目标站")
        elif not args.allow_writes:
            rep.error("safety", f"拦截器自检失败（{outcome}）：写请求可能会到达目标站，停止采集")
            raise RuntimeError("write-block self-test failed")

    features = page.evaluate(load_collect_script("features"))
    links = page.evaluate(load_collect_script("links"))
    features["httpStatus"] = status
    features["finalUrl"] = final_url
    features["redirectedToLogin"] = bool(final_url != url and classify_url(final_url) == "auth")
    features["captureMethod"] = "script"

    probes: dict = {"enabled": not args.no_probe, "actions": []}
    if not args.no_probe:
        probes["actions"] = run_probes(page, features, net, rep, url)
    write_json(out_dir / "page.json", features)
    write_json(out_dir / "links.json", links)
    write_json(out_dir / "probes.json", probes)
    return features, links, probes


def run_probes(page, features: dict, net: NetworkLog, rep: Report, url: str) -> list[dict]:
    """只读交互探测：Tab、排序、分页下一页、筛选。每个动作记录触发的请求数与 URL 变化。写按钮一律不碰。"""
    actions = []

    def snapshot(label: str):
        before = len(net.entries)
        before_url = page.url
        net.current_trigger = label
        return before, before_url

    def finish(label: str, before: int, before_url: str, detail: str):
        page.wait_for_timeout(600)
        new = [e for e in net.entries[before:] if e.get("resourceType") in ("xhr", "fetch") or e.get("blocked")]
        actions.append(
            {
                "action": label,
                "detail": detail,
                "requests": len(new),
                "blocked": sum(1 for e in new if e.get("blocked")),
                "urlChanged": page.url != before_url,
                "urlAfter": page.url if page.url != before_url else None,
                "requestPaths": sorted({e["path"] for e in new})[:8],
            }
        )
        net.current_trigger = "load"

    try:
        # Tab
        tabs = features.get("controls", {}).get("tabs") or []
        if tabs and len(tabs[0].get("items", [])) >= 2:
            b, bu = snapshot("tab")
            page.locator(tabs[0]["path"]).locator("[role=tab], button, a").nth(1).click(timeout=2000)
            finish("tab", b, bu, tabs[0]["items"][1])
        # 排序
        sorts = [s for s in features.get("controls", {}).get("sorts") or [] if s.get("isSort") and len(s.get("options", [])) >= 2]
        if sorts:
            b, bu = snapshot("sort")
            sel = page.locator("select").filter(has_text=sorts[0]["options"][1]).first
            sel.select_option(index=1, timeout=2000)
            finish("sort", b, bu, sorts[0]["options"][1])
        # 筛选（第二个单选 / 复选）
        filters = features.get("controls", {}).get("filters") or []
        if filters and len(filters[0].get("options", [])) >= 2 and filters[0].get("name"):
            b, bu = snapshot("filter")
            opt = filters[0]["options"][1]
            loc = page.locator(f"input[name='{filters[0]['name']}'][value='{opt.get('value')}']").first
            loc.check(timeout=2000, force=True) if filters[0]["type"] == "checkbox" else loc.click(timeout=2000, force=True)
            finish("filter", b, bu, f"{filters[0].get('label') or filters[0]['name']} = {opt.get('label') or opt.get('value')}")
        # 分页下一页
        pags = features.get("controls", {}).get("paginations") or []
        if pags:
            b, bu = snapshot("pagination")
            nxt = page.locator(pags[0]["path"]).locator("a, button").filter(has_text=re.compile(r"(下一|next|›|»|>)", re.I)).first
            if nxt.count() and nxt.is_enabled():
                nxt.click(timeout=2000)
                finish("pagination", b, bu, "next")
            else:
                net.current_trigger = "load"
        # 加载更多
        if features.get("controls", {}).get("loadMore"):
            b, bu = snapshot("load-more")
            page.get_by_role("button", name=re.compile(features["controls"]["loadMore"][0])).first.click(timeout=2000)
            finish("load-more", b, bu, features["controls"]["loadMore"][0])
    except Exception as e:  # noqa: BLE001
        net.current_trigger = "load"
        rep.info(url, f"只读探测中断（{type(e).__name__}），不影响静态采集")
    return actions


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", help="URL 或 site-map.json")
    ap.add_argument("-o", "--out", default="features")
    ap.add_argument("--max-pages", type=int, default=20)
    ap.add_argument("--max-depth", type=int, default=3)
    ap.add_argument("--storage-state")
    ap.add_argument("--admin-url", action="append", default=[], help="后台入口 URL，可多次；采到的页面 type 标 admin")
    ap.add_argument("--no-probe", action="store_true", help="不做只读交互探测")
    ap.add_argument("--allow-writes", action="store_true", help="不拦截写请求。仅自有 / 测试站点！")
    ap.add_argument("--wait", type=int, default=800)
    ap.add_argument("--timeout", type=int, default=45000)
    ap.add_argument("--locale", default="zh-CN")
    ap.add_argument("--headed", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    sync_playwright = require_playwright()
    rep = Report()
    if args.allow_writes:
        print("!!! --allow-writes 已开启：写请求不会被拦截，只读探测可能在目标站产生真实数据。确认这是你自有 / 测试站点。", file=sys.stderr)
        rep.warn("safety", "--allow-writes 开启：本次采集可能在目标站产生写操作")
    else:
        rep.info("safety", "默认拦截所有非 GET/HEAD/OPTIONS 请求，不提交表单、不点写按钮")

    seeds, external_map = parse_source(args.source)
    if not seeds:
        rep.error("args", "没有可采集的页面")
        return rep.emit(args.json, "crawl_features")
    for a in args.admin_url:
        seeds.append({"url": a, "type": "admin", "depth": 0, "admin": True})
    origin_url = seeds[0]["url"]
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    net = NetworkLog(allow_writes=args.allow_writes)
    pages_done: list[dict] = []
    taken: set[str] = set()
    seen: set[str] = set()
    queue = deque(seeds)
    t0 = time.time()

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=not args.headed)
        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, locale=args.locale, storage_state=args.storage_state)
        page = ctx.new_page()
        page.set_default_timeout(args.timeout)
        net.attach(page)
        while queue and len(pages_done) < args.max_pages:
            item = queue.popleft()
            url = item["url"].split("#")[0]
            if url in seen:
                continue
            seen.add(url)
            depth = item.get("depth", 0)
            pid = page_id_for(url, taken)
            pdir = out / pid
            try:
                features, links, probes = collect_page(page, url, pdir, args, net, rep)
            except Exception as e:  # noqa: BLE001
                rep.error(url, f"采集失败：{type(e).__name__}: {str(e).splitlines()[0][:200]}")
                continue
            ptype = "admin" if item.get("admin") or (features or {}).get("pageType") == "admin" else (features or {}).get("pageType") or classify_url(url)
            entry = {
                "url": url,
                "pageId": pid,
                "type": ptype,
                "title": (features or {}).get("title"),
                "depth": depth,
                "loginWall": bool((features or {}).get("loginWall") or (features or {}).get("redirectedToLogin")),
                "httpStatus": (features or {}).get("httpStatus"),
                "forms": len((features or {}).get("forms", [])),
                "lists": len((features or {}).get("lists", [])),
                "probes": len((probes or {}).get("actions", [])),
            }
            pages_done.append(entry)
            rep.info(url, f"{ptype}{'（登录墙）' if entry['loginWall'] else ''} forms {entry['forms']} lists {entry['lists']} probes {entry['probes']} → {pdir.name}")
            if not external_map and links and depth < args.max_depth:
                for lk in links.get("links", []):
                    u = lk["url"]
                    if not lk.get("sameOrigin") or not same_site(u, origin_url) or SKIP_LINK_RE.search(u) or u in seen:
                        continue
                    queue.append({"url": u, "type": classify_url(u), "depth": depth + 1, "text": (lk.get("texts") or [""])[0]})
        ctx.close()
        browser.close()

    write_json(out / "site-map.json", {"generatedAt": now_iso(), "origin": origin_url, "source": "external" if external_map else "crawl", "pages": pages_done})
    for e in net.entries:
        e.pop("time", None)
    write_json(out / "network.json", {"generatedAt": now_iso(), "allowWrites": args.allow_writes, "blocked": net.blocked, "count": len(net.entries), "entries": net.entries})
    api_like = [e for e in net.entries if e.get("resourceType") in ("xhr", "fetch") or re.search(r"\.json(\?|$)|/api/", e["url"])]
    summary = {
        "generatedAt": now_iso(),
        "source": args.source,
        "pages": len(pages_done),
        "types": {t: sum(1 for p in pages_done if p["type"] == t) for t in sorted({p["type"] for p in pages_done})},
        "loginWalls": sum(1 for p in pages_done if p["loginWall"]),
        "network": {"total": len(net.entries), "apiLike": len(api_like), "blocked": net.blocked, "allowWrites": args.allow_writes},
        "elapsedSec": round(time.time() - t0, 1),
        "options": {k: v for k, v in vars(args).items() if k != "json"},
    }
    write_json(out / "summary.json", summary)
    rep.info("site", f"{len(pages_done)} 页，{len(api_like)} 条 API 类请求，拦截 {net.blocked} 个写请求 → {out}（{summary['elapsedSec']}s）")
    if not external_map and len(pages_done) == 1 and (links or {}).get("sameOrigin", 0) < 3:
        rep.warn("discover", "只发现了 1 页且同域链接极少：可能是 SPA 导航在交互后才渲染、或链接是按钮。加大 --wait，或用内联浏览器展开菜单后手动补页面清单")
    if summary["loginWalls"]:
        rep.warn("auth", f"{summary['loginWalls']} 页在登录墙后：用户有账号时用内联浏览器登录后采，或提供 --storage-state")
    rep.info("next", f"python3 analyze_features.py {out} -o {out / 'features.json'}")
    return rep.emit(args.json, "crawl_features")


if __name__ == "__main__":
    sys.exit(main())
