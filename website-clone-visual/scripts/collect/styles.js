/* collect/styles.js — 样式表序列化。
   能读的 CSSOM 规则直接 cssText 输出；跨域被拦（SecurityError）的只给 href，由外层 fetch。
   顺带抽出 @media 条件（断点）、@keyframes 名、@font-face 数量、@import。 */
(() => {
  const sheets = [];
  const mediaQueries = new Map();
  const keyframes = [];
  let fontFaces = 0;

  const walkRules = (rules, sheetIndex) => {
    for (const rule of Array.from(rules)) {
      if (rule instanceof CSSMediaRule) {
        const cond = rule.conditionText || rule.media.mediaText;
        mediaQueries.set(cond, (mediaQueries.get(cond) || 0) + rule.cssRules.length);
        walkRules(rule.cssRules, sheetIndex);
      } else if (rule instanceof CSSKeyframesRule) {
        keyframes.push(rule.name);
      } else if (rule instanceof CSSFontFaceRule) {
        fontFaces++;
      } else if (rule instanceof CSSSupportsRule || (window.CSSLayerBlockRule && rule instanceof CSSLayerBlockRule) || (window.CSSContainerRule && rule instanceof CSSContainerRule)) {
        walkRules(rule.cssRules, sheetIndex);
      }
    }
  };

  Array.from(document.styleSheets).forEach((sheet, i) => {
    const entry = {
      index: i,
      href: sheet.href || null,
      inline: !sheet.href,
      media: sheet.media && sheet.media.mediaText ? sheet.media.mediaText : "",
      disabled: sheet.disabled,
      ownerTag: sheet.ownerNode ? sheet.ownerNode.tagName.toLowerCase() : null,
      ruleCount: 0,
      cssText: null,
      blocked: false,
      error: null,
    };
    try {
      const rules = sheet.cssRules;
      entry.ruleCount = rules.length;
      entry.cssText = Array.from(rules).map((r) => r.cssText).join("\n");
      walkRules(rules, i);
    } catch (e) {
      entry.blocked = true;
      entry.error = String(e && e.name ? e.name : e);
    }
    sheets.push(entry);
  });

  // 元素上的 style 属性也算样式来源，统计一下规模，供分析判断"内联样式有多重"
  let inlineStyleCount = 0;
  document.querySelectorAll("[style]").forEach(() => inlineStyleCount++);

  const result = {
    url: location.href,
    sheets,
    mediaQueries: Array.from(mediaQueries.entries()).map(([condition, ruleCount]) => ({ condition, ruleCount })),
    keyframes: Array.from(new Set(keyframes)),
    fontFaceCount: fontFaces,
    inlineStyleAttributeCount: inlineStyleCount,
    blockedHrefs: sheets.filter((s) => s.blocked && s.href).map((s) => s.href),
  };
  window.__wc = window.__wc || {};
  window.__wc.styles = result;
  return JSON.parse(JSON.stringify(result)); // 去掉 undefined 键：与 _read.js 分片 / 脚本路径落盘字节一致
})();
