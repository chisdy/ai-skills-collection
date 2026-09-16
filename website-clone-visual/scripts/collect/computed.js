/* collect/computed.js — 可见元素的计算样式 + boundingBox。
   只采可见且尺寸 > 0 的元素，默认上限 1500 个（按文档顺序），约 40 个与布局 / 排版 / 颜色相关的属性；
   等于默认值的属性会被丢掉以控制体量。key 为 CSS path（nth-of-type 链），与 sections.js / animations.js 一致。
   可选参数：window.__wcOptions = { maxElements: 3000 } */
(() => {
  const opts = Object.assign({ maxElements: 1500, textLength: 60 }, window.__wcOptions || {});
  const PROPS = [
    "display", "position", "box-sizing", "overflow",
    "flex-direction", "flex-wrap", "justify-content", "align-items", "gap", "row-gap", "column-gap", "flex",
    "grid-template-columns", "grid-template-rows", "grid-auto-flow",
    "width", "height", "max-width", "min-height",
    "padding-top", "padding-right", "padding-bottom", "padding-left",
    "margin-top", "margin-right", "margin-bottom", "margin-left",
    "font-family", "font-size", "font-weight", "line-height", "letter-spacing", "text-transform", "text-align", "text-decoration-line",
    "color", "background-color", "background-image", "background-size", "background-position",
    "border-top-width", "border-top-style", "border-top-color", "border-radius",
    "box-shadow", "opacity", "z-index", "transform", "transition", "backdrop-filter", "object-fit", "aspect-ratio", "cursor",
  ];
  const DEFAULTS = {
    "position": "static", "box-sizing": "content-box", "overflow": "visible",
    "flex-direction": "row", "flex-wrap": "nowrap", "justify-content": "normal", "align-items": "normal",
    "gap": "normal", "row-gap": "normal", "column-gap": "normal", "flex": "0 1 auto",
    "grid-template-columns": "none", "grid-template-rows": "none", "grid-auto-flow": "row",
    "max-width": "none", "min-height": "0px", "width": "auto", "height": "auto",
    "padding-top": "0px", "padding-right": "0px", "padding-bottom": "0px", "padding-left": "0px",
    "margin-top": "0px", "margin-right": "0px", "margin-bottom": "0px", "margin-left": "0px",
    "letter-spacing": "normal", "text-transform": "none", "text-align": "start", "text-decoration-line": "none",
    "background-color": "rgba(0, 0, 0, 0)", "background-image": "none", "background-size": "auto", "background-position": "0% 0%",
    "border-top-width": "0px", "border-top-style": "none", "border-radius": "0px",
    "box-shadow": "none", "opacity": "1", "z-index": "auto", "transform": "none", "transition": "all 0s ease 0s", "transition_alt": "all",
    "backdrop-filter": "none", "object-fit": "fill", "aspect-ratio": "auto", "cursor": "auto",
  };

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

  const isVisible = (el, rect, cs) => {
    if (rect.width <= 0 || rect.height <= 0) return false;
    if (cs.display === "none" || cs.visibility === "hidden") return false;
    return true;
  };

  const elements = [];
  const all = document.body ? document.body.getElementsByTagName("*") : [];
  let truncated = false;
  for (const el of Array.from(all)) {
    if (/^(SCRIPT|STYLE|NOSCRIPT|TEMPLATE|LINK|META|BR|WBR|PATH|G|DEFS|USE|CIRCLE|RECT|LINE|POLYGON|POLYLINE|ELLIPSE|STOP|LINEARGRADIENT|RADIALGRADIENT|CLIPPATH|MASK|TSPAN)$/.test(el.tagName)) continue;
    const rect = el.getBoundingClientRect();
    const cs = getComputedStyle(el);
    if (!isVisible(el, rect, cs)) continue;
    if (elements.length >= opts.maxElements) { truncated = true; break; }
    const styles = {};
    const hasBorder = cs.borderTopStyle !== "none" && cs.borderTopWidth !== "0px";
    for (const p of PROPS) {
      const v = cs.getPropertyValue(p);
      if (!v || v === DEFAULTS[p]) continue;
      if (p === "width" || p === "height") continue; // 用 rect 代替
      if (p === "transition" && (v === "all" || /^all 0s/.test(v))) continue;
      if (p === "min-height" && v === "auto") continue;
      if (p.startsWith("border-top") && !hasBorder) continue; // 没有边框时 border-color 只是 currentColor 的回显
      styles[p] = v;
    }
    let text = "";
    for (const n of el.childNodes) if (n.nodeType === 3) text += n.textContent;
    text = text.replace(/\s+/g, " ").trim().slice(0, opts.textLength);
    elements.push({
      path: cssPath(el),
      tag: el.tagName.toLowerCase(),
      id: el.id || undefined,
      classes: el.className && typeof el.className === "string" ? el.className.trim().split(/\s+/).slice(0, 12) : undefined,
      text: text || undefined,
      rect: { x: Math.round(rect.left + window.scrollX), y: Math.round(rect.top + window.scrollY), w: Math.round(rect.width), h: Math.round(rect.height) },
      styles,
    });
  }

  const bodyCs = getComputedStyle(document.body);
  const result = {
    url: location.href,
    viewport: { width: window.innerWidth, height: window.innerHeight, dpr: window.devicePixelRatio, documentHeight: document.documentElement.scrollHeight },
    body: { fontFamily: bodyCs.fontFamily, fontSize: bodyCs.fontSize, lineHeight: bodyCs.lineHeight, color: bodyCs.color, backgroundColor: bodyCs.backgroundColor },
    count: elements.length,
    truncated,
    elements,
  };
  window.__wc = window.__wc || {};
  window.__wc.computed = result;
  return JSON.parse(JSON.stringify(result)); // 去掉 undefined 键：与 _read.js 分片 / 脚本路径落盘字节一致
})();
