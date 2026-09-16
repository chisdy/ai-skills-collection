/* collect/sections.js — 把页面切成区块（header / hero / feature grid / footer …）。
   候选：landmark 元素（header/nav/main/footer/aside）、section/article、main 或 body 的直接块级子元素；
   过滤高度 < 40px 的；有已入选祖先的元素（main 除外）不再入选，保证输出是"一层"区块清单。
   每个区块记录：位置、标题、布局模式（flex/grid + 列数）、内容统计、用到的主要背景色 / 文字色，供蓝图逐区块复刻。 */
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
  const clean = (t) => (t || "").replace(/\s+/g, " ").trim();
  const visible = (el) => { const r = el.getBoundingClientRect(); const cs = getComputedStyle(el); return r.width > 0 && r.height >= 40 && cs.display !== "none" && cs.visibility !== "hidden"; };

  // 最像"内容容器"的后代：面积最大且有 >= 2 个子元素的 flex/grid
  const layoutOf = (el) => {
    let best = null, bestArea = 0;
    const consider = (node, depth) => {
      if (depth > 4) return;
      const cs = getComputedStyle(node);
      if ((cs.display.includes("flex") || cs.display.includes("grid")) && node.children.length >= 2) {
        const r = node.getBoundingClientRect(); const area = r.width * r.height;
        if (area > bestArea) { bestArea = area; best = { node, cs }; }
      }
      for (const c of Array.from(node.children)) consider(c, depth + 1);
    };
    consider(el, 0);
    if (!best) return { mode: "flow", container: null };
    const { node, cs } = best;
    const mode = cs.display.includes("grid") ? "grid" : "flex";
    let columns = null;
    if (mode === "grid") {
      const tracks = cs.gridTemplateColumns.split(" ").filter((t) => t && t !== "none");
      columns = tracks.length || null;
    } else if (cs.flexDirection.startsWith("row")) {
      // 同一行内的子元素数
      const tops = Array.from(node.children).map((c) => Math.round(c.getBoundingClientRect().top));
      const first = tops[0]; columns = tops.filter((t) => Math.abs(t - first) < 4).length;
    } else columns = 1;
    return { mode, container: cssPath(node), containerClasses: typeof node.className === "string" ? node.className.trim() : "", direction: cs.flexDirection, justify: cs.justifyContent, align: cs.alignItems, gap: cs.gap, gridTemplateColumns: mode === "grid" ? cs.gridTemplateColumns : undefined, columns, childCount: node.children.length, childTag: node.children[0] ? node.children[0].tagName.toLowerCase() : null };
  };

  const candidates = new Set();
  document.querySelectorAll("header, nav, main, footer, aside, section, article, [role=banner], [role=contentinfo], [role=region], [role=navigation]").forEach((el) => candidates.add(el));
  const containers = [document.body, ...Array.from(document.querySelectorAll("main, #root, #app, #__next, #__nuxt, .page, .site, .wrapper, .container"))];
  for (const c of containers) for (const child of Array.from(c.children)) {
    const cs = getComputedStyle(child);
    if (/^(SCRIPT|STYLE|LINK|NOSCRIPT|TEMPLATE)$/.test(child.tagName)) continue;
    if (cs.display !== "inline" && child.getBoundingClientRect().height >= 80) candidates.add(child);
  }

  let list = Array.from(candidates).filter(visible);
  // 去掉有入选祖先的（main / body / 通用容器除外，它们只作为容器不作为区块）
  const isWrapper = (el) => el === document.body || el.tagName === "MAIN" || /^(root|app|__next|__nuxt)$/.test(el.id) || (el.children.length === 1 && el.tagName === "DIV");
  const chosen = list.filter((el) => {
    if (isWrapper(el)) return false;
    let p = el.parentElement;
    while (p && p !== document.body) { if (list.includes(p) && !isWrapper(p)) return false; p = p.parentElement; }
    return true;
  });
  chosen.sort((a, b) => a.getBoundingClientRect().top - b.getBoundingClientRect().top || a.getBoundingClientRect().left - b.getBoundingClientRect().left);

  const sections = chosen.map((el, i) => {
    const r = el.getBoundingClientRect(); const cs = getComputedStyle(el);
    const heading = el.querySelector("h1, h2, h3, h4, [role=heading]");
    const role = el.getAttribute("role") || (el.tagName === "HEADER" && "banner") || (el.tagName === "FOOTER" && "contentinfo") || (el.tagName === "NAV" && "navigation") || null;
    const kindGuess = (() => {
      const cls = (typeof el.className === "string" ? el.className : "").toLowerCase();
      if (el.tagName === "HEADER" || role === "banner" || /header|navbar|topbar/.test(cls)) return "header";
      if (el.tagName === "FOOTER" || role === "contentinfo" || /footer/.test(cls)) return "footer";
      if (el.tagName === "NAV") return "nav";
      if (/hero|banner|jumbotron|masthead|splash/.test(cls) || (i <= 2 && heading && heading.tagName === "H1")) return "hero";
      if (/testimonial|review|quote/.test(cls)) return "testimonial";
      if (/pricing|plan/.test(cls)) return "pricing";
      if (/faq|accordion/.test(cls)) return "faq";
      if (/cta|newsletter|subscribe|signup/.test(cls)) return "cta";
      if (/feature|benefit|service|grid|cards|showcase|product|gallery|portfolio|team|logo|partner|stat/.test(cls)) return "grid";
      if (/form|contact|login|checkout|auth/.test(cls) || el.querySelector("form")) return "form";
      if (el.querySelector("table")) return "table";
      return "content";
    })();
    const imgs = el.querySelectorAll("img, picture, video, svg:not(:scope svg svg)");
    return {
      index: i,
      path: cssPath(el),
      tag: el.tagName.toLowerCase(),
      id: el.id || null,
      classes: typeof el.className === "string" ? el.className.trim() : "",
      role, kindGuess,
      heading: heading ? { tag: heading.tagName.toLowerCase(), text: clean(heading.textContent).slice(0, 120) } : null,
      rect: { x: Math.round(r.left + window.scrollX), y: Math.round(r.top + window.scrollY), w: Math.round(r.width), h: Math.round(r.height) },
      style: { display: cs.display, position: cs.position, backgroundColor: cs.backgroundColor, backgroundImage: cs.backgroundImage !== "none" ? cs.backgroundImage.slice(0, 200) : null, color: cs.color, padding: `${cs.paddingTop} ${cs.paddingRight} ${cs.paddingBottom} ${cs.paddingLeft}`, maxWidth: cs.maxWidth, borderTop: cs.borderTopStyle !== "none" ? `${cs.borderTopWidth} ${cs.borderTopStyle} ${cs.borderTopColor}` : null, borderBottom: cs.borderBottomStyle !== "none" ? `${cs.borderBottomWidth} ${cs.borderBottomStyle} ${cs.borderBottomColor}` : null },
      layout: layoutOf(el),
      counts: { text: clean(el.textContent).length, links: el.querySelectorAll("a[href]").length, buttons: el.querySelectorAll("button, [role=button], input[type=submit]").length, images: imgs.length, forms: el.querySelectorAll("form").length, inputs: el.querySelectorAll("input, select, textarea").length, headings: el.querySelectorAll("h1,h2,h3,h4,h5,h6").length, listItems: el.querySelectorAll("li").length },
      textPreview: clean(el.textContent).slice(0, 160),
    };
  });

  const result = {
    url: location.href,
    viewport: { width: window.innerWidth, height: window.innerHeight, documentHeight: document.documentElement.scrollHeight },
    count: sections.length,
    sections,
  };
  window.__wc = window.__wc || {};
  window.__wc.sections = result;
  return JSON.parse(JSON.stringify(result)); // 去掉 undefined 键：与 _read.js 分片 / 脚本路径落盘字节一致
})();
