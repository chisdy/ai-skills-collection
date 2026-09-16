"""website-clone-visual 脚本共用的小工具。

只依赖标准库。Pillow 可选：有则做像素级对比与截图裁片，没有就跳过并说明。
与 website-clone / website-clone-functional 里的同名文件故意保持独立（安装单位是目录，不做跨目录引用）。
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

try:  # 可选依赖
    from PIL import Image  # type: ignore

    HAS_PIL = True
except Exception:  # pragma: no cover
    Image = None  # type: ignore
    HAS_PIL = False


SCRIPTS_DIR = Path(__file__).resolve().parent
COLLECT_DIR = SCRIPTS_DIR / "collect"

INSTALL_HINT = (
    "未找到 playwright。安装（Homebrew / 系统 Python 会被 PEP 668 拦，用 venv 或 uv）：\n"
    "  python3 -m venv /tmp/wc-venv && /tmp/wc-venv/bin/pip install playwright pillow && /tmp/wc-venv/bin/playwright install chromium\n"
    "  然后用 /tmp/wc-venv/bin/python 运行本脚本；或 uv run --with playwright,pillow python <script>\n"
    "装不上也没关系：按 references/capture-guide.md 的「内联浏览器路径」用 Cursor / Playwright MCP 注入同一批 collect/*.js。"
)


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
        """打印报告，返回进程退出码（有 ERROR 则 1）。"""
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
    """把 URL 变成目录名：/ → index；/products.html?category=x → products-html--category-x。"""
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


def parse_viewports(spec: str) -> list[dict]:
    out = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        m = re.match(r"^(\d+)x(\d+)$", part)
        if not m:
            raise ValueError(f"视口格式应为 WxH，得到 {part!r}")
        out.append({"width": int(m.group(1)), "height": int(m.group(2))})
    if not out:
        raise ValueError("至少一个视口")
    return out


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def safe_filename(url: str, default_ext: str = "") -> str:
    """稳定、可读、不重名的本地文件名：<sha1 前 10 位>-<原文件名>。"""
    u = urlparse(url)
    base = os.path.basename(u.path) or "asset"
    base = re.sub(r"[^A-Za-z0-9._-]+", "-", base)[:80]
    if "." not in base and default_ext:
        base += default_ext
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:10]
    return f"{digest}-{base}"


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def human_bytes(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f}{unit}" if unit == "B" else f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}TB"
