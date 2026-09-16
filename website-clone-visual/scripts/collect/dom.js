/* collect/dom.js — 渲染后的 DOM 快照。
   自包含 IIFE；结果同时写入 window.__wc.dom（供 MCP 路径用 _read.js 分片读取）并作为返回值。
   清理：去掉 <script>、noscript、内联事件属性、常见埋点属性；保留 style 与 class（复刻需要）。 */
(() => {
  const root = document.documentElement.cloneNode(true);
  root.querySelectorAll("script, noscript, template, iframe[src*='googletagmanager'], iframe[src*='doubleclick']").forEach((n) => n.remove());
  const TRACKING = /^(data-(gtm|ga|gtag|track|analytics|hotjar|hj|clarity|segment|amplitude|mixpanel|fb|pixel)|onclick$|on[a-z]+$)/i;
  root.querySelectorAll("*").forEach((el) => {
    for (const attr of Array.from(el.attributes)) {
      if (TRACKING.test(attr.name)) el.removeAttribute(attr.name);
    }
  });
  const meta = {};
  document.querySelectorAll("meta[name], meta[property]").forEach((m) => {
    const k = m.getAttribute("name") || m.getAttribute("property");
    if (/^(description|viewport|theme-color|og:title|og:description|og:image|twitter:card)$/i.test(k)) meta[k] = m.getAttribute("content");
  });
  const dt = document.doctype;
  const result = {
    url: location.href,
    title: document.title,
    lang: document.documentElement.lang || null,
    doctype: dt ? `<!DOCTYPE ${dt.name}${dt.publicId ? ` PUBLIC "${dt.publicId}"` : ""}${dt.systemId ? ` "${dt.systemId}"` : ""}>` : "<!DOCTYPE html>",
    meta,
    html: root.outerHTML,
    elementCount: document.getElementsByTagName("*").length,
  };
  window.__wc = window.__wc || {};
  window.__wc.dom = result;
  return JSON.parse(JSON.stringify(result)); // 去掉 undefined 键：与 _read.js 分片 / 脚本路径落盘字节一致
})();
