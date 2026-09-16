"""website-clone-functional 脚本共用的小工具（仅标准库）。

与 website-clone / website-clone-visual 里的同名文件故意保持独立：安装单位是目录，不做跨目录引用。
"""

from __future__ import annotations

import json
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

SCRIPTS_DIR = Path(__file__).resolve().parent
COLLECT_DIR = SCRIPTS_DIR / "collect"

INSTALL_HINT = (
    "未找到 playwright。安装（Homebrew / 系统 Python 会被 PEP 668 拦，用 venv 或 uv）：\n"
    "  python3 -m venv /tmp/wc-venv && /tmp/wc-venv/bin/pip install playwright && /tmp/wc-venv/bin/playwright install chromium\n"
    "  然后用 /tmp/wc-venv/bin/python 运行本脚本；或 uv run --with playwright python <script>\n"
    "装不上也没关系：按 SKILL.md 的「内联浏览器路径」逐页注入 collect/links.js 与 collect/features.js，结果存到 features/<page-id>/page.json。"
)


@dataclass
class Finding:
    level: str
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
        if as_json:
            print(json.dumps([f.__dict__ for f in self.findings], ensure_ascii=False, indent=2))
        else:
            if title:
                print(f"== {title} ==")
            for f in self.findings:
                print(f"[{f.level}] {f.where}: {f.message}")
            print(f"-- {self.errors} error(s), {self.warnings} warning(s), {len(self.findings) - self.errors - self.warnings} info")
        return 1 if self.errors else 0


def require_playwright():
    try:
        from playwright.sync_api import sync_playwright  # type: ignore

        return sync_playwright
    except Exception:
        print(INSTALL_HINT, file=sys.stderr)
        sys.exit(2)


def load_collect_script(name: str) -> str:
    path = COLLECT_DIR / f"{name}.js"
    if not path.exists():
        raise FileNotFoundError(f"缺少采集脚本 {path}")
    return path.read_text(encoding="utf-8")


def page_id_for(url: str, taken: set[str] | None = None) -> str:
    u = urlparse(url)
    path = u.path.strip("/") or "index"
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", path).strip("-") or "index"
    if u.query:
        q = re.sub(r"[^A-Za-z0-9=_-]+", "-", u.query).replace("=", "-").strip("-")
        slug = f"{slug}--{q[:40]}"
    slug = slug[:80]
    if taken is not None:
        base, n = slug, 2
        while slug in taken:
            slug = f"{base}-{n}"
            n += 1
        taken.add(slug)
    return slug


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def same_site(a: str, b: str) -> bool:
    """同一站点：主机名去掉 www 后相同。"""
    ha = urlparse(a).hostname or ""
    hb = urlparse(b).hostname or ""
    return ha.removeprefix("www.") == hb.removeprefix("www.")


def classify_url(url: str) -> str:
    """只看 URL 的页面类型粗分类，与 features.js 的 guessType 口径一致（后者还看 DOM）。"""
    p = (urlparse(url).path + "?" + urlparse(url).query).lower()
    if re.search(r"(admin|manage|dashboard|console|backend)", p):
        return "admin"
    if re.search(r"(login|signin|sign-in|register|signup|sign-up|auth|password)", p):
        return "auth"
    if re.search(r"(cart|checkout|order|pay)", p):
        return "checkout"
    if re.search(r"(search|\?q=|keyword=)", p):
        return "search"
    if re.search(r"(account|profile|user|member|/me\b)", p):
        return "account"
    if re.search(r"(privacy|terms|legal|policy|about|contact|faq|help)", p):
        return "legal"
    if re.search(r"(/p/|/product/|/item/|/detail|/post/|/article/|id=|/\d+/?$)", p):
        return "detail"
    if re.search(r"(list|category|collection|products|shop|blog|news|archive|tag)", p):
        return "list"
    path_only = urlparse(url).path
    if path_only in ("", "/") or re.match(r"^/(index|home)(\.\w+)?$", path_only):
        return "landing"
    return "content"
