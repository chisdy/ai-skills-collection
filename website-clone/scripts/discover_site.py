#!/usr/bin/env python3
"""站点发现（仅标准库）：sitemap.xml / robots.txt / 首页与导航链接 BFS → site-map.json。

  python3 discover_site.py <url> -o clone-package/site-map.json [--max-pages 30] [--max-depth 2] [--timeout 15] [--render] [--json]

做的事：
  1. robots.txt：记录 Disallow 规则（写进 site-map.json 供合规确认）与 Sitemap: 行
  2. sitemap.xml（含 sitemap index）：拿 URL 清单
  3. 从首页开始 BFS 同域链接（限深限量），用 html.parser 抽 <a href>、<nav> / <header> / <footer> 归属
  4. 每页按 URL + 标题 + 表单 / 密码框 做启发式分类：landing / list / detail / auth / checkout / search / account / legal / form / content
  5. 登录墙识别：401 / 403、302 → login、页面只有密码表单
  6. SPA 识别：首页同域链接 < 3 或根容器为空 + <script type=module> → WARN，提示 --render（需 playwright）或用内联浏览器注入 scripts/collect/links.js

--render：每页额外用 Playwright 渲染后再抽链接（可选依赖；没装则报错并给出两种替代）。JS 渲染的列表（商品卡片）只有这样才能发现详情页。
产出 site-map.json：{origin, generatedAt, source, robots, pages[{url, pageId, type, title, depth, status, loginWall, inNav, forms}], warnings}
"""

from __future__ import annotations

import argparse
import gzip
import re
import sys
import time
import urllib.error
import urllib.request
from collections import deque
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse, urlunparse
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import Report, classify_url, now_iso, page_id_for, same_site, write_json  # noqa: E402

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36 website-clone-discover"
SKIP_RE = re.compile(r"(logout|signout|sign-out|log-out|退出|delete|remove|unsubscribe|\.(pdf|zip|jpg|jpeg|png|gif|svg|webp|mp4|mp3|css|js|xml|ico|woff2?)(\?|$)|^mailto:|^tel:|^javascript:|^#)", re.I)


class PageParser(HTMLParser):
    """抽链接（带区域）、标题、表单 / 密码框、根容器是否为空、module 脚本数。"""

    def __init__(self, base: str):
        super().__init__(convert_charrefs=True)
        self.base = base
        self.links: list[tuple[str, str, str]] = []  # (url, region, text)
        self.title = ""
        self._in_title = False
        self._stack: list[str] = []
        self.forms = 0
        self.password = False
        self.module_scripts = 0
        self.body_text_len = 0
        self.root_ids: list[str] = []
        self.h1 = ""
        self._in_h1 = False
        self._cur_a: list | None = None
        self.metas: dict[str, str] = {}

    def _region(self) -> str:
        for tag in reversed(self._stack):
            if tag in ("header", "nav", "footer", "aside"):
                return tag
        return "main"

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self._stack.append(tag)
        if tag == "title":
            self._in_title = True
        elif tag == "h1" and not self.h1:
            self._in_h1 = True
        elif tag == "a" and a.get("href"):
            self._cur_a = [urljoin(self.base, a["href"]), self._region(), ""]
        elif tag == "form":
            self.forms += 1
        elif tag == "input" and (a.get("type") or "").lower() == "password":
            self.password = True
        elif tag == "script" and (a.get("type") or "").lower() == "module":
            self.module_scripts += 1
        elif tag == "div" and a.get("id") in ("root", "app", "__next", "__nuxt", "app-root", "q-app"):
            self.root_ids.append(a["id"])
        elif tag == "meta" and a.get("name") in ("description", "generator") and a.get("content"):
            self.metas[a["name"]] = a["content"][:200]

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        elif tag == "h1":
            self._in_h1 = False
        elif tag == "a" and self._cur_a:
            self.links.append((self._cur_a[0], self._cur_a[1], re.sub(r"\s+", " ", self._cur_a[2]).strip()[:60]))
            self._cur_a = None
        while self._stack and self._stack.pop() != tag:
            pass

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        if self._in_h1:
            self.h1 += data
        if self._cur_a is not None:
            self._cur_a[2] += data
        if self._stack and self._stack[-1] not in ("script", "style", "title", "noscript"):
            self.body_text_len += len(data.strip())


def fetch(url: str, timeout: int) -> tuple[int, str, str, dict]:
    """返回 (status, final_url, text, headers)。4xx/5xx 也返回正文以便分类。"""
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            if resp.headers.get("Content-Encoding") == "gzip" or url.endswith(".gz"):
                try:
                    raw = gzip.decompress(raw)
                except Exception:  # noqa: BLE001
                    pass
            ctype = resp.headers.get("Content-Type", "")
            charset = re.search(r"charset=([\w-]+)", ctype)
            text = raw.decode(charset.group(1) if charset else "utf-8", errors="replace")
            return resp.status, resp.geturl(), text, dict(resp.headers)
    except urllib.error.HTTPError as e:
        try:
            text = e.read().decode("utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            text = ""
        return e.code, e.geturl() or url, text, dict(e.headers or {})


def read_robots(origin: str, timeout: int, rep: Report) -> dict:
    out = {"fetched": False, "disallow": [], "sitemaps": [], "crawlDelay": None}
    try:
        status, _, text, _ = fetch(origin + "/robots.txt", timeout)
    except Exception as e:  # noqa: BLE001
        rep.info("robots", f"robots.txt 不可达（{type(e).__name__}）")
        return out
    if status != 200:
        rep.info("robots", f"robots.txt HTTP {status}")
        return out
    out["fetched"] = True
    applies = False
    for line in text.splitlines():
        line = line.split("#")[0].strip()
        if not line or ":" not in line:
            continue
        k, v = [x.strip() for x in line.split(":", 1)]
        kl = k.lower()
        if kl == "user-agent":
            applies = v == "*" or "website-clone" in v.lower()
        elif kl == "disallow" and applies and v:
            out["disallow"].append(v)
        elif kl == "sitemap":
            out["sitemaps"].append(v)
        elif kl == "crawl-delay" and applies:
            out["crawlDelay"] = v
    if out["disallow"]:
        rep.warn("robots", f"robots.txt 对通用 UA 有 {len(out['disallow'])} 条 Disallow（{', '.join(out['disallow'][:5])}）——非站点所有者请与用户确认再继续；本脚本不会访问 Disallow 路径")
    return out


def disallowed(path: str, rules: list[str]) -> bool:
    for r in rules:
        pat = "^" + re.escape(r).replace(r"\*", ".*")
        if r.endswith("$"):
            pat = pat[:-2] + "$"
        if re.match(pat, path):
            return True
    return False


def read_sitemaps(urls: list[str], site_url: str, timeout: int, rep: Report, limit: int = 500) -> list[str]:
    """读 sitemap / sitemap index；index 里指向别的站的子 sitemap 一律跳过，不替第三方 sitemap 去请求任意地址。"""
    found: list[str] = []
    seen: set[str] = set()
    queue = deque(u for u in urls if same_site(u, site_url))
    hops = 0
    while queue and len(found) < limit and hops < 10:
        u = queue.popleft()
        hops += 1
        try:
            status, _, text, _ = fetch(u, timeout)
        except Exception as e:  # noqa: BLE001
            rep.info("sitemap", f"{u} 不可达（{type(e).__name__}）")
            continue
        if status != 200 or "<" not in text:
            rep.info("sitemap", f"{u} HTTP {status}")
            continue
        try:
            root = ET.fromstring(text.strip())
        except ET.ParseError:
            rep.info("sitemap", f"{u} 不是合法 XML")
            continue
        tag = root.tag.lower()
        locs = [el.text.strip() for el in root.iter() if el.tag.lower().endswith("loc") and el.text]
        if tag.endswith("sitemapindex"):
            children = [loc for loc in locs if same_site(loc, site_url)]
            if len(children) < len(locs):
                rep.info("sitemap", f"{u} 里 {len(locs) - len(children)} 个跨站子 sitemap 已跳过")
            queue.extend(children[:20])
        else:
            for loc in locs:
                if loc not in seen:
                    seen.add(loc)
                    found.append(loc)
    if found:
        rep.info("sitemap", f"sitemap 提供 {len(found)} 个 URL")
    return found


def classify(url: str, parsed: PageParser | None, status: int, final_url: str) -> tuple[str, bool]:
    t = classify_url(url)
    login_wall = False
    if status in (401, 403):
        login_wall = True
    if final_url and final_url != url and classify_url(final_url) == "auth":
        login_wall = True
    if parsed:
        if parsed.password and t not in ("auth",):
            if parsed.body_text_len < 1500:
                login_wall = True
            else:
                t = "auth" if t in ("content", "landing") else t
        if t == "content":
            if parsed.password:
                t = "auth"
            elif parsed.forms and parsed.body_text_len < 3000:
                t = "form"
            elif re.search(r"(list|category|collection|products|shop|blog|news|archive|tag|列表|分类|商品|文章)", parsed.title + parsed.h1, re.I):
                t = "list"
    return t, login_wall


class Renderer:
    """--render：用 Playwright 渲染每一页后注入本技能自己的 collect/links.js（可选依赖）。"""

    RENDER_HINT = "--render 需要 playwright：python3 -m venv /tmp/wc-venv && /tmp/wc-venv/bin/pip install playwright && /tmp/wc-venv/bin/playwright install chromium；或改用内联浏览器 browser_navigate 后 Runtime.evaluate 注入 scripts/collect/links.js"

    def __init__(self, timeout: int):
        # 缺依赖时抛 ImportError，由 main() 统一走 rep.error + rep.emit，退出码语义与其他错误一致
        from playwright.sync_api import sync_playwright  # type: ignore

        self.js = (Path(__file__).resolve().parent / "collect" / "links.js").read_text(encoding="utf-8")
        self.timeout = timeout
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch()
        self.page = self._browser.new_page(viewport={"width": 1440, "height": 900}, user_agent=UA)

    def links(self, url: str) -> tuple[list[tuple[str, str, str]], str]:
        try:
            self.page.goto(url, wait_until="networkidle", timeout=self.timeout * 1000)
        except Exception:  # noqa: BLE001
            pass
        self.page.wait_for_timeout(600)
        data = self.page.evaluate(self.js)
        links = [(lk["url"], "nav" if lk.get("inMainNav") else (lk.get("region") or "main"), (lk.get("texts") or [""])[0]) for lk in data.get("links", []) if lk.get("sameOrigin")]
        return links, self.page.title()

    def close(self):
        try:
            self._browser.close()
            self._pw.stop()
        except Exception:  # noqa: BLE001
            pass


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("url")
    ap.add_argument("-o", "--out", default="site-map.json")
    ap.add_argument("--max-pages", type=int, default=30)
    ap.add_argument("--max-depth", type=int, default=2)
    ap.add_argument("--timeout", type=int, default=15)
    ap.add_argument("--delay", type=float, default=0.3, help="请求间隔秒（robots Crawl-delay 更大时以它为准）")
    ap.add_argument("--render", action="store_true", help="每页额外用 Playwright 渲染后抽链接（SPA / JS 渲染的列表）；需要 playwright")
    ap.add_argument("--no-sitemap", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    rep = Report()
    url = args.url if re.match(r"^https?://", args.url) else "https://" + args.url
    pu = urlparse(url)
    origin = urlunparse((pu.scheme, pu.netloc, "", "", "", ""))
    t0 = time.time()

    robots = read_robots(origin, args.timeout, rep)
    delay = max(args.delay, float(robots["crawlDelay"] or 0)) if robots.get("crawlDelay") and str(robots["crawlDelay"]).replace(".", "").isdigit() else args.delay
    sitemap_urls: list[str] = []
    if not args.no_sitemap:
        candidates = robots["sitemaps"] or [origin + "/sitemap.xml", origin + "/sitemap_index.xml"]
        sitemap_urls = [u for u in read_sitemaps(candidates, url, args.timeout, rep) if same_site(u, url) and not SKIP_RE.search(u)]

    pages: list[dict] = []
    taken: set[str] = set()
    seen: set[str] = set()
    queue: deque[tuple[str, int, bool, str]] = deque([(url, 0, True, "")])
    for su in sitemap_urls[: args.max_pages * 2]:
        queue.append((su, 1, False, ""))
    nav_links_home = 0
    spa_hint = False
    rendered_used = False
    renderer = None
    if args.render:
        try:
            renderer = Renderer(args.timeout)
        except ImportError:
            rep.error("render", Renderer.RENDER_HINT)
            return rep.emit(args.json, "discover_site")

    while queue and len(pages) < args.max_pages:
        u, depth, in_nav, text = queue.popleft()
        u = u.split("#")[0]
        if u in seen or not same_site(u, url) or SKIP_RE.search(u):
            continue
        if disallowed(urlparse(u).path, robots["disallow"]):
            rep.info(u, "robots Disallow，跳过")
            seen.add(u)
            continue
        seen.add(u)
        try:
            status, final_url, html, headers = fetch(u, args.timeout)
        except Exception as e:  # noqa: BLE001
            rep.warn(u, f"抓取失败：{type(e).__name__}: {str(e)[:120]}")
            if depth == 0:
                return rep.emit(args.json, "discover_site")
            continue
        ctype = headers.get("Content-Type", "") if isinstance(headers, dict) else ""
        parsed = None
        if "html" in ctype.lower() or html.lstrip()[:15].lower().startswith(("<!doctype", "<html")):
            parsed = PageParser(final_url or u)
            try:
                parsed.feed(html)
            except Exception:  # noqa: BLE001
                pass
        ptype, login_wall = classify(u, parsed, status, final_url)
        pid = page_id_for(u, taken)
        entry = {
            "url": u,
            "pageId": pid,
            "type": ptype,
            "title": re.sub(r"\s+", " ", parsed.title).strip()[:120] if parsed else None,
            "h1": re.sub(r"\s+", " ", parsed.h1).strip()[:100] if parsed else None,
            "depth": depth,
            "status": status,
            "finalUrl": final_url if final_url != u else None,
            "loginWall": login_wall,
            "inNav": in_nav,
            "linkText": text or None,
            "forms": parsed.forms if parsed else 0,
            "fromSitemap": depth == 1 and not text and u in sitemap_urls,
        }
        if depth == 0 and parsed and parsed.metas.get("generator"):
            entry["generator"] = parsed.metas["generator"]
        pages.append(entry)
        if not parsed or depth >= args.max_depth:
            continue
        same = [(href, region, txt) for href, region, txt in parsed.links if same_site(href, url) and not SKIP_RE.search(href)]
        if depth == 0:
            nav_links_home = len({href.split("#")[0] for href, _, _ in same})
            spa_hint = bool(nav_links_home < 3 or (parsed.root_ids and parsed.body_text_len < 300 and parsed.module_scripts >= 1))
        if renderer:
            try:
                rl, rtitle = renderer.links(u)
                static_urls = {href.split("#")[0] for href, _, _ in same}
                extra = [x for x in rl if not SKIP_RE.search(x[0]) and x[0].split("#")[0] not in static_urls]
                same += extra
                entry["title"] = entry["title"] or rtitle
                entry["renderedLinks"] = len(extra)
                rendered_used = True
                if depth == 0:
                    rep.info("render", f"首页渲染后新增 {len(extra)} 个静态 HTML 里没有的同域链接")
            except Exception as e:  # noqa: BLE001
                rep.warn(u, f"渲染失败（{type(e).__name__}），只用静态链接")
        for href, region, txt in same:
            href = href.split("#")[0]
            if href not in seen:
                queue.append((href, depth + 1, region in ("header", "nav"), txt))
        time.sleep(delay)
    if renderer:
        renderer.close()

    # 类型统计与 WARN
    types: dict[str, int] = {}
    for p in pages:
        types[p["type"]] = types.get(p["type"], 0) + 1
    warnings: list[str] = []
    if spa_hint and not rendered_used:
        msg = (
            f"首页只解析到 {nav_links_home} 个同域链接"
            + ("，且根容器为空 + module 脚本（像 SPA）" if pages and pages[0].get("forms") == 0 and nav_links_home < 3 else "")
            + "：标准库拿不到 JS 渲染的导航。有 Playwright → 加 --render；否则用内联浏览器 browser_navigate 打开首页，Runtime.evaluate 注入 scripts/collect/links.js，把链接补进 site-map.json 再继续。site-map.json 只有首页时不要继续委派"
        )
        warnings.append(msg)
        rep.warn("spa", msg)
    if len(pages) <= 1:
        warnings.append("只发现 1 页")
    walls = [p for p in pages if p["loginWall"]]
    if walls:
        rep.warn("auth", f"{len(walls)} 页在登录墙后（{', '.join(p['url'] for p in walls[:3])}）：用户有账号时由其在内联浏览器登录后采，或子技能脚本用 --storage-state")
    if not types.get("list") or not types.get("detail"):
        rep.info("coverage", f"类型分布 {types}；缺 list / detail 时子技能采集范围会偏窄，可加大 --max-pages / --max-depth 或手动补 URL")
    if pages and pages[0].get("generator"):
        rep.info("platform", f"首页 generator：{pages[0]['generator']}")

    out = Path(args.out)
    write_json(
        out,
        {
            "origin": origin,
            "startUrl": url,
            "generatedAt": now_iso(),
            "source": "discover_site" + ("+render" if rendered_used else ""),
            "robots": robots,
            "pageTypes": types,
            "pages": pages,
            "warnings": warnings,
            "options": {"maxPages": args.max_pages, "maxDepth": args.max_depth},
            "elapsedSec": round(time.time() - t0, 1),
        },
    )
    rep.info("site", f"{len(pages)} 页 {types} → {out}（{round(time.time() - t0, 1)}s）")
    return rep.emit(args.json, "discover_site")


if __name__ == "__main__":
    sys.exit(main())
