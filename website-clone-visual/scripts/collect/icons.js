/* collect/icons.js — 图标清单。
   四类来源：内联 <svg>（按内容 hash 去重）、<use href="#id"> 精灵图、icon-font class（Font Awesome / Material / iconfont…）、小尺寸 <img src=*.svg>。
   每个图标记录语义线索（aria-label、title、所在按钮 / 链接的文字、class 名、邻近文字），供 map_icons.py 映射到 Lucide / Heroicons / Iconify。
   内联 SVG 的 outerHTML 也保留（去掉 class/id/style 等无关属性后），方便无法映射时直接内联使用。 */
(() => {
  const cssPath = (el) => {
    const parts = [];
    while (el && el.nodeType === 1 && el !== document.documentElement) {
      let part = el.tagName.toLowerCase();
      if (el.id && /^[A-Za-z][\w-]*$/.test(el.id)) { parts.unshift(`#${el.id}`); break; }
      const parent = el.parentElement;
      if (parent) {
        const same = Array.from(parent.children).filter((c) => c.tagName === el.tagName);
        if (same.length > 1) part += `:nth-of-type(${same.indexOf(el) + 1})`;
      }
      parts.unshift(part);
      el = parent;
    }
    return parts.join(" > ");
  };
  const hash = (s) => { let h = 5381; for (let i = 0; i < s.length; i++) h = ((h << 5) + h + s.charCodeAt(i)) | 0; return (h >>> 0).toString(16).padStart(8, "0"); };
  const clean = (t) => (t || "").replace(/\s+/g, " ").trim().slice(0, 80);
  const context = (el) => {
    const host = el.closest("button, a, [role=button], [role=tab], [role=menuitem], label, li, h1, h2, h3, h4, summary") || el.parentElement;
    const ctx = {
      ariaLabel: el.getAttribute("aria-label") || (host && host.getAttribute("aria-label")) || null,
      title: el.getAttribute("title") || (el.querySelector && el.querySelector("title") ? el.querySelector("title").textContent : null) || (host && host.getAttribute("title")) || null,
      hostTag: host ? host.tagName.toLowerCase() : null,
      hostText: host ? clean(host.textContent) : null,
      hostHref: host && host.getAttribute ? host.getAttribute("href") : null,
      classes: typeof el.className === "string" ? el.className.trim() : (el.className && el.className.baseVal) || "",
      hostClasses: host && typeof host.className === "string" ? host.className.trim() : "",
      dataIcon: el.getAttribute("data-icon") || el.getAttribute("data-lucide") || el.getAttribute("data-feather") || null,
      region: (el.closest("header, nav") && "header") || (el.closest("footer") && "footer") || (el.closest("aside") && "aside") || "main",
    };
    return ctx;
  };
  const rectOf = (el) => { const r = el.getBoundingClientRect(); return { w: Math.round(r.width), h: Math.round(r.height), visible: r.width > 0 && r.height > 0 }; };

  // 1. 内联 SVG（排除超大的插画：任一边 > 160px 视为插图而非图标，但仍记录到 illustrations）
  const inlineMap = new Map(), illustrations = [];
  const STRIP = /^(class|id|style|aria-\w+|data-\w+|focusable|role|tabindex|xmlns:xlink)$/i;
  for (const svg of Array.from(document.querySelectorAll("svg"))) {
    if (svg.closest("svg") !== svg) continue; // 嵌套 svg 跳过
    if (svg.querySelector("use")) continue; // 交给精灵图分支
    const r = rectOf(svg);
    const copy = svg.cloneNode(true);
    for (const n of [copy, ...Array.from(copy.querySelectorAll("*"))]) for (const a of Array.from(n.attributes)) if (STRIP.test(a.name)) n.removeAttribute(a.name);
    copy.querySelectorAll("title, desc").forEach((n) => n.remove());
    const markup = copy.outerHTML.replace(/\s+/g, " ").trim();
    const isIcon = r.w <= 160 && r.h <= 160;
    if (!isIcon) { illustrations.push({ path: cssPath(svg), size: r, bytes: markup.length, viewBox: svg.getAttribute("viewBox") }); continue; }
    const h = hash(markup);
    if (!inlineMap.has(h)) {
      inlineMap.set(h, { id: `svg-${h}`, hash: h, kind: "inline-svg", viewBox: svg.getAttribute("viewBox"), pathCount: copy.querySelectorAll("path, circle, rect, line, polyline, polygon, ellipse").length, strokeBased: /stroke=/.test(markup) && !/fill="(?!none)/.test(markup), markup, count: 0, sizes: [], occurrences: [] });
    }
    const e = inlineMap.get(h);
    e.count++;
    if (r.visible) e.sizes.push(`${r.w}x${r.h}`);
    if (e.occurrences.length < 5) e.occurrences.push({ path: cssPath(svg), ...context(svg) });
  }

  // 2. 精灵图 <use href="#id">
  const sprites = new Map();
  for (const use of Array.from(document.querySelectorAll("svg use"))) {
    const href = use.getAttribute("href") || use.getAttribute("xlink:href") || "";
    const svg = use.closest("svg");
    const key = href;
    if (!sprites.has(key)) {
      const symId = href.startsWith("#") ? href.slice(1) : null;
      const sym = symId ? document.getElementById(symId) : null;
      sprites.set(key, { id: `use-${hash(href)}`, kind: "svg-sprite", href, symbolFound: !!sym, symbolMarkup: sym ? sym.outerHTML.replace(/\s+/g, " ").slice(0, 4000) : null, viewBox: sym ? sym.getAttribute("viewBox") : null, count: 0, sizes: [], occurrences: [] });
    }
    const e = sprites.get(key);
    e.count++;
    const r = rectOf(svg || use);
    if (r.visible) e.sizes.push(`${r.w}x${r.h}`);
    if (e.occurrences.length < 5) e.occurrences.push({ path: cssPath(svg || use), ...context(svg || use) });
  }

  // 3. icon-font class
  const FONT_CLASS = /(^|\s)((fa|fas|far|fab|fal|fad|fa-solid|fa-regular|fa-brands|fa-light|fa-duotone)(\s|$)|fa-[\w-]+|material-icons[\w-]*|material-symbols[\w-]*|icon-[\w-]+|iconfont|icon|bi(\s|$)|bi-[\w-]+|ri-[\w-]+|mdi(\s|$)|mdi-[\w-]+|ti-[\w-]+|la(\s|$)|la-[\w-]+|ph(\s|$)|ph-[\w-]+|feather-[\w-]+|lni-[\w-]+|uil-[\w-]+|anticon(-[\w-]+)?|el-icon-[\w-]+|glyphicon(-[\w-]+)?|ion-[\w-]+|dashicons(-[\w-]+)?)/;
  const fonts = new Map();
  for (const el of Array.from(document.querySelectorAll("i, span, em, [class*='icon']"))) {
    const cls = typeof el.className === "string" ? el.className.trim() : "";
    if (!cls || !FONT_CLASS.test(" " + cls + " ")) continue;
    if (el.children.length > 0) continue; // 有子元素的是容器（比如包着 <svg> 的 .icon-btn），不是字体图标
    const rr = rectOf(el);
    if (rr.visible && (rr.w > 96 || rr.h > 96)) continue; // 太大的不是图标
    const ligature = el.tagName !== "I" && /material/.test(cls) ? clean(el.textContent) : (el.tagName === "I" ? clean(el.textContent) : "");
    const key = cls + "|" + ligature;
    if (!fonts.has(key)) {
      const family = /material-symbols/.test(cls) ? "Material Symbols" : /material-icons/.test(cls) ? "Material Icons" : /(^|\s)(fa|fas|far|fab|fal|fad|fa-)/.test(cls) ? "Font Awesome" : /(^|\s)bi(-|\s|$)/.test(cls) ? "Bootstrap Icons" : /(^|\s)ri-/.test(cls) ? "Remix Icon" : /(^|\s)mdi/.test(cls) ? "Material Design Icons" : /(^|\s)ph(-|\s|$)/.test(cls) ? "Phosphor" : /iconfont/.test(cls) ? "iconfont" : /anticon/.test(cls) ? "Ant Design Icons" : /el-icon/.test(cls) ? "Element Icons" : /ion-/.test(cls) ? "Ionicons" : "unknown";
      fonts.set(key, { id: `font-${hash(key)}`, kind: "icon-font", family, classes: cls, ligature: ligature || null, count: 0, sizes: [], occurrences: [] });
    }
    const e = fonts.get(key);
    e.count++;
    const r = rectOf(el);
    if (r.visible) e.sizes.push(`${r.w}x${r.h}`);
    if (e.occurrences.length < 5) e.occurrences.push({ path: cssPath(el), ...context(el) });
  }

  // 4. 小尺寸 svg/png 图片（<= 64px）
  const images = [];
  for (const img of Array.from(document.querySelectorAll("img"))) {
    const r = rectOf(img);
    const src = img.currentSrc || img.src;
    if (!src) continue;
    const small = r.visible && r.w <= 64 && r.h <= 64;
    if (small || /\.svg(\?|$)/i.test(src) && r.w <= 160) {
      images.push({ id: `img-${hash(src)}`, kind: "img", src, alt: img.alt || null, size: r, path: cssPath(img), ...context(img) });
    }
  }

  const result = {
    url: location.href,
    inline: Array.from(inlineMap.values()),
    sprites: Array.from(sprites.values()),
    fonts: Array.from(fonts.values()),
    images,
    illustrations,
    summary: { inlineUnique: inlineMap.size, spriteUnique: sprites.size, fontUnique: fonts.size, imageIcons: images.length, illustrations: illustrations.length },
  };
  window.__wc = window.__wc || {};
  window.__wc.icons = result;
  return JSON.parse(JSON.stringify(result)); // 去掉 undefined 键：与 _read.js 分片 / 脚本路径落盘字节一致
})();
