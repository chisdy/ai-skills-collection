/* collect/animations.js — 动画与过渡清单。
   - @keyframes 定义（名字 → 各帧 cssText）
   - 带 animation 的元素、带 transition 的元素（path + 参数）
   - document.getAnimations() 当前正在跑 / 已完成的动画
   - 滚动显现检测：第一次调用（页面顶部、滚动前）记录候选元素的 opacity / transform / class；
     第二次调用（滚动到底并回顶之后）对比，变化了的就是 scroll-reveal。
   调用两次是外层（capture_site.py 或 MCP 操作序列）的职责。 */
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

  // 1. @keyframes
  const keyframes = {};
  const walk = (rules) => {
    for (const rule of Array.from(rules)) {
      if (rule instanceof CSSKeyframesRule) {
        keyframes[rule.name] = Array.from(rule.cssRules).map((k) => ({ keyText: k.keyText, style: k.style.cssText }));
      } else if (rule.cssRules) walk(rule.cssRules);
    }
  };
  for (const sheet of Array.from(document.styleSheets)) { try { walk(sheet.cssRules); } catch (e) { /* 跨域 */ } }

  // 2. 元素扫描
  const animated = [], transitions = [], candidates = [];
  const REVEAL_CLASS = /(reveal|aos|animate|in-view|inview|fade|slide|appear|visible|active|show|wow|motion|scroll)/i;
  for (const el of Array.from(document.body.getElementsByTagName("*"))) {
    if (/^(SCRIPT|STYLE|NOSCRIPT|TEMPLATE|PATH|G|DEFS|USE|CIRCLE|RECT|LINE|POLYGON|POLYLINE|ELLIPSE|STOP|LINEARGRADIENT|RADIALGRADIENT|CLIPPATH|MASK|TSPAN)$/.test(el.tagName)) continue;
    const cs = getComputedStyle(el);
    if (cs.display === "none") continue;
    const path = cssPath(el);
    if (cs.animationName && cs.animationName !== "none") {
      animated.push({ path, tag: el.tagName.toLowerCase(), classes: typeof el.className === "string" ? el.className : "", animationName: cs.animationName, duration: cs.animationDuration, timingFunction: cs.animationTimingFunction, delay: cs.animationDelay, iterationCount: cs.animationIterationCount, fillMode: cs.animationFillMode, playState: cs.animationPlayState });
    }
    const hasTransition = cs.transitionDuration && cs.transitionDuration.split(",").some((d) => parseFloat(d) > 0);
    if (hasTransition) {
      transitions.push({ path, tag: el.tagName.toLowerCase(), classes: typeof el.className === "string" ? el.className : "", property: cs.transitionProperty, duration: cs.transitionDuration, timingFunction: cs.transitionTimingFunction, delay: cs.transitionDelay });
    }
    const cls = typeof el.className === "string" ? el.className : "";
    const dataAttrs = Array.from(el.attributes).filter((a) => /^data-(aos|animate|scroll|reveal|sal|wow|inview)/i.test(a.name)).map((a) => `${a.name}="${a.value}"`);
    if (hasTransition || REVEAL_CLASS.test(cls) || dataAttrs.length || (cs.opacity !== "1" && el.getBoundingClientRect().height > 0)) {
      candidates.push({ path, opacity: cs.opacity, transform: cs.transform, visibility: cs.visibility, classes: cls, dataAttrs, rectTop: Math.round(el.getBoundingClientRect().top + window.scrollY) });
    }
  }

  // 3. Web Animations API
  let running = [];
  try {
    running = document.getAnimations().slice(0, 200).map((a) => {
      const eff = a.effect, tgt = eff && eff.target;
      const t = eff && eff.getTiming ? eff.getTiming() : {};
      return {
        type: a.constructor.name,
        name: a.animationName || a.id || (a.transitionProperty ? `transition:${a.transitionProperty}` : null),
        target: tgt ? cssPath(tgt) : null,
        pseudo: eff && eff.pseudoElement ? eff.pseudoElement : null,
        playState: a.playState,
        duration: t.duration, delay: t.delay, iterations: t.iterations, easing: t.easing, fill: t.fill,
      };
    });
  } catch (e) { /* ignore */ }

  // 4. 滚动显现：两次调用做 diff
  window.__wc = window.__wc || {};
  let scrollReveal = null, phase = "before";
  const before = window.__wc.__animBefore;
  if (!before) {
    window.__wc.__animBefore = candidates;
  } else {
    phase = "after";
    const byPath = new Map(before.map((c) => [c.path, c]));
    scrollReveal = candidates.filter((c) => {
      const b = byPath.get(c.path);
      return b && (b.opacity !== c.opacity || b.transform !== c.transform || b.visibility !== c.visibility || b.classes !== c.classes);
    }).map((c) => {
      const b = byPath.get(c.path);
      const added = c.classes.split(/\s+/).filter((x) => x && !b.classes.split(/\s+/).includes(x));
      return { path: c.path, before: { opacity: b.opacity, transform: b.transform, classes: b.classes }, after: { opacity: c.opacity, transform: c.transform, classes: c.classes }, classesAdded: added, dataAttrs: c.dataAttrs, rectTop: c.rectTop };
    });
  }

  const result = {
    url: location.href,
    phase,
    keyframes,
    animatedElements: animated,
    transitionElements: transitions,
    webAnimations: running,
    revealCandidates: candidates.length,
    scrollReveal,
    prefersReducedMotionRuleCount: (() => { let n = 0; const w = (rules) => { for (const r of Array.from(rules)) { if (r instanceof CSSMediaRule && /prefers-reduced-motion/.test(r.conditionText)) n += r.cssRules.length; else if (r.cssRules) w(r.cssRules); } }; for (const s of Array.from(document.styleSheets)) { try { w(s.cssRules); } catch (e) {} } return n; })(),
  };
  window.__wc.animations = result;
  return JSON.parse(JSON.stringify(result)); // 去掉 undefined 键：与 _read.js 分片 / 脚本路径落盘字节一致
})();
