/* collect/links.js — 同域链接清单，用于 --follow-nav 多页采集。
   记录每个链接所在区域（header nav / footer / main / aside）、文字、是否在主导航里；同 URL（去 hash）去重。
   与 website-clone-visual / website-clone-functional 里的同名文件故意保持一致：安装单位是目录，不做跨目录引用。 */
(() => {
  const norm = (href) => { try { const u = new URL(href, location.href); u.hash = ""; return u.href; } catch (e) { return null; } };
  const seen = new Map();
  const region = (a) => (a.closest("header, [role=banner]") && "header") || (a.closest("nav, [role=navigation]") && "nav") || (a.closest("footer, [role=contentinfo]") && "footer") || (a.closest("aside") && "aside") || "main";
  for (const a of Array.from(document.querySelectorAll("a[href]"))) {
    const raw = a.getAttribute("href") || "";
    if (/^(mailto:|tel:|javascript:|#|sms:)/i.test(raw.trim())) continue;
    const href = norm(raw); if (!href) continue;
    let u; try { u = new URL(href); } catch (e) { continue; }
    const sameOrigin = u.origin === location.origin;
    const text = (a.getAttribute("aria-label") || a.textContent || a.title || (a.querySelector("img") && a.querySelector("img").alt) || "").replace(/\s+/g, " ").trim().slice(0, 80);
    const reg = region(a);
    const inMainNav = reg === "header" || (reg === "nav" && !a.closest("footer"));
    if (!seen.has(href)) seen.set(href, { url: href, path: u.pathname + u.search, sameOrigin, texts: [], regions: new Set(), inMainNav: false, count: 0, external: !sameOrigin, target: a.target || null, rel: a.rel || null });
    const e = seen.get(href);
    e.count++;
    if (text && !e.texts.includes(text) && e.texts.length < 4) e.texts.push(text);
    e.regions.add(reg);
    if (inMainNav) e.inMainNav = true;
  }
  const links = Array.from(seen.values()).map((l) => ({ ...l, regions: Array.from(l.regions) }));
  const result = {
    url: location.href,
    origin: location.origin,
    total: links.length,
    sameOrigin: links.filter((l) => l.sameOrigin).length,
    mainNav: links.filter((l) => l.sameOrigin && l.inMainNav).map((l) => l.url),
    links,
    // 供 SPA 判断：根容器是否为空、是否有 module 脚本
    spaHints: { emptyRoot: !!document.querySelector("#root:empty, #app:empty, #__next:empty"), moduleScripts: document.querySelectorAll("script[type=module]").length, bodyTextLength: (document.body.textContent || "").trim().length },
  };
  window.__wc = window.__wc || {};
  window.__wc.links = result;
  return JSON.parse(JSON.stringify(result)); // 去掉 undefined 键：与 _read.js 分片 / 脚本路径落盘字节一致
})();
