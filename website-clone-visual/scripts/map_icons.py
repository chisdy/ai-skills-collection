#!/usr/bin/env python3
"""把采集到的图标映射到开源图标库（Lucide / Heroicons / Tabler / Phosphor …）的候选符号（仅标准库）。

思路：从每个图标的语义线索（aria-label、title、所在按钮 / 链接文字、class 名、Font Awesome 类名、href）提关键词，
中文词先查内置词表翻成英文，再请求 Iconify 搜索 API（https://api.iconify.design/search）拿候选；
按 stroke / fill 风格给出推荐。断网或 API 失败不报错：candidates 为空、保留关键词，让模型对着 icons/*.svg 与截图裁片人工挑选。

用法：
  python3 map_icons.py capture/ [--libraries lucide,heroicons,tabler] [--offline] [--timeout 8] [-o capture/icons-map.json]

输出 icons-map.json：{ icons: [{ id, kind, pages, file, keywords, candidates: {lucide: [...], ...}, recommended, confidence, needsReview }] }
之后重跑 analyze_capture.py，蓝图第 5 节会带上映射建议。退出码始终 0（映射是建议不是校验）。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import Report, read_json, write_json  # noqa: E402

ICONIFY = "https://api.iconify.design/search"
# 中文 / 常见词 → 图标库常用英文名
ZH = {
    "搜索": "search",
    "查找": "search",
    "购物车": "shopping-cart",
    "加入购物车": "shopping-cart",
    "结算": "shopping-bag",
    "订单": "receipt",
    "登录": "log-in",
    "登出": "log-out",
    "退出": "log-out",
    "注册": "user-plus",
    "用户": "user",
    "账户": "user",
    "我的": "user",
    "头像": "user-circle",
    "菜单": "menu",
    "导航": "menu",
    "关闭": "x",
    "首页": "home",
    "主页": "home",
    "返回": "arrow-left",
    "上一": "chevron-left",
    "下一": "chevron-right",
    "更多": "ellipsis",
    "展开": "chevron-down",
    "收起": "chevron-up",
    "下拉": "chevron-down",
    "箭头": "arrow-right",
    "前往": "arrow-right",
    "查看全部": "arrow-right",
    "浏览全部": "arrow-right",
    "了解更多": "arrow-right",
    "立即": "arrow-right",
    "心愿": "heart",
    "喜欢": "heart",
    "收藏": "bookmark",
    "点赞": "thumbs-up",
    "分享": "share",
    "评论": "message-circle",
    "留言": "message-square",
    "消息": "message-circle",
    "通知": "bell",
    "提醒": "bell",
    "设置": "settings",
    "编辑": "pencil",
    "删除": "trash",
    "移除": "x",
    "添加": "plus",
    "新增": "plus",
    "增加": "plus",
    "减少": "minus",
    "确认": "check",
    "完成": "check",
    "成功": "check-circle",
    "错误": "x-circle",
    "警告": "alert-triangle",
    "提示": "info",
    "帮助": "help-circle",
    "问题": "help-circle",
    "电话": "phone",
    "联系": "phone",
    "邮箱": "mail",
    "邮件": "mail",
    "地址": "map-pin",
    "位置": "map-pin",
    "地图": "map",
    "时间": "clock",
    "日期": "calendar",
    "日历": "calendar",
    "下载": "download",
    "上传": "upload",
    "文件": "file",
    "文档": "file-text",
    "图片": "image",
    "视频": "video",
    "播放": "play",
    "暂停": "pause",
    "音量": "volume-2",
    "静音": "volume-x",
    "筛选": "filter",
    "过滤": "filter",
    "排序": "arrow-up-down",
    "刷新": "refresh-cw",
    "重置": "rotate-ccw",
    "复制": "copy",
    "链接": "link",
    "外部": "external-link",
    "锁": "lock",
    "密码": "lock",
    "安全": "shield",
    "质保": "shield-check",
    "保障": "shield-check",
    "认证": "badge-check",
    "星": "star",
    "评分": "star",
    "灯": "lightbulb",
    "光": "sun",
    "太阳": "sun",
    "月亮": "moon",
    "夜间": "moon",
    "主题": "sun-moon",
    "眼睛": "eye",
    "隐藏": "eye-off",
    "显示": "eye",
    "卡车": "truck",
    "发货": "truck",
    "配送": "truck",
    "物流": "package",
    "包裹": "package",
    "礼物": "gift",
    "优惠": "tag",
    "标签": "tag",
    "价格": "tag",
    "钱": "wallet",
    "支付": "credit-card",
    "语言": "globe",
    "全球": "globe",
    "国际": "globe",
    "翻译": "languages",
    "微信": "message-circle",
    "微博": "at-sign",
    "全屏": "maximize",
    "退出全屏": "minimize",
    "购买": "shopping-bag",
    "商店": "store",
    "商品": "package",
    "分类": "layout-grid",
    "网格": "layout-grid",
    "列表": "list",
    "表格": "table",
    "图表": "bar-chart",
    "团队": "users",
    "公司": "building",
    "关于": "info",
    "博客": "newspaper",
    "新闻": "newspaper",
    "文章": "file-text",
    "书": "book-open",
    "学习": "graduation-cap",
    "trophy": "trophy",
    "奖": "award",
    "火": "flame",
    "热": "flame",
    "新品": "sparkles",
    "推荐": "sparkles",
    "闪": "zap",
    "快": "zap",
    "飞机": "send",
    "发送": "send",
    "订阅": "mail",
}
# Font Awesome / Material 等类名 → 通用名
FA_ALIAS = {
    "cart-shopping": "shopping-cart",
    "magnifying-glass": "search",
    "xmark": "x",
    "bars": "menu",
    "right-to-bracket": "log-in",
    "right-from-bracket": "log-out",
    "truck-fast": "truck",
    "circle-check": "check-circle",
    "circle-xmark": "x-circle",
    "triangle-exclamation": "alert-triangle",
    "circle-info": "info",
    "circle-question": "help-circle",
    "envelope": "mail",
    "location-dot": "map-pin",
    "gear": "settings",
    "pen-to-square": "pencil",
    "trash-can": "trash",
    "arrow-up-right-from-square": "external-link",
    "chevron-down": "chevron-down",
    "user-large": "user",
    "heart": "heart",
    "star": "star",
    "phone": "phone",
    "lock": "lock",
    "globe": "globe",
    "shield-halved": "shield",
    "bell": "bell",
    "house": "home",
}
STOP = {
    "btn",
    "button",
    "icon",
    "svg",
    "img",
    "logo",
    "link",
    "nav",
    "item",
    "wrapper",
    "inner",
    "active",
    "primary",
    "secondary",
    "ghost",
    "sm",
    "md",
    "lg",
    "xl",
    "solid",
    "regular",
    "brands",
    "fa",
    "fas",
    "far",
    "fab",
    "light",
    "duotone",
    "mark",
    "text",
    "span",
    "i",
    "a",
}


def keywords_for(icon: dict) -> list[str]:
    kws: list[str] = []
    seen = set()

    def add(k: str | None):
        if not k:
            return
        k = k.strip().lower()
        k = re.sub(r"[^a-z0-9\u4e00-\u9fff -]+", " ", k).strip()
        if not k or k in seen or k in STOP:
            return
        seen.add(k)
        kws.append(k)

    def add_text(t: str | None):
        if not t:
            return
        t = t.strip()
        for zh, en in ZH.items():
            if zh in t:
                add(en)
        if re.search(r"[a-zA-Z]", t) and len(t) <= 30:
            for w in re.split(r"[\s/|·,._-]+", t):
                if len(w) >= 3:
                    add(w)

    occs = icon.get("occurrences") or [icon]
    for occ in occs[:3]:
        add_text(occ.get("ariaLabel"))
        add_text(occ.get("title"))
        add_text(occ.get("dataIcon"))
        host = occ.get("hostText") or ""
        if len(host) <= 24:
            add_text(host)
        href = occ.get("hostHref") or ""
        if href and not href.startswith("http"):
            href = re.sub(r"\.(html?|php|aspx?|jsp)(\?|#|$)", r"\2", href)
            for w in re.split(r"[/.?=#&-]+", href):
                if w.isalpha() and len(w) >= 3 and w.lower() not in ("index", "www"):
                    add_text(w)
    cls = (icon.get("classes") or "") + " " + " ".join((o.get("classes") or "") + " " + (o.get("hostClasses") or "") for o in occs[:2])
    for c in cls.split():
        c = c.lower()
        m = re.match(r"^(fa|fas|far|fab|fal|fad|bi|ri|mdi|ti|la|ph|lucide|feather|icon|i|uil|lni)-(.+)$", c)
        if m:
            name = m.group(2)
            name = re.sub(r"-(line|fill|outline|solid|o|alt|bold|light|thin|duotone)$", "", name)
            add(FA_ALIAS.get(name, name))
        elif "icon" in c and c not in STOP:
            parts = [p for p in c.replace("icon", " ").split("-") if p and p not in STOP]
            for p in parts:
                add(p)
    if icon.get("ligature"):
        add(icon["ligature"].replace("_", "-"))
    if icon.get("alt"):
        add_text(icon["alt"])
    if icon.get("src"):
        base = icon["src"].rsplit("/", 1)[-1].split(".")[0]
        for w in re.split(r"[-_]+", base):
            if w.isalpha() and len(w) >= 3:
                add(w)
    return kws[:6]


def iconify_search(query: str, prefixes: list[str], timeout: float, limit: int = 12) -> list[str]:
    params = {"query": query, "limit": str(limit), "prefixes": ",".join(prefixes)}
    req = Request(f"{ICONIFY}?{urlencode(params)}", headers={"User-Agent": "website-clone-visual/1.0"})
    with urlopen(req, timeout=timeout) as resp:  # noqa: S310
        data = json.loads(resp.read().decode("utf-8"))
    return data.get("icons", [])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("capture", help="capture 目录（读取所有 <page>/icons.json）或单个 icons.json")
    ap.add_argument("-o", "--out")
    ap.add_argument("--libraries", default="lucide,heroicons,tabler,ph", help="Iconify 前缀，逗号分隔（lucide, heroicons, tabler, ph=Phosphor, mdi, ri, bi, fa6-solid…）")
    ap.add_argument("--offline", action="store_true", help="不访问网络，只输出关键词")
    ap.add_argument("--timeout", type=float, default=8)
    args = ap.parse_args()

    rep = Report()
    root = Path(args.capture)
    files = [root] if root.is_file() else sorted(root.glob("*/icons.json")) or ([root / "icons.json"] if (root / "icons.json").exists() else [])
    if not files:
        rep.error(str(root), "没找到 icons.json")
        rep.emit(False, "map_icons")
        return 0
    out_path = Path(args.out) if args.out else (root.parent if root.is_file() else root) / "icons-map.json"
    prefixes = [p.strip() for p in args.libraries.split(",") if p.strip()]

    icons: dict[str, dict] = {}
    for f in files:
        data = read_json(f)
        page = f.parent.name
        for kind in ("inline", "fonts", "sprites", "images"):
            for e in data.get(kind, []):
                x = icons.setdefault(e["id"], {**e, "pages": []})
                x["pages"].append(page)
                if e.get("file") and "fileRel" not in x:
                    x["fileRel"] = f"{page}/{e['file']}"
    rep.info("icons", f"{len(icons)} 个唯一图标，来自 {len(files)} 个页面")

    online = not args.offline
    cache: dict[str, list[str]] = {}
    results = []
    for icon in icons.values():
        kws = keywords_for(icon)
        cands: dict[str, list[str]] = {p: [] for p in prefixes}
        all_cls = " ".join([icon.get("classes") or ""] + [(o.get("classes") or "") + " " + (o.get("hostClasses") or "") for o in (icon.get("occurrences") or [])[:2]]).lower()
        is_logo = "logo" in all_cls or "brand" in all_cls
        if is_logo:  # Logo 不映射到图标库：原样内联或由用户替换
            results.append(
                {
                    "id": icon["id"],
                    "kind": icon.get("kind"),
                    "pages": sorted(set(icon["pages"])),
                    "file": icon.get("fileRel"),
                    "count": icon.get("count", 1),
                    "sizes": sorted(set(icon.get("sizes", []))),
                    "strokeBased": icon.get("strokeBased"),
                    "classes": icon.get("classes"),
                    "semantic": (icon.get("occurrences") or [{}])[0],
                    "keywords": ["logo"],
                    "candidates": {},
                    "recommended": None,
                    "confidence": "n/a",
                    "needsReview": True,
                    "note": "Logo / 品牌标识：不映射图标库，内联 icons/*.svg 或由用户提供替代",
                }
            )
            continue
        if online and kws:
            for kw in kws[:3]:
                if kw in cache:
                    found = cache[kw]
                else:
                    try:
                        found = iconify_search(kw, prefixes, args.timeout)
                    except Exception as e:  # noqa: BLE001
                        rep.warn("iconify", f"搜索失败（{type(e).__name__}），转离线模式")
                        online = False
                        found = []
                    cache[kw] = found
                for name in found:
                    pfx, _, nm = name.partition(":")
                    if pfx in cands and nm not in cands[pfx] and len(cands[pfx]) < 6:
                        cands[pfx].append(nm)
        stroke = icon.get("strokeBased", True) if icon.get("kind") == "inline-svg" else True
        order = ["lucide", "tabler", "heroicons", "ph"] if stroke else ["heroicons", "ph", "tabler", "lucide"]
        recommended = None
        for p in order:
            if cands.get(p):
                recommended = f"{p}:{cands[p][0]}"
                break
        confidence = (
            "high" if recommended and (icon.get("ariaLabel") or (icon.get("occurrences") or [{}])[0].get("ariaLabel") or icon.get("kind") == "icon-font") else ("medium" if recommended else "none")
        )
        results.append(
            {
                "id": icon["id"],
                "kind": icon.get("kind"),
                "pages": sorted(set(icon["pages"])),
                "file": icon.get("fileRel"),
                "count": icon.get("count", 1),
                "sizes": sorted(set(icon.get("sizes", []))),
                "strokeBased": icon.get("strokeBased"),
                "classes": icon.get("classes"),
                "semantic": (icon.get("occurrences") or [{}])[0],
                "keywords": kws,
                "candidates": cands,
                "recommended": recommended,
                "confidence": confidence,
                "needsReview": confidence != "high" or not kws,
            }
        )
    write_json(out_path, {"generatedAt": __import__("time").strftime("%Y-%m-%dT%H:%M:%S%z"), "libraries": prefixes, "online": online, "icons": results})
    mapped = sum(1 for r in results if r["recommended"])
    rep.info("map", f"{mapped}/{len(results)} 个有候选，{sum(1 for r in results if r['needsReview'])} 个需人工确认 → {out_path}")
    if not online:
        rep.info("offline", "未联网：candidates 为空，请对着 icons/*.svg 与 screenshots/sections/ 按 keywords 在图标库里挑选")
    rep.info("next", "把映射表交用户确认后再写图标组件；重跑 analyze_capture.py 让蓝图带上建议")
    rep.emit(False, "map_icons")
    return 0


if __name__ == "__main__":
    sys.exit(main())
