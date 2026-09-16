/* collect/assets.js — 素材 URL 清单（只列，不下载）：图片（img/srcset/picture/背景图）、视频与 poster、字体、favicon、样式表、脚本。
   全部转成绝对 URL；每条带类型、来源元素、alt、渲染尺寸与原始尺寸，供 download_assets.py 与蓝图的素材清单使用。 */
(() => {
  const abs = (u) => { try { return new URL(u, location.href).href; } catch (e) { return null; } };
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
  const seen = new Map();
  const add = (url, type, extra) => {
    const u = abs(url); if (!u || u.startsWith("data:") && u.length > 200000) return;
    if (!seen.has(u)) seen.set(u, { url: u, type, isDataUri: u.startsWith("data:"), usedBy: [], ...extra });
    const e = seen.get(u);
    if (extra && extra.usedBy && e.usedBy.length < 5) e.usedBy.push(extra.usedBy);
    if (extra && extra.alt && !e.alt) e.alt = extra.alt;
    if (extra && extra.rendered && !e.rendered) e.rendered = extra.rendered;
    if (extra && extra.natural && !e.natural) e.natural = extra.natural;
  };
  const parseSrcset = (s) => (s || "").split(",").map((p) => p.trim().split(/\s+/)[0]).filter(Boolean);

  for (const img of Array.from(document.images)) {
    const r = img.getBoundingClientRect();
    const extra = { usedBy: cssPath(img), alt: img.alt || null, rendered: { w: Math.round(r.width), h: Math.round(r.height) }, natural: { w: img.naturalWidth, h: img.naturalHeight }, loading: img.loading || null };
    if (img.currentSrc) add(img.currentSrc, "image", extra);
    if (img.getAttribute("src")) add(img.getAttribute("src"), "image", extra);
    for (const c of parseSrcset(img.getAttribute("srcset"))) add(c, "image-srcset", extra);
  }
  for (const s of Array.from(document.querySelectorAll("picture source"))) for (const c of parseSrcset(s.getAttribute("srcset"))) add(c, "image-srcset", { usedBy: cssPath(s), media: s.getAttribute("media"), mime: s.getAttribute("type") });
  for (const v of Array.from(document.querySelectorAll("video"))) {
    if (v.getAttribute("src")) add(v.getAttribute("src"), "video", { usedBy: cssPath(v), autoplay: v.autoplay, loop: v.loop, muted: v.muted });
    if (v.poster) add(v.poster, "video-poster", { usedBy: cssPath(v) });
    for (const s of Array.from(v.querySelectorAll("source"))) if (s.getAttribute("src")) add(s.getAttribute("src"), "video", { usedBy: cssPath(v), mime: s.getAttribute("type") });
  }
  for (const a of Array.from(document.querySelectorAll("audio, audio source"))) if (a.getAttribute("src")) add(a.getAttribute("src"), "audio", { usedBy: cssPath(a) });
  for (const o of Array.from(document.querySelectorAll("object[data], embed[src]"))) add(o.getAttribute("data") || o.getAttribute("src"), "embed", { usedBy: cssPath(o) });

  // 背景图（含伪元素）
  const URL_RE = /url\((['"]?)(.*?)\1\)/g;
  for (const el of Array.from(document.body.getElementsByTagName("*"))) {
    for (const pseudo of [null, "::before", "::after"]) {
      const cs = getComputedStyle(el, pseudo);
      const bg = cs.backgroundImage;
      if (!bg || bg === "none") continue;
      let m; URL_RE.lastIndex = 0;
      while ((m = URL_RE.exec(bg))) { const r = el.getBoundingClientRect(); add(m[2], "background-image", { usedBy: cssPath(el) + (pseudo || ""), rendered: { w: Math.round(r.width), h: Math.round(r.height) }, backgroundSize: cs.backgroundSize, backgroundPosition: cs.backgroundPosition, backgroundRepeat: cs.backgroundRepeat }); }
      const mask = cs.maskImage || cs.webkitMaskImage;
      if (mask && mask !== "none") { URL_RE.lastIndex = 0; while ((m = URL_RE.exec(mask))) add(m[2], "mask-image", { usedBy: cssPath(el) + (pseudo || "") }); }
    }
  }

  // 字体（可读的 CSSOM）
  const walk = (rules, baseHref) => {
    for (const rule of Array.from(rules)) {
      if (rule instanceof CSSFontFaceRule) {
        const src = rule.style.getPropertyValue("src"); let m; URL_RE.lastIndex = 0;
        while ((m = URL_RE.exec(src))) { let u = m[2]; try { u = new URL(u, baseHref || location.href).href; } catch (e) {} add(u, "font", { family: rule.style.getPropertyValue("font-family").replace(/^["']|["']$/g, ""), weight: rule.style.getPropertyValue("font-weight") || null, style: rule.style.getPropertyValue("font-style") || null, usedBy: baseHref || "inline <style>" }); }
      } else if (rule.cssRules) walk(rule.cssRules, baseHref);
    }
  };
  for (const sheet of Array.from(document.styleSheets)) { try { walk(sheet.cssRules, sheet.href); } catch (e) {} }

  for (const l of Array.from(document.querySelectorAll("link[rel~='icon'], link[rel='apple-touch-icon'], link[rel='manifest']"))) add(l.href, l.rel.includes("manifest") ? "manifest" : "favicon", { sizes: l.getAttribute("sizes") });
  for (const l of Array.from(document.querySelectorAll("link[rel='stylesheet']"))) add(l.href, "stylesheet", { media: l.media || null });
  for (const l of Array.from(document.querySelectorAll("link[rel='preload'][as='font'], link[rel='preload'][as='image']"))) add(l.href, l.getAttribute("as") === "font" ? "font" : "image", { preload: true });
  for (const s of Array.from(document.scripts)) if (s.src) add(s.src, "script", { module: s.type === "module", defer: s.defer, async: s.async });
  const og = document.querySelector("meta[property='og:image']"); if (og && og.content) add(og.content, "og-image", {});

  const assets = Array.from(seen.values());
  const byType = {};
  for (const a of assets) byType[a.type] = (byType[a.type] || 0) + 1;
  const result = { url: location.href, origin: location.origin, count: assets.length, byType, assets };
  window.__wc = window.__wc || {};
  window.__wc.assets = result;
  return JSON.parse(JSON.stringify(result)); // 去掉 undefined 键：与 _read.js 分片 / 脚本路径落盘字节一致
})();
