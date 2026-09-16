#!/usr/bin/env python3
"""把 features/ 采集结果提炼成 features.json（功能点 / 实体 / 角色 / 流程 / admin 反推 / API 清单），仅标准库。

  python3 analyze_features.py features/ [-o features/features.json] [--md features/features-summary.md] [--site-type ecommerce|content|saas|community|auto]

核心纪律：每一条都带 `来源`（页面 + 元素 / 请求）和 `依据`（实采 / 推断）。实采 = 页面上或网络里直接看到；推断 = 由实采内容按规则推出。
后续三份文档（PRD / 前端 IA / admin IA）由模型按 assets/templates/ 填充，本文件是唯一数据来源。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import Report, now_iso, read_json, write_json  # noqa: E402

REAL, INFER = "实采", "推断"

# 功能分类法（与 references/feature-taxonomy.md 一致）
MODULES = ["账户与认证", "内容浏览", "搜索与筛选", "交易与支付", "社交与互动", "通知与消息", "个人中心", "国际化与本地化", "SEO 与营销", "客服与帮助", "内容管理", "系统与基础"]

# 表单意图识别：action / name / heading / submit 文案 → (模块, 功能名, 优先级)
FORM_INTENTS = [
    (r"(login|signin|sign-in|登录)", ("账户与认证", "登录", "Must")),
    (r"(register|signup|sign-up|注册|创建账户)", ("账户与认证", "注册", "Must")),
    (r"(forgot|reset|password|找回|重置密码)", ("账户与认证", "找回 / 重置密码", "Should")),
    (r"(subscribe|newsletter|订阅)", ("SEO 与营销", "邮件订阅", "Could")),
    (r"(contact|feedback|留言|联系|反馈)", ("客服与帮助", "联系 / 留言表单", "Should")),
    (r"(comment|review|评论|评价)", ("社交与互动", "发表评论 / 评价", "Should")),
    (r"(order|checkout|结算|下单|订单)", ("交易与支付", "结算下单", "Must")),
    (r"(search|搜索)", ("搜索与筛选", "站内搜索", "Must")),
    (r"(profile|account|settings|资料|设置)", ("个人中心", "资料与设置", "Should")),
    (r"(upload|发布|投稿|post|create)", ("内容管理", "用户发布内容", "Should")),
    (r"(coupon|promo|优惠)", ("交易与支付", "优惠码", "Could")),
]
FIELD_ENTITY = {  # 表单字段名 → (实体, 属性名)
    r"^(email|mail|邮箱)$": ("User", "email"),
    r"^(password|passwd|pwd)$": ("User", "password"),
    r"^(confirm|password2|confirm_password)$": None,
    r"^(name|username|nickname|姓名|用户名)$": ("User", "name"),
    r"^(phone|mobile|tel|手机号?)$": ("User", "phone"),
    r"^(remember|agree|terms)$": None,
    r"^(avatar)$": ("User", "avatar"),
    r"^(receiver|consignee|收货人)$": ("Address", "receiver"),
    r"^(region|province|city|state|省|市)$": ("Address", "region"),
    r"^(address|street|详细地址)$": ("Address", "address"),
    r"^(postcode|zip|zipcode|邮编)$": ("Address", "postcode"),
    r"^(shipping|delivery|配送)$": ("Order", "shippingMethod"),
    r"^(payment|pay_method|支付)$": ("Order", "paymentMethod"),
    r"^(coupon|promo|优惠码)$": ("Order", "couponCode"),
    r"^(note|remark|备注)$": ("Order", "note"),
    r"^(rating|score|评分)$": ("Review", "rating"),
    r"^(body|content|comment|message|text|内容|留言)$": ("Review", "body"),
    r"^(title|subject|标题)$": ("Post", "title"),
    r"^(q|query|keyword|search|s)$": None,
}
ADMIN_FIXED = [
    ("仪表盘", "核心指标（订单 / 用户 / 内容增量）、待处理事项", "任何站点"),
    ("角色与权限", "管理员账号、角色（超级管理员 / 运营 / 客服 / 内容编辑）、权限矩阵、操作日志", "任何站点"),
    ("站点设置", "基本信息、SEO 默认值、导航与页脚配置、多语言 / 货币开关", "任何站点"),
    ("Banner / 推荐位", "首页 hero、精选位、公告的内容与排期", "有首页精选 / Banner 时"),
    ("日志审计", "登录日志、敏感操作日志、导出", "任何站点"),
]


def load(features_dir: Path) -> tuple[list[dict], dict, dict]:
    site_map = read_json(features_dir / "site-map.json") if (features_dir / "site-map.json").exists() else {"pages": []}
    network = read_json(features_dir / "network.json") if (features_dir / "network.json").exists() else {"entries": []}
    pages = []
    for d in sorted(p for p in features_dir.iterdir() if p.is_dir() and (p / "page.json").exists()):
        pg = read_json(d / "page.json")
        pg["_pageId"] = d.name
        pg["_probes"] = read_json(d / "probes.json") if (d / "probes.json").exists() else {}
        meta = next((m for m in site_map.get("pages", []) if m.get("pageId") == d.name), {})
        pg["_type"] = meta.get("type") or pg.get("pageType")
        pg["_admin"] = meta.get("type") == "admin"
        pages.append(pg)
    # 首页 / 列表 / 详情优先，让功能点的第一条来源落在最有代表性的页面上
    order = {"landing": 0, "list": 1, "detail": 2, "checkout": 3, "auth": 4, "account": 5, "search": 6, "form": 7, "content": 8, "legal": 9, "admin": 10}
    pages.sort(key=lambda p: (order.get(p["_type"], 20), p["_pageId"]))
    return pages, site_map, network


def src(page: dict, what: str) -> dict:
    return {"page": page["_pageId"], "url": page.get("url"), "evidence": what}


def guess_site_type(pages: list[dict], network: dict) -> str:
    txt = " ".join((p.get("url", "") + " " + " ".join(h["text"] for h in p.get("headings", [])) + " " + " ".join(b["text"] for b in p.get("buttons", []))) for p in pages).lower()
    inter = Counter(k for p in pages for k, v in p.get("interactions", {}).items() if v)
    if inter.get("cart") or re.search(r"(购物车|结算|下单|cart|checkout|price|¥|\$)", txt):
        return "ecommerce"
    if re.search(r"(pricing|订阅|plan|定价|dashboard|workspace|api key)", txt):
        return "saas"
    if inter.get("comments") and re.search(r"(帖子|话题|讨论|forum|thread|community|问答)", txt):
        return "community"
    if re.search(r"(blog|news|article|文章|新闻|博客|docs|文档)", txt):
        return "content"
    return "content"


def analyze(pages: list[dict], site_map: dict, network: dict, site_type: str, rep: Report) -> dict:
    features: list[dict] = []
    fid = [0]

    def add(module: str, name: str, desc: str, source: dict, basis: str = REAL, priority: str = "Should", roles=None, tags=None):
        for f in features:
            if f["module"] == module and f["name"] == name:
                if source not in f["sources"]:
                    f["sources"].append(source)
                return f
        fid[0] += 1
        f = {"id": f"F{fid[0]:03d}", "module": module, "name": name, "description": desc, "priority": priority, "basis": basis, "roles": roles or ["访客"], "sources": [source], "tags": tags or []}
        features.append(f)
        return f

    entities: dict[str, dict] = {}

    def ent(name: str) -> dict:
        return entities.setdefault(name, {"name": name, "attributes": {}, "sources": [], "basis": INFER, "relations": []})

    def attr(entity: str, a: str, source: dict, basis: str = REAL, typ: str | None = None):
        e = ent(entity)
        if a not in e["attributes"]:
            e["attributes"][a] = {"type": typ, "basis": basis, "sources": []}
        if source not in e["attributes"][a]["sources"]:
            e["attributes"][a]["sources"].append(source)
        if basis == REAL:
            e["basis"] = REAL
        if source not in e["sources"]:
            e["sources"].append(source)

    types = Counter(p["_type"] for p in pages)
    roles_seen: dict[str, dict] = {"访客": {"name": "访客", "basis": REAL, "sources": [{"evidence": "所有未登录可访问页面"}], "can": []}}

    # ---- 页面级 ----
    for p in pages:
        t = p["_type"]
        if t == "landing":
            add("内容浏览", "首页 / 落地页", "品牌介绍、精选内容入口、CTA", src(p, f"h1「{p.get('h1')}」"), REAL, "Must")
        if t == "list":
            add("内容浏览", "列表页", f"{p.get('h1') or p.get('title')}：卡片 / 列表展示，含分页或加载更多", src(p, f"lists {len(p.get('lists', []))} 个"), REAL, "Must")
        if t == "detail":
            add("内容浏览", "详情页", f"{p.get('h1') or p.get('title')}：单个实体的完整信息", src(p, f"h1「{p.get('h1')}」"), REAL, "Must")
        if t == "legal":
            add("客服与帮助", "帮助 / 政策 / 关于页面", "、".join(h["text"] for h in p.get("headings", [])[:6]), src(p, "headings"), REAL, "Should")
        if p.get("breadcrumb"):
            add("内容浏览", "面包屑导航", " / ".join(p["breadcrumb"][:4]), src(p, "breadcrumb"), REAL, "Should")
        if p.get("loginWall") or p.get("redirectedToLogin"):
            add("账户与认证", "登录墙", f"{p.get('url')} 需登录后访问", src(p, "loginWall / 302→login"), REAL, "Must", ["注册用户"])
        # 导航
        nav = p.get("navigation", {})
        if nav.get("main") and t == "landing":
            add("系统与基础", "全局导航（Header）", "、".join(dict.fromkeys(x["text"] for x in nav["main"] if x["text"])), src(p, "header nav"), REAL, "Must")
        if nav.get("footerGroups") and t == "landing":
            add(
                "系统与基础",
                "页脚链接分组",
                "；".join(f"{g.get('heading') or '?'}: {', '.join(lk['text'] for lk in g['links'][:5])}" for g in nav["footerGroups"][:5]),
                src(p, "footer"),
                REAL,
                "Should",
            )
        # 表单
        for f in p.get("forms", []):
            key = " ".join(str(x) for x in [f.get("action"), f.get("name"), f.get("id"), f.get("heading"), f.get("submitText")] if x).lower()
            intent = next((v for k, v in FORM_INTENTS if re.search(k, key)), None)
            fields_desc = "、".join(f"{x.get('label') or x.get('name') or x['type']}{'*' if x.get('required') else ''}" for x in f.get("fields", []))
            if intent:
                module, name, pri = intent
                feat = add(
                    module,
                    name,
                    f"字段：{fields_desc}；提交 → {f.get('method')} {urlparse(f.get('action') or '').path or '(JS)'}",
                    src(p, f"form[action={f.get('action')}] 「{f.get('submitText')}」"),
                    REAL,
                    pri,
                )
                if f.get("hasCaptcha"):
                    feat["tags"].append("验证码")
                if f.get("hasFileUpload"):
                    feat["tags"].append("文件上传")
            else:
                add(
                    "内容管理" if f.get("hasFileUpload") else "系统与基础",
                    f"表单：{f.get('heading') or f.get('submitText') or f.get('name') or '未命名'}",
                    f"字段：{fields_desc}",
                    src(p, f"form {f.get('path')}"),
                    REAL,
                    "Could",
                )
            # 字段 → 实体属性
            for x in f.get("fields", []):
                nm = (x.get("name") or "").lower()
                for pat, target in FIELD_ENTITY.items():
                    if re.match(pat, nm):
                        if target:
                            attr(target[0], target[1], src(p, f"form field {nm}"), REAL, x.get("type"))
                        break
            if f.get("hasPassword"):
                roles_seen.setdefault("注册用户", {"name": "注册用户", "basis": REAL, "sources": [], "can": []})["sources"].append(src(p, "密码表单"))
        # 控件
        c = p.get("controls", {})
        if c.get("searches"):
            add(
                "搜索与筛选",
                "站内搜索",
                f"占位「{c['searches'][0].get('placeholder')}」" + ("，提交到 " + c["searches"][0]["formAction"] if c["searches"][0].get("formAction") else "，前端即时过滤 / JS 触发"),
                src(p, "input[type=search]"),
                REAL,
                "Must",
            )
        for fg in c.get("filters", []):
            add(
                "搜索与筛选",
                f"筛选：{fg.get('label') or fg.get('name')}",
                "、".join(str(o.get("label") or o.get("value")) for o in fg.get("options", [])[:8]) + ("…" if len(fg.get("options", [])) > 8 else ""),
                src(p, f"{fg['type']}[name={fg.get('name')}]"),
                REAL,
                "Should",
            )
        for r in c.get("ranges", []):
            add("搜索与筛选", f"范围筛选：{r.get('label') or r.get('name')}", f"{r.get('min')}–{r.get('max')} step {r.get('step')}", src(p, "input[type=range]"), REAL, "Could")
        for s in c.get("sorts", []):
            if s.get("isSort"):
                add("搜索与筛选", "排序", "、".join(s.get("options", [])), src(p, "select 排序"), REAL, "Should")
        if c.get("paginations"):
            add(
                "内容浏览",
                "分页",
                ("URL 参数分页" if c["paginations"][0].get("usesQuery") else "前端分页 / JS") + f"：{' '.join(c['paginations'][0].get('items', [])[:8])}",
                src(p, "pagination"),
                REAL,
                "Should",
            )
        if c.get("loadMore"):
            add("内容浏览", "加载更多 / 无限滚动", c["loadMore"][0], src(p, "button 加载更多"), REAL, "Should")
        for tb in c.get("tabs", []):
            add("内容浏览", f"Tab 切换：{' / '.join(tb.get('items', [])[:5])}", f"{p.get('h1') or t} 页内分区", src(p, "tablist"), REAL, "Should")
        if c.get("accordions"):
            add("内容浏览", "折叠 / 展开区块", f"{c['accordions']} 处", src(p, "details / aria-expanded"), REAL, "Could")
        if c.get("modals"):
            add("系统与基础", "弹窗 / 抽屉", f"{c['modals']} 处", src(p, "dialog / .modal"), REAL, "Could")
        # 互动
        it = p.get("interactions", {})
        if it.get("cart"):
            add("交易与支付", "购物车", f"购物车入口{'，角标 ' + str(it.get('cartBadge')) if it.get('cartBadge') is not None else ''}", src(p, "cart"), REAL, "Must", ["访客", "注册用户"])
            attr("CartItem", "productId", src(p, "cart"), INFER)
            attr("CartItem", "quantity", src(p, "cart"), INFER, "int")
        if it.get("wishlist"):
            add("社交与互动", "收藏 / 心愿单", "收藏单个内容项", src(p, "wishlist"), REAL, "Should", ["注册用户"])
            attr("Wishlist", "productId", src(p, "wishlist"), INFER)
        if it.get("like"):
            add("社交与互动", "点赞", "", src(p, "like"), REAL, "Could", ["注册用户"])
        if it.get("share"):
            add("社交与互动", "分享", "", src(p, "share"), REAL, "Could")
        if it.get("comments"):
            add("社交与互动", "评论 / 评价列表", "详情页展示评论", src(p, "comments / reviews"), REAL, "Should")
        if it.get("rating"):
            add("社交与互动", "评分展示", "星级 / 分值", src(p, "rating"), REAL, "Should")
            attr("Review", "rating", src(p, "rating"), REAL, "number")
        if it.get("follow"):
            add("社交与互动", "关注", "", src(p, "follow"), REAL, "Could", ["注册用户"])
        if it.get("upload"):
            add("内容管理", "文件上传", "", src(p, "input[type=file]"), REAL, "Should", ["注册用户"])
        if it.get("download"):
            add("内容浏览", "文件下载", "", src(p, "a[download]"), REAL, "Could")
        if it.get("notifications"):
            add("通知与消息", "站内通知", "", src(p, "notification"), REAL, "Should", ["注册用户"])
        if it.get("chatWidget"):
            add("客服与帮助", "在线客服", "", src(p, "chat widget"), REAL, "Should")
        if it.get("newsletter") and not any(f["name"] == "邮件订阅" for f in features):
            add("SEO 与营销", "邮件订阅", "", src(p, "email input"), REAL, "Could")
        if it.get("map"):
            add("客服与帮助", "地图 / 门店位置", "", src(p, "map"), REAL, "Could")
        if it.get("video"):
            add("内容浏览", "视频播放", "", src(p, "video / iframe"), REAL, "Could")
        if it.get("compare"):
            add("搜索与筛选", "对比", "", src(p, "compare"), REAL, "Could")
        if it.get("coupon"):
            add("交易与支付", "优惠码", "", src(p, "coupon input"), REAL, "Could")
        # 账户 / 角色 / i18n
        au = p.get("auth", {})
        if au.get("links"):
            add("账户与认证", "登录 / 注册入口", "、".join(dict.fromkeys(lk["text"] for lk in au["links"])), src(p, "auth links"), REAL, "Must")
        if au.get("avatar"):
            add("个人中心", "头像 / 账户菜单", "", src(p, "avatar"), REAL, "Should", ["注册用户"])
        for hint in au.get("roleHints", []):
            if re.search(r"(会员|vip|premium|pro|企业)", hint):
                roles_seen.setdefault("付费用户 / 会员", {"name": "付费用户 / 会员", "basis": INFER, "sources": [], "can": []})["sources"].append(src(p, f"文案「{hint}」"))
            if re.search(r"(商家|卖家|店铺|供应商|seller|merchant|vendor)", hint):
                roles_seen.setdefault("商家", {"name": "商家", "basis": INFER, "sources": [], "can": []})["sources"].append(src(p, f"文案「{hint}」"))
            if re.search(r"(管理员|admin|后台|管理中心|moderator)", hint):
                roles_seen.setdefault("管理员", {"name": "管理员", "basis": INFER, "sources": [], "can": []})["sources"].append(src(p, f"文案「{hint}」"))
        i18n = p.get("i18n", {})
        if i18n.get("langSwitch"):
            add("国际化与本地化", "多语言切换", "、".join(dict.fromkeys(i18n["langSwitch"]))[:60], src(p, "lang switch"), REAL, "Should")
        if len(i18n.get("currencies", [])) > 1:
            add("国际化与本地化", "多货币", "、".join(i18n["currencies"]), src(p, "currency symbols"), REAL, "Could")
        for tp in p.get("thirdParty", []):
            names = {
                "payment": ("交易与支付", "第三方支付", "Must"),
                "analytics": ("SEO 与营销", "数据统计", "Should"),
                "ads": ("SEO 与营销", "广告投放", "Could"),
                "chat": ("客服与帮助", "在线客服（第三方）", "Should"),
                "maps": ("客服与帮助", "地图（第三方）", "Could"),
                "auth": ("账户与认证", "第三方登录", "Should"),
                "video": ("内容浏览", "视频（第三方）", "Could"),
                "social": ("社交与互动", "社交媒体链接", "Could"),
                "search": ("搜索与筛选", "托管搜索服务", "Should"),
                "forms": ("客服与帮助", "第三方表单", "Could"),
                "captcha": ("账户与认证", "验证码", "Should"),
                "cdn-ui": None,
            }
            hit = names.get(tp["category"])
            if hit:
                add(hit[0], hit[1], "、".join(tp["evidence"]), src(p, f"script / iframe {tp['category']}"), REAL, hit[2])
        for b in p.get("buttons", []):
            if re.search(r"(微信|apple|google|github|facebook|wechat|qq)登录|使用 .* 登录|sign in with", b["text"], re.I):
                add("账户与认证", "第三方登录", b["text"], src(p, f"button「{b['text']}」"), REAL, "Should")
        # 列表 → 实体
        for lst in p.get("lists", []):
            if lst["itemCount"] < 3 or not lst.get("fields"):
                continue
            kinds = Counter(f["kind"] for f in lst["fields"])
            ename = "Product" if lst.get("itemHasPrice") else ("Review" if lst.get("itemHasRating") and not lst.get("itemHasImage") else ("Article" if lst.get("itemHasDate") else "Item"))
            attr(ename, "title", src(p, f"list {lst['path']} title"), REAL, "string")
            if lst.get("itemHasImage"):
                attr(ename, "image", src(p, f"list {lst['path']} img"), REAL, "url")
            if lst.get("itemHasPrice"):
                attr(ename, "price", src(p, f"list {lst['path']} price"), REAL, "money")
            if lst.get("itemHasRating"):
                attr(ename, "rating", src(p, f"list {lst['path']} rating"), REAL, "number")
            if lst.get("itemHasDate"):
                attr(ename, "publishedAt", src(p, f"list {lst['path']} date"), REAL, "datetime")
            if kinds.get("tag"):
                attr(ename, "category / tag", src(p, f"list {lst['path']} tag"), REAL, "string")
            if lst.get("itemHasLink"):
                attr(ename, "id / slug", src(p, f"list item link {lst.get('itemLinkSample')}"), INFER, "id")
        # JSON-LD
        for ld in p.get("jsonLd", []):
            typ = ld.get("type")
            if isinstance(typ, list):
                typ = typ[0]
            if typ and typ not in ("WebSite", "WebPage", "BreadcrumbList", "Organization"):
                for k in ld.get("keys", []):
                    attr(str(typ), k, src(p, "JSON-LD"), REAL)
        # 详情页实体线索
        if t == "detail":
            eh = p.get("entityHints", {})
            ename = "Product" if eh.get("prices") else ("Article" if eh.get("dates") else "Item")
            attr(ename, "title", src(p, f"h1「{p.get('h1')}」"), REAL, "string")
            attr(ename, "description", src(p, "详情正文"), REAL, "text")
            if eh.get("prices"):
                attr(ename, "price", src(p, f"价格 {eh['prices'][:2]}"), REAL, "money")
            if eh.get("ratings"):
                attr(ename, "rating", src(p, "评分"), REAL, "number")
            for tb in c.get("tabs", []):
                for item in tb.get("items", []):
                    attr(ename, f"section: {item}", src(p, "tab"), REAL, "section")
            for tbl in p.get("tables", []):
                for rh in tbl.get("rowHeaders", [])[:12]:
                    attr(ename, f"spec: {rh}", src(p, "规格表"), REAL, "string")
            for b in p.get("buttons", []):
                if b["kind"] == "write" and re.search(r"(购物车|cart|购买|buy)", b["text"], re.I):
                    add("交易与支付", "加入购物车 / 立即购买", b["text"], src(p, f"button「{b['text']}」"), REAL, "Must", ["访客", "注册用户"])
                    attr("CartItem", "productId", src(p, "加入购物车"), REAL)
                    attr("CartItem", "quantity", src(p, "数量控件"), REAL if any(x["text"] in ("增加", "减少", "+", "−", "-") for x in p.get("buttons", [])) else INFER, "int")
                    attr("CartItem", "variant（颜色 / 规格）", src(p, "色板 / 规格按钮"), INFER if not any(x["kind"] == "unknown" and x["tag"] == "button" for x in p.get("buttons", [])) else REAL)
        if t == "checkout":
            add("交易与支付", "购物车管理", "查看 / 移除商品、金额汇总", src(p, "cart items / summary"), REAL, "Must")
            attr("Order", "items", src(p, "购物车列表"), REAL, "CartItem[]")
            attr("Order", "subtotal / shipping / total", src(p, "订单摘要"), REAL, "money")
            attr("Order", "status", src(p, "下单流程"), INFER, "enum")
            attr("Order", "userId", src(p, "结算需账户"), INFER)

    # ---- 网络 → API 清单 ----
    api: dict[str, dict] = {}
    for e in network.get("entries", []):
        if e.get("trigger") == "self-test":
            continue
        is_api = e.get("resourceType") in ("xhr", "fetch") or re.search(r"\.json(\?|$)|/api/|/graphql|/v\d+/", e.get("url", ""))
        if not is_api:
            continue
        key = f"{e['method']} {e['path']}"
        a = api.setdefault(
            key,
            {
                "method": e["method"],
                "path": e["path"],
                "host": e.get("host"),
                "count": 0,
                "pages": [],
                "triggers": [],
                "queryKeys": [],
                "bodyKeys": e.get("bodyKeys"),
                "status": e.get("status"),
                "blocked": bool(e.get("blocked")),
                "responseShape": e.get("responseShape"),
                "responseSample": e.get("responseSample"),
                "sameSite": e.get("sameSite"),
            },
        )
        a["count"] += 1
        if e.get("page") and e["page"] not in a["pages"]:
            a["pages"].append(e["page"])
        if e.get("trigger") not in a["triggers"]:
            a["triggers"].append(e.get("trigger"))
        for k in e.get("queryKeys", []):
            if k not in a["queryKeys"]:
                a["queryKeys"].append(k)
        if e.get("blocked"):
            a["blocked"] = True
        # 路径名词 → 实体
        for seg in reversed([s for s in e["path"].split("/") if s and not re.match(r"^(api|v\d+|graphql)$", s)]):
            noun = re.sub(r"\.(json|php|aspx?)$", "", seg)
            if re.match(r"^[a-zA-Z_-]{3,}$", noun) and not re.match(r"^\d+$", noun):
                ename = noun[:-1].capitalize() if noun.endswith("s") and not noun.endswith("ss") else noun.capitalize()
                ename = ename.replace("-", " ").title().replace(" ", "")
                shape = e.get("responseShape")
                item = shape.get("item") if isinstance(shape, dict) and "__array__" in shape else shape
                if isinstance(item, dict):
                    for k, v in item.items():
                        attr(ename, k, {"page": e.get("page"), "evidence": f"API {key} 响应字段", "type": v if isinstance(v, str) else "object"}, REAL, v if isinstance(v, str) else "object")
                    ent(ename)["api"] = key
                elif e.get("bodyKeys"):
                    for k in e["bodyKeys"]:
                        attr(ename, k, {"page": e.get("page"), "evidence": f"API {key} 请求体字段（被拦截）"}, REAL)
                break

    # ---- 实体关系（规则） ----
    names = set(entities)
    rel = []
    if "Product" in names and "Review" in names:
        rel.append(("Product", "1..n", "Review", "商品有多条评价", INFER))
        attr("Review", "productId", {"evidence": "评价挂在商品详情页"}, INFER)
    if "User" in names and "Review" in names:
        rel.append(("User", "1..n", "Review", "用户发表评价", INFER))
        attr("Review", "userId / author", {"evidence": "评论有作者"}, INFER)
    if "User" in names and "Order" in names:
        rel.append(("User", "1..n", "Order", "用户下多个订单", INFER))
    if "Order" in names and "CartItem" in names:
        rel.append(("Order", "1..n", "CartItem", "订单包含多个商品行（OrderItem）", INFER))
    if "CartItem" in names and "Product" in names:
        rel.append(("CartItem", "n..1", "Product", "商品行指向商品", INFER))
    if "Wishlist" in names:
        rel.append(("User", "n..m", "Product", "心愿单（Wishlist 关联表）", INFER))
    if "User" in names and "Address" in names:
        rel.append(("User", "1..n", "Address", "用户有多个收货地址", INFER))
    if "Product" in names and any("category" in a for a in entities["Product"]["attributes"]):
        ent("Category")
        attr("Category", "name", {"evidence": "商品分类筛选 / 标签"}, REAL)
        rel.append(("Category", "1..n", "Product", "分类下多个商品", INFER))
    if "Article" in names:
        ent("Category") if "Category" not in names else None
        rel.append(("Category", "1..n", "Article", "栏目下多篇文章", INFER))
    for a, card, b, desc, basis in rel:
        ent(a)["relations"].append({"to": b, "cardinality": card, "description": desc, "basis": basis})
    for e in entities.values():
        if not e["sources"]:
            e["basis"] = INFER
    # 泛化占位实体 Item：已经有 Product / Article 且自身信息量很小时丢弃
    if "Item" in entities and (names & {"Product", "Article", "Post"}) and len(entities["Item"]["attributes"]) <= 2:
        del entities["Item"]
        names.discard("Item")

    # ---- 角色 ----
    if "Order" in names or any(f["module"] == "交易与支付" for f in features):
        roles_seen.setdefault("注册用户", {"name": "注册用户", "basis": INFER, "sources": [], "can": []})
    roles_seen.setdefault("管理员", {"name": "管理员", "basis": INFER, "sources": [{"evidence": "任何有内容 / 用户 / 订单的站点都需要后台管理者；未在前台实采到"}], "can": []})
    if any(p["_admin"] for p in pages):
        roles_seen["管理员"]["basis"] = REAL
        roles_seen["管理员"]["sources"] = [src(p, "后台页面实采") for p in pages if p["_admin"]]
    for f in features:
        for r in f["roles"]:
            if r in roles_seen and f["name"] not in roles_seen[r]["can"]:
                roles_seen[r]["can"].append(f["name"])

    # ---- 流程 ----
    flows = []
    has = lambda name: any(f["name"] == name for f in features)  # noqa: E731
    page_of = lambda t: next((p for p in pages if p["_type"] == t), None)  # noqa: E731

    def step(label, p, basis=REAL):
        return {"step": label, "page": p["_pageId"] if p else None, "url": p.get("url") if p else None, "basis": basis if p else INFER}

    if has("注册") or has("登录"):
        pa = page_of("auth")
        flows.append(
            {
                "name": "注册 / 登录",
                "actor": "访客 → 注册用户",
                "steps": [step("进入登录 / 注册页", pa), step("填写表单并提交（第三方登录可选）", pa), step("成功后返回来源页，Header 显示账户入口", page_of("landing"), INFER)],
                "basis": REAL if pa else INFER,
            }
        )
    if types.get("list") and types.get("detail"):
        flows.append(
            {
                "name": "浏览 → 筛选 → 详情",
                "actor": "访客",
                "steps": [step("首页进入列表", page_of("landing")), step("筛选 / 排序 / 搜索 / 分页", page_of("list")), step("打开详情", page_of("detail"))],
                "basis": REAL,
            }
        )
    if has("加入购物车 / 立即购买") or has("购物车"):
        flows.append(
            {
                "name": "加购 → 结算 → 下单 → 支付",
                "actor": "访客 / 注册用户",
                "steps": [
                    step("详情页选规格数量加购", page_of("detail")),
                    step("购物车确认商品与金额", page_of("checkout")),
                    step("填写收货 / 配送 / 支付 / 优惠码", page_of("checkout")),
                    step("提交订单 → 支付 → 订单状态流转（待支付 / 已支付 / 已发货 / 已完成）", None, INFER),
                ],
                "basis": REAL,
            }
        )
    if has("站内搜索"):
        flows.append(
            {
                "name": "搜索 → 结果 → 详情",
                "actor": "访客",
                "steps": [step("输入关键词", page_of("list") or page_of("landing")), step("结果列表（空态 / 加载态）", page_of("list")), step("打开详情", page_of("detail"))],
                "basis": REAL,
            }
        )
    if has("发表评论 / 评价"):
        flows.append(
            {
                "name": "发表评价",
                "actor": "注册用户",
                "steps": [step("详情页评价 Tab", page_of("detail")), step("填写评分与内容提交", page_of("detail")), step("审核后展示（是否需审核为推断）", None, INFER)],
                "basis": REAL,
            }
        )
    if has("邮件订阅"):
        flows.append({"name": "邮件订阅", "actor": "访客", "steps": [step("输入邮箱提交", page_of("landing")), step("确认邮件 / 成功提示", None, INFER)], "basis": REAL})
    if has("联系 / 留言表单"):
        flows.append({"name": "联系 / 留言", "actor": "访客", "steps": [step("填写联系表单", page_of("legal")), step("后台收到工单并回复", None, INFER)], "basis": REAL})
    if has("收藏 / 心愿单"):
        flows.append({"name": "收藏", "actor": "注册用户", "steps": [step("详情 / 列表点收藏", page_of("detail")), step("个人中心查看收藏列表", page_of("account"), INFER)], "basis": REAL})

    # ---- admin 反推 ----
    admin_modules = []
    admin_real = any(p["_admin"] for p in pages)
    STATUS = {
        "Product": ["草稿", "上架", "下架", "售罄"],
        "Article": ["草稿", "待审核", "已发布", "已下线"],
        "Post": ["草稿", "待审核", "已发布", "已隐藏"],
        "Review": ["待审核", "已通过", "已拒绝", "已隐藏"],
        "Order": ["待支付", "已支付", "已发货", "已完成", "已取消", "退款中", "已退款"],
        "User": ["正常", "禁用"],
        "Category": ["启用", "停用"],
    }
    for e in entities.values():
        if e["name"] in ("CartItem", "Wishlist", "Address"):
            continue
        fields = [a for a in e["attributes"] if not re.search(r"(password|passwd|pwd)", a, re.I)][:12]
        filters = [a for a in fields if re.search(r"(category|tag|status|type|rating|date|At|region|method)", a)]
        admin_modules.append(
            {
                "module": f"{e['name']} 管理",
                "entity": e["name"],
                "basis": REAL if admin_real else INFER,
                "list": {
                    "columns": fields[:8],
                    "filters": filters or ["关键词", "创建时间"],
                    "batch": ["批量删除"] + (["批量上下架"] if e["name"] in ("Product", "Article", "Post") else []) + (["批量审核"] if e["name"] in ("Review", "Post") else []),
                },
                "form": {"fields": fields, "validation": "必填项与前台表单一致；金额 / 数量为非负数"},
                "actions": ["新建", "编辑", "删除", "查看详情"] + (["导出"] if e["name"] in ("Order", "User") else []),
                "states": STATUS.get(e["name"], ["启用", "停用"]),
                "source": e["sources"][:2],
            }
        )
    if "User" not in names:
        admin_modules.append(
            {
                "module": "User 管理",
                "entity": "User",
                "basis": INFER,
                "list": {"columns": ["id", "name", "email", "phone", "注册时间", "状态"], "filters": ["关键词", "注册时间", "状态"], "batch": ["禁用", "导出"]},
                "form": {"fields": ["name", "email", "phone", "角色", "状态"], "validation": "邮箱 / 手机唯一"},
                "actions": ["查看", "编辑", "禁用", "重置密码"],
                "states": STATUS["User"],
                "source": [{"evidence": "站点有登录 / 注册 → 必有用户管理"}],
            }
        )
    if has("发表评论 / 评价") or has("评论 / 评价列表"):
        if not any(m["entity"] == "Review" for m in admin_modules):
            admin_modules.append(
                {
                    "module": "评论审核",
                    "entity": "Review",
                    "basis": INFER,
                    "list": {"columns": ["内容", "评分", "作者", "所属对象", "时间", "状态"], "filters": ["状态", "评分", "时间"], "batch": ["批量通过", "批量拒绝"]},
                    "form": {"fields": ["状态", "拒绝原因"], "validation": ""},
                    "actions": ["通过", "拒绝", "隐藏", "删除"],
                    "states": STATUS["Review"],
                    "source": [{"evidence": "前台有评论 / 评价"}],
                }
            )
    if has("联系 / 留言表单"):
        admin_modules.append(
            {
                "module": "留言 / 工单",
                "entity": "Message",
                "basis": INFER,
                "list": {"columns": ["姓名", "邮箱", "内容", "时间", "状态", "处理人"], "filters": ["状态", "时间"], "batch": ["标记已处理"]},
                "form": {"fields": ["回复内容"], "validation": ""},
                "actions": ["查看", "回复", "关闭"],
                "states": ["待处理", "处理中", "已关闭"],
                "source": [{"evidence": "前台联系表单"}],
            }
        )
    if has("邮件订阅"):
        admin_modules.append(
            {
                "module": "订阅者",
                "entity": "Subscriber",
                "basis": INFER,
                "list": {"columns": ["邮箱", "订阅时间", "状态", "来源页"], "filters": ["状态"], "batch": ["导出", "退订"]},
                "form": {"fields": []},
                "actions": ["导出", "退订"],
                "states": ["已订阅", "已退订"],
                "source": [{"evidence": "前台订阅表单"}],
            }
        )
    if has("优惠码"):
        admin_modules.append(
            {
                "module": "优惠券",
                "entity": "Coupon",
                "basis": INFER,
                "list": {"columns": ["码", "类型", "面额 / 折扣", "门槛", "有效期", "已用 / 总量", "状态"], "filters": ["状态", "有效期"], "batch": ["停用"]},
                "form": {"fields": ["码", "类型", "面额", "门槛", "有效期", "总量", "适用范围"], "validation": "码唯一"},
                "actions": ["新建", "编辑", "停用"],
                "states": ["未开始", "生效中", "已过期", "已停用"],
                "source": [{"evidence": "结算页优惠码输入"}],
            }
        )
    if "Order" in names:
        admin_modules.append(
            {
                "module": "配送与运费",
                "entity": "ShippingRule",
                "basis": INFER,
                "list": {"columns": ["名称", "计费方式", "免运费门槛", "区域", "状态"], "filters": ["状态"], "batch": []},
                "form": {"fields": ["名称", "计费方式", "门槛", "区域"], "validation": ""},
                "actions": ["新建", "编辑", "停用"],
                "states": ["启用", "停用"],
                "source": [{"evidence": "结算页配送方式与免运费提示"}],
            }
        )
    if any(f["name"] == "数据统计" for f in features) or "Order" in names:
        admin_modules.append(
            {
                "module": "报表",
                "entity": None,
                "basis": INFER,
                "list": {"columns": ["日期", "访问", "注册", "订单数", "GMV", "转化率"], "filters": ["时间范围", "渠道"], "batch": ["导出"]},
                "form": {"fields": []},
                "actions": ["导出"],
                "states": [],
                "source": [{"evidence": "有交易 / 统计脚本"}],
            }
        )
    for name, desc, when in ADMIN_FIXED:
        if name == "Banner / 推荐位" and not types.get("landing"):
            continue
        if name == "站点设置" and not (has("多语言切换") or has("多货币")):
            desc = desc.replace("、多语言 / 货币开关", "")
        admin_modules.append({"module": name, "entity": None, "basis": INFER, "description": desc, "when": when, "list": {}, "form": {}, "actions": [], "states": [], "source": [{"evidence": when}]})
    admin_roles = [
        {"role": "超级管理员", "scope": "全部模块 + 角色权限 + 站点设置", "basis": INFER},
        {"role": "运营", "scope": "内容 / 商品 / Banner / 优惠券 / 报表查看", "basis": INFER},
        {"role": "客服", "scope": "订单查看与备注、留言工单、用户查看", "basis": INFER},
    ] + ([{"role": "内容编辑", "scope": "文章 / 评论审核", "basis": INFER}] if "Article" in names or "Post" in names else [])

    # ---- 页面清单 ----
    page_list = [
        {
            "pageId": p["_pageId"],
            "url": p.get("url"),
            "type": p["_type"],
            "title": p.get("title"),
            "h1": p.get("h1"),
            "forms": len(p.get("forms", [])),
            "lists": len(p.get("lists", [])),
            "loginWall": bool(p.get("loginWall") or p.get("redirectedToLogin")),
            "admin": p["_admin"],
            "probes": [a["action"] for a in p["_probes"].get("actions", [])],
        }
        for p in pages
    ]

    features.sort(key=lambda f: (MODULES.index(f["module"]) if f["module"] in MODULES else 99, {"Must": 0, "Should": 1, "Could": 2, "Won't": 3}.get(f["priority"], 9)))
    return {
        "generatedAt": now_iso(),
        "origin": site_map.get("origin"),
        "siteType": site_type,
        "pages": page_list,
        "pageTypes": dict(types),
        "features": features,
        "entities": list(entities.values()),
        "roles": list(roles_seen.values()),
        "flows": flows,
        "api": sorted(api.values(), key=lambda a: (a["blocked"], a["method"], a["path"])),
        "admin": {"basis": REAL if admin_real else INFER, "roles": admin_roles, "modules": admin_modules},
        "assumptions": [
            "所有标「推断」的条目需用户确认；admin 模块在没有后台实采时完全由前台反推",
            "被拦截（blocked）的写请求只记录了方法 / 路径 / 请求体字段名，响应结构未知",
            "角色划分基于可见入口与文案，付费 / 商家等角色的真实权限边界需用户补充",
            "第三方服务按脚本域名识别，可能遗漏自建或代理的服务",
        ],
    }


def to_markdown(data: dict) -> str:
    md = [
        f"# 功能分析摘要 — {data.get('origin')}\n",
        f"站点类型：{data['siteType']}；页面 {len(data['pages'])} 个（{data['pageTypes']}）；功能点 {len(data['features'])}；实体 {len(data['entities'])}；角色 {len(data['roles'])}；流程 {len(data['flows'])}；API {len(data['api'])}\n",
        "## 功能点\n",
        "| ID | 模块 | 功能 | 优先级 | 依据 | 来源 |",
        "|---|---|---|---|---|---|",
    ]
    for f in data["features"]:
        s = f["sources"][0]
        md.append(f"| {f['id']} | {f['module']} | {f['name']} | {f['priority']} | {f['basis']} | `{s.get('page')}` {str(s.get('evidence'))[:50]} |")
    md += ["\n## 实体\n"]
    for e in data["entities"]:
        attrs = "、".join(f"{a}{'' if v['basis'] == REAL else '?'}" for a, v in list(e["attributes"].items())[:14])
        rels = "；".join(f"{r['cardinality']} {r['to']}" for r in e["relations"])
        md.append(f"- **{e['name']}**（{e['basis']}）：{attrs}" + (f"　关系：{rels}" if rels else "") + (f"　API：`{e['api']}`" if e.get("api") else ""))
    md += ["\n`?` 表示推断属性。\n", "## 角色\n"]
    for r in data["roles"]:
        md.append(f"- **{r['name']}**（{r['basis']}）：{'、'.join(r['can'][:8]) or '—'}")
    md += ["\n## 流程\n"]
    for fl in data["flows"]:
        md.append(f"- **{fl['name']}**（{fl['actor']}）：" + " → ".join(f"{s['step']}{'' if s['basis'] == REAL else '?'}" for s in fl["steps"]))
    md += ["\n## API\n", "| 方法 | 路径 | 触发 | 状态 | 拦截 | 响应形状 |", "|---|---|---|---|---|---|"]
    for a in data["api"]:
        md.append(
            f"| {a['method']} | `{a['path']}` | {'、'.join(str(t) for t in a['triggers'])} | {a.get('status')} | {'是' if a['blocked'] else ''} | `{json.dumps(a.get('responseShape'), ensure_ascii=False)[:60] if a.get('responseShape') else (a.get('bodyKeys') or '')}` |"
        )
    md += [f"\n## admin 反推（{data['admin']['basis']}）\n"]
    for m in data["admin"]["modules"]:
        md.append(
            f"- **{m['module']}**（{m['basis']}）" + (f"：列 {', '.join(m['list'].get('columns', [])[:6])}；状态 {' → '.join(m['states'])}" if m.get("list") else f"：{m.get('description', '')}")
        )
    md += ["\n## 假设\n"] + [f"- {a}" for a in data["assumptions"]]
    return "\n".join(md) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("features_dir")
    ap.add_argument("-o", "--out")
    ap.add_argument("--md", help="同时输出 Markdown 摘要")
    ap.add_argument("--site-type", default="auto", choices=["auto", "ecommerce", "content", "saas", "community"])
    args = ap.parse_args()

    rep = Report()
    fdir = Path(args.features_dir)
    if not fdir.exists():
        rep.error(str(fdir), "目录不存在")
        return rep.emit(False, "analyze_features")
    pages, site_map, network = load(fdir)
    if not pages:
        rep.error(str(fdir), "没有 <page>/page.json；先运行 crawl_features.py 或用内联浏览器注入 collect/features.js 后存为 page.json")
        return rep.emit(False, "analyze_features")
    site_type = args.site_type if args.site_type != "auto" else guess_site_type(pages, network)
    data = analyze(pages, site_map, network, site_type, rep)
    out = Path(args.out) if args.out else fdir / "features.json"
    write_json(out, data)
    md_path = Path(args.md) if args.md else fdir / "features-summary.md"
    md_path.write_text(to_markdown(data), encoding="utf-8")
    real = sum(1 for f in data["features"] if f["basis"] == REAL)
    rep.info(
        "features",
        f"{len(data['features'])} 个功能点（实采 {real}）、{len(data['entities'])} 个实体、{len(data['roles'])} 个角色、{len(data['flows'])} 条流程、{len(data['api'])} 个 API、admin 模块 {len(data['admin']['modules'])} → {out}",
    )
    rep.info("summary", f"→ {md_path}")
    if network.get("allowWrites"):
        rep.warn("safety", "本次采集开启了 --allow-writes")
    blocked = [a for a in data["api"] if a["blocked"]]
    if blocked:
        rep.info("blocked", f"{len(blocked)} 个写接口被拦截，只有请求体字段名：" + "、".join(f"{a['method']} {a['path']}" for a in blocked[:6]))
    rep.info("next", "按 assets/templates/ 填写 PRD.md、frontend-ia.md、admin-ia.md；每条保留「实采 / 推断」列")
    return rep.emit(False, "analyze_features")


if __name__ == "__main__":
    sys.exit(main())
