/* collect/tokens.js — 设计 token：:root 自定义属性、@font-face、以及按出现频次统计的颜色 / 字号 / 字重 / 字体 / 间距 / 圆角 / 阴影。
   频次基于可见元素的计算样式（与 computed.js 同一套可见性判断），所以反映的是"页面上真的在用的值"。 */
(() => {
  const customProps = {};
  const fontFaces = [];
  const walk = (rules) => {
    for (const rule of Array.from(rules)) {
      if (rule instanceof CSSStyleRule && /^(:root|html)(\s*,\s*(:root|html))*$/.test(rule.selectorText.trim())) {
        for (const name of Array.from(rule.style)) {
          if (name.startsWith("--")) customProps[name] = rule.style.getPropertyValue(name).trim();
        }
      } else if (rule instanceof CSSFontFaceRule) {
        const s = rule.style;
        fontFaces.push({
          family: s.getPropertyValue("font-family").replace(/^["']|["']$/g, ""),
          src: s.getPropertyValue("src"),
          weight: s.getPropertyValue("font-weight") || null,
          style: s.getPropertyValue("font-style") || null,
          display: s.getPropertyValue("font-display") || null,
        });
      } else if (rule.cssRules) {
        walk(rule.cssRules);
      }
    }
  };
  for (const sheet of Array.from(document.styleSheets)) {
    try { walk(sheet.cssRules); } catch (e) { /* 跨域，跳过 */ }
  }
  // 自定义属性的解析值（可能引用别的变量）
  const rootCs = getComputedStyle(document.documentElement);
  const resolved = {};
  for (const name of Object.keys(customProps)) resolved[name] = rootCs.getPropertyValue(name).trim();

  const counter = () => new Map();
  const bump = (map, key, weight = 1) => { if (!key) return; map.set(key, (map.get(key) || 0) + weight); };
  const colors = counter(), fontSizes = counter(), fontWeights = counter(), fontFamilies = counter();
  const spacing = counter(), radii = counter(), shadows = counter(), lineHeights = counter(), gaps = counter(), zIndices = counter();
  const TRANSPARENT = /^rgba\(\d+, \d+, \d+, 0\)$/;

  for (const el of Array.from(document.body.getElementsByTagName("*"))) {
    if (/^(SCRIPT|STYLE|NOSCRIPT|TEMPLATE|PATH|G|DEFS|USE|CIRCLE|RECT|LINE|POLYGON|POLYLINE|ELLIPSE|STOP|LINEARGRADIENT|RADIALGRADIENT|CLIPPATH|MASK|TSPAN|SVG)$/.test(el.tagName)) continue;
    const rect = el.getBoundingClientRect();
    if (rect.width <= 0 || rect.height <= 0) continue;
    const cs = getComputedStyle(el);
    if (cs.display === "none" || cs.visibility === "hidden") continue;
    const area = Math.max(1, Math.log2(rect.width * rect.height));
    const hasText = Array.from(el.childNodes).some((n) => n.nodeType === 3 && n.textContent.trim());
    if (hasText) { bump(colors, cs.color); bump(fontSizes, cs.fontSize); bump(fontWeights, cs.fontWeight); bump(fontFamilies, cs.fontFamily); bump(lineHeights, cs.lineHeight); }
    if (!TRANSPARENT.test(cs.backgroundColor)) bump(colors, cs.backgroundColor, Math.round(area / 4));
    if (cs.borderTopStyle !== "none" && cs.borderTopWidth !== "0px") bump(colors, cs.borderTopColor);
    for (const side of ["paddingTop", "paddingRight", "paddingBottom", "paddingLeft", "marginTop", "marginRight", "marginBottom", "marginLeft"]) {
      const v = cs[side]; if (v && v !== "0px" && !v.startsWith("-")) bump(spacing, v);
    }
    if (cs.rowGap && cs.rowGap !== "normal" && cs.rowGap !== "0px") bump(gaps, cs.rowGap);
    if (cs.columnGap && cs.columnGap !== "normal" && cs.columnGap !== "0px") bump(gaps, cs.columnGap);
    if (cs.borderRadius && cs.borderRadius !== "0px") bump(radii, cs.borderRadius);
    if (cs.boxShadow && cs.boxShadow !== "none") bump(shadows, cs.boxShadow);
    if (cs.zIndex && cs.zIndex !== "auto") bump(zIndices, cs.zIndex);
  }

  const top = (map, n = 24) => Array.from(map.entries()).sort((a, b) => b[1] - a[1]).slice(0, n).map(([value, count]) => ({ value, count }));
  const numeric = (map) => Array.from(map.entries()).map(([value, count]) => ({ value, px: parseFloat(value), count })).filter((x) => !isNaN(x.px)).sort((a, b) => a.px - b.px);

  const result = {
    url: location.href,
    customProperties: customProps,
    customPropertiesResolved: resolved,
    fontFaces,
    colors: top(colors, 32),
    fontFamilies: top(fontFamilies, 8),
    fontSizes: numeric(fontSizes),
    fontWeights: top(fontWeights, 8),
    lineHeights: top(lineHeights, 10),
    spacing: numeric(spacing).slice(0, 40),
    gaps: numeric(gaps),
    radii: top(radii, 12),
    shadows: top(shadows, 12),
    zIndices: top(zIndices, 10),
  };
  window.__wc = window.__wc || {};
  window.__wc.tokens = result;
  return JSON.parse(JSON.stringify(result)); // 去掉 undefined 键：与 _read.js 分片 / 脚本路径落盘字节一致
})();
