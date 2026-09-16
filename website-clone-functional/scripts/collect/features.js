/* collect/features.js — 页面功能特征提取（只读，不触发任何交互）。
   产出：页面类型猜测、导航结构、表单与字段、按钮 / CTA（标注读 / 写）、列表与表格及其字段、筛选 / 排序 / 搜索 / 分页 / Tab 控件、
   登录态与角色线索、国际化 / 货币、互动点（购物车 / 收藏 / 评论 / 分享…）、第三方服务、JSON-LD 结构化数据、价格 / 日期 / 评分等实体线索。
   自包含 IIFE；结果写到 window.__wc.features 并返回。与 website-clone-visual 的 collect/*.js 同一套约定。 */
(() => {
  const clean = (t) => (t || "").replace(/\s+/g, " ").trim();
  const visible = (el) => { const r = el.getBoundingClientRect(); const cs = getComputedStyle(el); return r.width > 0 && r.height > 0 && cs.display !== "none" && cs.visibility !== "hidden"; };
  const cssPath = (el) => {
    const parts = [];
    while (el && el.nodeType === 1 && el !== document.documentElement) {
      let part = el.tagName.toLowerCase();
      if (el.id && /^[A-Za-z][\w-]*$/.test(el.id)) { parts.unshift(`#${el.id}`); break; }
      const parent = el.parentElement;
      if (parent) { const same = Array.from(parent.children).filter((c) => c.tagName === el.tagName); if (same.length > 1) part += `:nth-of-type(${same.indexOf(el) + 1})`; }
      parts.unshift(part); el = parent;
    }
    return parts.join(" > ");
  };
  const region = (el) => (el.closest("header, [role=banner]") && "header") || (el.closest("footer, [role=contentinfo]") && "footer") || (el.closest("aside, [role=complementary]") && "aside") || (el.closest("nav, [role=navigation]") && "nav") || (el.closest("dialog, [role=dialog], .modal") && "modal") || "main";
  const abs = (u) => { try { return new URL(u, location.href).href; } catch (e) { return u; } };
  const labelOf = (input) => {
    if (input.id) { const l = document.querySelector(`label[for="${CSS.escape(input.id)}"]`); if (l) return clean(l.textContent); }
    const wrap = input.closest("label"); if (wrap) return clean(Array.from(wrap.childNodes).filter((n) => n.nodeType === 3).map((n) => n.textContent).join(" ")) || clean(wrap.textContent).slice(0, 40);
    const aria = input.getAttribute("aria-label"); if (aria) return aria;
    const labelled = input.getAttribute("aria-labelledby"); if (labelled) { const l = document.getElementById(labelled); if (l) return clean(l.textContent); }
    const prev = input.previousElementSibling; if (prev && /^(LABEL|SPAN|DIV|P)$/.test(prev.tagName) && clean(prev.textContent).length < 30) return clean(prev.textContent);
    return null;
  };

  const WRITE_RE = /(提交|保存|发布|发送|注册|创建|新建|添加|加入|下单|购买|结算|支付|付款|订阅|评论|评价|收藏|关注|点赞|删除|移除|取消|退款|申请|上传|确认|修改|更新|编辑|重置密码|绑定|签到|领取|兑换|投票|举报|submit|save|publish|send|register|sign ?up|create|add|buy|checkout|pay|subscribe|comment|review|like|follow|delete|remove|apply|upload|confirm|update|edit|claim|redeem|vote|report|post)/i;
  const READ_RE = /(登录|查看|了解|浏览|搜索|筛选|排序|展开|收起|更多|下一|上一|切换|返回|关闭|取消|详情|下载|分享|复制|打印|login|sign ?in|view|learn|browse|search|filter|sort|expand|collapse|more|next|prev|toggle|back|close|detail|download|share|copy|print)/i;

  // ---- 页面类型猜测 ----
  const path = location.pathname.toLowerCase() + location.search.toLowerCase();
  const text = clean(document.body.innerText || "").toLowerCase();
  const formCount = document.forms.length;
  const pwd = document.querySelector("input[type=password]");
  const guessType = () => {
    if (/(admin|manage|dashboard|console|backend|后台)/.test(path)) return "admin";
    if (pwd || /(login|signin|sign-in|register|signup|sign-up|auth|登录|注册)/.test(path)) return "auth";
    if (/(cart|checkout|order|pay|结算|购物车|订单|支付)/.test(path)) return "checkout";
    if (/(search|s\?q=|\?q=|keyword=|搜索)/.test(path)) return "search";
    if (/(account|profile|user|member|me\b|个人|会员)/.test(path)) return "account";
    if (/(privacy|terms|legal|policy|about|contact|faq|help|隐私|条款|关于|联系|帮助)/.test(path)) return "legal";
    if (/(\/p\/|\/product\/|\/item\/|\/detail|\/post\/|\/article\/|\/blog\/[^/]+$|id=|\/\d+$)/.test(path) && document.querySelector("h1")) return "detail";
    if (document.querySelectorAll("[class*=pagination], nav[aria-label*=分页], nav[aria-label*=pagination]").length || /(list|category|collection|products|shop|blog|news|archive|tag|列表|分类)/.test(path)) return "list";
    if (location.pathname === "/" || /^\/(index|home)(\.\w+)?$/.test(location.pathname)) return "landing";
    if (formCount >= 1 && text.length < 3000) return "form";
    return "content";
  };

  // ---- 导航 ----
  const navLink = (a) => ({ text: clean(a.getAttribute("aria-label") || a.textContent).slice(0, 60), href: abs(a.getAttribute("href")), active: /(^|\s)(active|current|selected)(\s|$)/.test(a.className) || a.getAttribute("aria-current") != null });
  const mainNav = Array.from(document.querySelectorAll("header a[href], [role=banner] a[href], nav:not(footer nav) a[href]")).filter((a) => !a.closest("footer") && visible(a)).map(navLink);
  const footerGroups = [];
  for (const col of Array.from(document.querySelectorAll("footer"))) {
    for (const group of Array.from(col.querySelectorAll("div, ul, section, nav"))) {
      const links = Array.from(group.querySelectorAll(":scope > a[href], :scope > li > a[href]"));
      if (links.length < 2) continue;
      const h = group.querySelector("h1,h2,h3,h4,h5,h6,strong,b") || group.previousElementSibling;
      footerGroups.push({ heading: h ? clean(h.textContent).slice(0, 40) : null, links: links.map(navLink) });
    }
  }
  const breadcrumb = Array.from(document.querySelectorAll("[aria-label*=面包屑], [aria-label*=breadcrumb], .breadcrumb, .breadcrumbs, nav ol")).slice(0, 1).flatMap((b) => Array.from(b.querySelectorAll("a, span, li")).filter((x) => !x.querySelector("a, span")).map((x) => clean(x.textContent)).filter((t) => t && t !== "/" && t !== ">"));
  const sideNav = Array.from(document.querySelectorAll("aside a[href], [role=complementary] a[href]")).filter(visible).map(navLink);

  // ---- 表单 ----
  const forms = Array.from(document.querySelectorAll("form")).map((f) => {
    const submit = f.querySelector("button[type=submit], input[type=submit], button:not([type])");
    const fields = Array.from(f.querySelectorAll("input, select, textarea")).filter((i) => !/^(hidden|submit|button|reset|image)$/.test(i.type)).map((i) => ({
      name: i.name || null, type: i.tagName === "SELECT" ? "select" : i.tagName === "TEXTAREA" ? "textarea" : i.type,
      label: labelOf(i), placeholder: i.placeholder || null, required: i.required, pattern: i.getAttribute("pattern"), minlength: i.getAttribute("minlength"), maxlength: i.getAttribute("maxlength"), min: i.getAttribute("min"), max: i.getAttribute("max"),
      autocomplete: i.getAttribute("autocomplete"), inputmode: i.getAttribute("inputmode"), value: /^(radio|checkbox)$/.test(i.type) ? i.value : undefined, checked: /^(radio|checkbox)$/.test(i.type) ? i.checked : undefined,
      options: i.tagName === "SELECT" ? Array.from(i.options).map((o) => clean(o.textContent)).slice(0, 30) : undefined,
    }));
    // radio / checkbox 同名合并
    const merged = [];
    for (const fl of fields) {
      if (/^(radio|checkbox)$/.test(fl.type) && fl.name) {
        const hit = merged.find((m) => m.name === fl.name && m.type === fl.type);
        if (hit) { hit.options.push({ value: fl.value, label: fl.label, checked: fl.checked }); continue; }
        merged.push({ ...fl, options: [{ value: fl.value, label: fl.label, checked: fl.checked }], label: undefined, value: undefined, checked: undefined });
      } else merged.push(fl);
    }
    const heading = f.closest("section, div, article, main")?.querySelector("h1, h2, h3, legend");
    const hidden = Array.from(f.querySelectorAll("input[type=hidden]")).map((h) => h.name).filter(Boolean);
    return {
      path: cssPath(f), id: f.id || null, name: f.getAttribute("name") || f.getAttribute("data-form") || null, action: f.getAttribute("action") ? abs(f.getAttribute("action")) : null, method: (f.getAttribute("method") || "get").toUpperCase(),
      heading: heading ? clean(heading.textContent).slice(0, 60) : null, submitText: submit ? clean(submit.textContent || submit.value).slice(0, 40) : null, region: region(f), fieldCount: merged.length, fields: merged, hiddenFields: hidden,
      hasPassword: !!f.querySelector("input[type=password]"), hasFileUpload: !!f.querySelector("input[type=file]"), hasCaptcha: !!f.querySelector("[class*=captcha], [id*=captcha], iframe[src*=recaptcha], iframe[src*=hcaptcha]"),
      errorSlots: f.querySelectorAll("[role=alert], .error, .invalid-feedback, [class*=error]").length,
    };
  });

  // ---- 按钮 / CTA ----
  const buttons = Array.from(document.querySelectorAll("button, [role=button], input[type=submit], input[type=button], a.btn, a[class*=btn], a[class*=button], a[class*=cta]")).filter(visible).map((b) => {
    const t = clean(b.getAttribute("aria-label") || b.textContent || b.value || b.title).slice(0, 50);
    const inForm = !!b.closest("form");
    const isTab = !!b.closest("[role=tablist], .tabs, [class*=tabs]") || b.getAttribute("role") === "tab";
    const kind = (b.type === "submit" || (inForm && !b.type)) ? "submit" : isTab ? "read" : WRITE_RE.test(t) ? "write" : READ_RE.test(t) ? "read" : b.tagName === "A" ? "navigate" : "unknown";
    return { text: t, tag: b.tagName.toLowerCase(), kind, href: b.tagName === "A" ? abs(b.getAttribute("href")) : null, region: region(b), path: cssPath(b), dataAttrs: Array.from(b.attributes).filter((a) => a.name.startsWith("data-") && !a.name.startsWith("data-cursor")).map((a) => a.name).slice(0, 4), disabled: b.disabled || b.getAttribute("aria-disabled") === "true" };
  });
  const dedupButtons = [];
  for (const b of buttons) { const hit = dedupButtons.find((x) => x.text === b.text && x.kind === b.kind && x.region === b.region); if (hit) hit.count++; else dedupButtons.push({ ...b, count: 1 }); }

  // ---- 列表 / 重复结构 / 表格 ----
  const PRICE_RE = /([¥$€£₩]|CNY|USD|RMB|元)\s?\d[\d,.]*|\d[\d,.]*\s?(元|CNY|USD)/;
  const DATE_RE = /\b(19|20)\d{2}[-/.年]\d{1,2}([-/.月]\d{1,2}日?)?\b|\b\d{1,2}\s(min|hour|day|week|month)s?\sago\b|\d+\s?(分钟|小时|天|周|月)前/;
  const RATING_RE = /[★☆]{3,}|\b[0-5](\.\d)?\s?\/\s?5\b|\b(\d(\.\d)?)\s?(分|stars?)\b/;
  const lists = [];
  const seenContainers = new Set();
  for (const c of Array.from(document.body.querySelectorAll("ul, ol, div, section, table tbody"))) {
    if (!visible(c) || seenContainers.has(c)) continue;
    const kids = Array.from(c.children).filter((k) => k.tagName !== "TEMPLATE");
    if (kids.length < 3) continue;
    const sig = (k) => k.tagName + "." + (typeof k.className === "string" ? k.className.split(/\s+/).slice(0, 2).join(".") : "");
    const groups = {};
    for (const k of kids) groups[sig(k)] = (groups[sig(k)] || 0) + 1;
    const [topSig, n] = Object.entries(groups).sort((a, b) => b[1] - a[1])[0];
    if (n < 3 || n / kids.length < 0.6) continue;
    const item = kids.find((k) => sig(k) === topSig);
    const itemArea = item.getBoundingClientRect().width * item.getBoundingClientRect().height;
    if (itemArea < 2000 && !c.closest("nav")) continue; // 太小的是导航 / 标签，不是内容列表
    if (c.closest("nav, header, footer") && !c.matches("table tbody")) continue;
    seenContainers.add(c);
    const itemText = clean(item.innerText);
    const fields = [];
    for (const node of Array.from(item.querySelectorAll("*"))) {
      const own = clean(Array.from(node.childNodes).filter((x) => x.nodeType === 3).map((x) => x.textContent).join(" "));
      if (!own || own.length > 120) continue;
      const cls = typeof node.className === "string" ? node.className.split(/\s+/)[0] : "";
      const kind = PRICE_RE.test(own) ? "price" : DATE_RE.test(own) ? "date" : RATING_RE.test(own) ? "rating" : /^(H[1-6])$/.test(node.tagName) || /title|name|heading/i.test(cls) ? "title" : /tag|badge|label|chip|category/i.test(cls) ? "tag" : /^(A)$/.test(node.tagName) ? "link" : "text";
      fields.push({ kind, cls: cls || null, tag: node.tagName.toLowerCase(), sample: own.slice(0, 60) });
      if (fields.length >= 12) break;
    }
    lists.push({
      path: cssPath(c), tag: c.tagName.toLowerCase(), classes: typeof c.className === "string" ? c.className.trim().slice(0, 60) : "", itemCount: n, itemTag: item.tagName.toLowerCase(), itemClasses: typeof item.className === "string" ? item.className.trim().slice(0, 60) : "",
      itemHasImage: !!item.querySelector("img, picture, svg[width], [style*=background-image]"), itemHasLink: !!item.querySelector("a[href]"), itemLinkSample: item.querySelector("a[href]") ? abs(item.querySelector("a[href]").getAttribute("href")) : null,
      itemHasPrice: PRICE_RE.test(itemText), itemHasDate: DATE_RE.test(itemText), itemHasRating: RATING_RE.test(itemText), itemButtons: Array.from(item.querySelectorAll("button, [role=button]")).map((b) => clean(b.textContent || b.getAttribute("aria-label")).slice(0, 30)).filter(Boolean).slice(0, 4),
      fields, heading: (() => { let p = c; for (let i = 0; i < 3 && p; i++, p = p.parentElement) { const h = p.querySelector(":scope > h1, :scope > h2, :scope > h3, :scope > div > h2, :scope > header h2"); if (h) return clean(h.textContent).slice(0, 60); } return null; })(),
      region: region(c), textSample: itemText.slice(0, 120),
    });
    if (lists.length >= 12) break;
  }
  const tables = Array.from(document.querySelectorAll("table")).filter(visible).map((t) => ({ path: cssPath(t), caption: t.caption ? clean(t.caption.textContent) : null, headers: Array.from(t.querySelectorAll("thead th, tr:first-child th, tr:first-child td")).map((h) => clean(h.textContent).slice(0, 40)), rowCount: t.querySelectorAll("tbody tr, tr").length, rowHeaders: Array.from(t.querySelectorAll("tbody tr > th:first-child, tr > th:first-child")).map((h) => clean(h.textContent).slice(0, 40)).slice(0, 20), hasActions: !!t.querySelector("tbody button, tbody a") }));

  // ---- 控件 ----
  const groupLabel = (el) => { const g = el.closest("fieldset, [role=group], .filter-group, [class*=filter], [class*=facet], details, section, div"); const h = g && g.querySelector("legend, h1,h2,h3,h4,h5,summary, [class*=title], strong"); return h ? clean(h.textContent).slice(0, 40) : null; };
  const filterGroups = {};
  for (const i of Array.from(document.querySelectorAll("input[type=radio], input[type=checkbox]")).filter(visible)) {
    if (i.closest("form") && (i.closest("form").querySelector("input[type=password]") || /order|checkout|结算|register/.test((i.closest("form").getAttribute("action") || "") + (i.closest("form").getAttribute("data-form") || "")))) continue;
    const key = (i.name || cssPath(i.parentElement)) + "|" + i.type;
    if (!filterGroups[key]) filterGroups[key] = { name: i.name || null, type: i.type, label: groupLabel(i), region: region(i), options: [] };
    if (filterGroups[key].options.length < 30) filterGroups[key].options.push({ value: i.value, label: labelOf(i), checked: i.checked });
  }
  const ranges = Array.from(document.querySelectorAll("input[type=range]")).filter(visible).map((r) => ({ name: r.name || null, label: labelOf(r) || groupLabel(r), min: r.min, max: r.max, step: r.step, value: r.value, region: region(r) }));
  const sorts = Array.from(document.querySelectorAll("select")).filter((s) => visible(s) && !s.closest("form[action*=order], form[action*=checkout], form[action*=register], form[action*=login]")).map((s) => ({ name: s.name || null, label: labelOf(s) || groupLabel(s), options: Array.from(s.options).map((o) => clean(o.textContent)).slice(0, 20), isSort: /sort|order|排序/i.test((s.name || "") + (labelOf(s) || "") + Array.from(s.options).map((o) => o.textContent).join(" ")), region: region(s), inForm: !!s.closest("form") }));
  const searches = Array.from(document.querySelectorAll("input[type=search], input[name*=q], input[name*=search], input[name*=keyword], input[placeholder*=搜索], input[placeholder*=Search], input[placeholder*=search], [role=search] input")).filter(visible).map((s) => ({ name: s.name || null, placeholder: s.placeholder || null, region: region(s), inForm: !!s.closest("form"), formAction: s.closest("form") ? abs(s.closest("form").getAttribute("action") || "") : null }));
  const paginations = Array.from(document.querySelectorAll("[class*=pagination], [class*=pager], nav[aria-label*=分页], nav[aria-label*=pagination], nav[aria-label*=Pagination]")).filter(visible).map((p) => ({ path: cssPath(p), items: Array.from(p.querySelectorAll("a, button")).map((x) => clean(x.textContent || x.getAttribute("aria-label")).slice(0, 12)).slice(0, 15), usesQuery: /[?&](page|p|offset)=/.test(Array.from(p.querySelectorAll("a[href]")).map((a) => a.href).join(" ")) }));
  const loadMore = dedupButtons.filter((b) => /(加载更多|更多|load more|show more|查看更多)/i.test(b.text)).map((b) => b.text);
  const tabs = Array.from(document.querySelectorAll("[role=tablist], .tabs, [class*=tabs]")).filter(visible).map((t) => ({ path: cssPath(t), items: Array.from(t.querySelectorAll("[role=tab], button, a")).map((x) => clean(x.textContent).slice(0, 30)).filter(Boolean).slice(0, 12), region: region(t) }));
  const accordions = Array.from(document.querySelectorAll("details, [aria-expanded], [class*=accordion], [class*=collapse]")).filter(visible).length;
  const modals = Array.from(document.querySelectorAll("dialog, [role=dialog], [class*=modal], [class*=drawer]")).length;

  // ---- 登录态 / 角色 / i18n / 互动 ----
  const authLinks = Array.from(document.querySelectorAll("a[href], button")).filter(visible).map((a) => ({ t: clean(a.textContent || a.getAttribute("aria-label")), h: a.getAttribute("href") || "" })).filter((x) => /(登录|注册|登出|退出|我的|个人中心|账户|account|login|sign ?in|sign ?up|register|logout|sign ?out|profile|dashboard)/i.test(x.t + " " + x.h)).map((x) => ({ text: x.t.slice(0, 30), href: abs(x.h) })).slice(0, 12);
  const avatar = !!document.querySelector("img[alt*=头像], img[alt*=avatar], [class*=avatar], [class*=user-menu], [class*=account-menu]");
  const roleHints = Array.from(new Set((text.match(/(会员|vip|premium|pro 版|企业版|商家|卖家|店铺|供应商|管理员|admin|后台|管理中心|讲师|作者|创作者|moderator|seller|merchant|vendor|partner|agent|经纪|代理)/gi) || []).map((s) => s.toLowerCase()))).slice(0, 12);
  const langSwitch = Array.from(document.querySelectorAll("[data-lang], [hreflang], [class*=lang], [class*=locale], select[name*=lang], select[name*=locale]")).filter(visible).map((x) => clean(x.textContent || x.getAttribute("hreflang") || x.getAttribute("data-lang")).slice(0, 20)).filter(Boolean).slice(0, 10);
  const currencies = Array.from(new Set((text.match(/[¥$€£₩]|\b(cny|usd|eur|gbp|jpy|rmb|hkd)\b/gi) || []).map((s) => s.toUpperCase()))).slice(0, 6);
  const interactions = {
    cart: !!document.querySelector("[class*=cart], [aria-label*=购物车], [aria-label*=cart], [data-cart-count], a[href*=cart]"), cartBadge: (document.querySelector("[data-cart-count], [class*=cart] [class*=badge], [class*=cart-count]") || {}).textContent || null,
    wishlist: !!document.querySelector("[class*=wish], [class*=favorite], [class*=favourite], [aria-label*=收藏], [aria-label*=心愿], [data-wishlist]"),
    like: !!document.querySelector("[class*=like], [aria-label*=点赞], [aria-label*=like]"), share: !!document.querySelector("[class*=share], [aria-label*=分享], [aria-label*=share]"),
    comments: !!document.querySelector("[class*=comment], [class*=review], [id*=comment], [id*=review], form[action*=comment], form[action*=review]"), rating: RATING_RE.test(text) || !!document.querySelector("[class*=rating], [class*=stars]"),
    follow: /(关注|follow)/i.test(dedupButtons.map((b) => b.text).join(" ")), upload: !!document.querySelector("input[type=file]"), download: !!document.querySelector("a[download], a[href$='.pdf'], a[href$='.zip']"),
    notifications: !!document.querySelector("[class*=notif], [aria-label*=通知], [aria-label*=notification], [class*=bell]"), chatWidget: !!document.querySelector("[class*=chat], [id*=intercom], [id*=crisp], [class*=livechat], iframe[src*=chat]"),
    newsletter: !!document.querySelector("form[action*=subscribe], form[data-form*=newsletter], input[type=email]:not(form[action*=login] input):not(form[action*=register] input)"),
    map: !!document.querySelector("iframe[src*=maps], [class*=map], #map, [id*=amap], [id*=bmap]"), video: !!document.querySelector("video, iframe[src*=youtube], iframe[src*=vimeo], iframe[src*=bilibili]"),
    compare: /(对比|compare)/i.test(dedupButtons.map((b) => b.text).join(" ")), coupon: !!document.querySelector("input[name*=coupon], input[name*=promo], input[placeholder*=优惠]"),
  };

  // ---- 第三方 ----
  const scriptSrcs = Array.from(document.scripts).map((s) => s.src).filter(Boolean);
  const iframeSrcs = Array.from(document.querySelectorAll("iframe[src]")).map((i) => i.src);
  const linkHrefs = Array.from(document.querySelectorAll("a[href^=http]")).map((a) => a.href);
  const THIRD = [
    ["payment", /(stripe|paypal|alipay|alipayobjects|wxpay|weixin.*pay|unionpay|adyen|braintree|square|klarna|checkout\.com|airwallex|paddle|lemonsqueezy)/i],
    ["analytics", /(googletagmanager|google-analytics|gtag|hm\.baidu|umeng|cnzz|clarity\.ms|hotjar|mixpanel|segment|amplitude|posthog|plausible|matomo|growingio|sensorsdata)/i],
    ["ads", /(doubleclick|googlesyndication|adsbygoogle|facebook\.net\/.*fbevents|tiktok.*pixel|criteo)/i],
    ["chat", /(intercom|crisp\.chat|zendesk|zopim|tawk|livechat|drift|hubspot|udesk|qiyukf|meiqia|53kf|tidio|freshchat)/i],
    ["maps", /(maps\.google|googleapis.*maps|amap\.com|api\.map\.baidu|mapbox|tianditu|qq\.com\/map)/i],
    ["auth", /(accounts\.google|appleid\.apple|open\.weixin|graph\.facebook|github\.com\/login|auth0|clerk|firebaseapp|supabase)/i],
    ["cdn-ui", /(fonts\.googleapis|fonts\.gstatic|cdn\.jsdelivr|unpkg|cdnjs|bootstrapcdn|fontawesome|iconify|at\.alicdn)/i],
    ["video", /(youtube|vimeo|bilibili|player\.polyv|aliyuncs.*player|wistia)/i],
    ["social", /(twitter\.com|x\.com|facebook\.com|instagram\.com|weibo\.com|zhihu\.com|linkedin\.com|github\.com|youtube\.com|tiktok\.com|douyin\.com|xiaohongshu\.com|discord\.gg|t\.me)/i],
    ["search", /(algolia|meilisearch|typesense)/i], ["forms", /(typeform|jotform|formspree|hsforms|jinshuju|wjx\.cn)/i], ["captcha", /(recaptcha|hcaptcha|turnstile|geetest|tencent.*captcha|aliyun.*captcha)/i],
  ];
  const thirdParty = [];
  for (const [cat, re] of THIRD) {
    const hits = [...scriptSrcs, ...iframeSrcs, ...(cat === "social" ? linkHrefs : [])].filter((u) => re.test(u));
    if (hits.length) thirdParty.push({ category: cat, evidence: Array.from(new Set(hits.map((u) => { try { return new URL(u).hostname; } catch (e) { return u.slice(0, 60); } }))).slice(0, 5) });
  }

  // ---- 结构化数据 / 实体线索 ----
  const jsonLd = Array.from(document.querySelectorAll("script[type='application/ld+json']")).map((s) => { try { const d = JSON.parse(s.textContent); const arr = Array.isArray(d) ? d : d["@graph"] ? d["@graph"] : [d]; return arr.map((x) => ({ type: x["@type"], keys: Object.keys(x).filter((k) => !k.startsWith("@")).slice(0, 20) })); } catch (e) { return null; } }).filter(Boolean).flat();
  const og = {}; document.querySelectorAll("meta[property^='og:'], meta[property^='product:'], meta[name^='twitter:']").forEach((m) => { og[m.getAttribute("property") || m.getAttribute("name")] = (m.content || "").slice(0, 100); });
  const headings = Array.from(document.querySelectorAll("h1, h2, h3")).filter(visible).map((h) => ({ level: h.tagName.toLowerCase(), text: clean(h.textContent).slice(0, 80) })).slice(0, 40);
  const entityHints = { prices: (text.match(PRICE_RE) || []).length ? (clean(document.body.innerText).match(new RegExp(PRICE_RE.source, "g")) || []).slice(0, 8) : [], dates: (clean(document.body.innerText).match(new RegExp(DATE_RE.source, "gi")) || []).slice(0, 6), ratings: (clean(document.body.innerText).match(new RegExp(RATING_RE.source, "g")) || []).slice(0, 4), emails: (text.match(/[\w.+-]+@[\w-]+\.[\w.]+/g) || []).slice(0, 3), phones: (text.match(/(\+?86)?1[3-9]\d{9}|\d{3,4}-\d{7,8}/g) || []).slice(0, 3) };

  // ---- 登录墙 ----
  // 登录墙：不是登录页本身，却只剩一张密码表单、几乎没有内容——说明原本的内容被挡在登录后面
  const pageType = guessType();
  const loginWall = pageType !== "auth" && !!pwd && forms.some((f) => f.hasPassword) && text.length < 1500 && lists.length === 0;

  const result = {
    url: location.href, title: document.title, lang: document.documentElement.lang || null, description: (document.querySelector("meta[name=description]") || {}).content || null,
    pageType, h1: clean((document.querySelector("h1") || {}).textContent || "").slice(0, 100), headings, breadcrumb, textLength: text.length, loginWall,
    navigation: { main: mainNav.slice(0, 40), footerGroups: footerGroups.slice(0, 8), side: sideNav.slice(0, 30) },
    forms, buttons: dedupButtons.slice(0, 60), lists, tables,
    controls: { filters: Object.values(filterGroups).slice(0, 12), ranges, sorts, searches, paginations, loadMore, tabs, accordions, modals },
    auth: { links: authLinks, avatar, hasPasswordField: !!pwd, roleHints }, i18n: { langSwitch, currencies, lang: document.documentElement.lang || null },
    interactions, thirdParty, jsonLd, openGraph: og, entityHints,
  };
  window.__wc = window.__wc || {};
  window.__wc.features = result;
  return JSON.parse(JSON.stringify(result)); // 去掉 undefined 键：与 _read.js 分片 / 脚本路径落盘字节一致
})();
