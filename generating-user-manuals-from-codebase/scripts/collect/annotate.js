/**
 * annotate.js — 截图标注覆盖层（自包含 IIFE，无依赖）
 *
 * 注入后暴露 window.__annotate：
 *
 *   window.__annotate({
 *     targets: [
 *       { selector: 'button[aria-label="导入文件"]', kind: 'box' },          // 高亮框
 *       { selector: '#file-input', kind: 'badge', label: '1' },              // 编号角标（自带细框）
 *       { selector: '.sidebar', kind: 'mask' },                              // 半透明遮罩（盖住无关区域）
 *       { selector: 'form', kind: 'box', label: '2', padding: 8 }            // 框 + 角标
 *     ],
 *     color: '#E5484D',      // 可选，默认红；界面红色多时改 '#0B6BCB'
 *     strokeWidth: 3,        // 可选，默认 3px
 *     badgeSize: 26,         // 可选，默认 26px
 *     badgePosition: 'top-right', // 可选：top-right | top-left | bottom-right | bottom-left
 *     dimOthers: false       // 可选：true 时给整页加 35% 遮罩，只露出 box/badge 目标
 *   })
 *   → 返回 { ok: true, applied: 3, missing: ['#not-found'] }
 *
 *   window.__annotate.clear()  → 移除全部覆盖层
 *
 * 设计约束：
 * - 不修改目标元素的样式或 DOM，只在 document.body 末尾追加一个 fixed 定位的容器。
 * - 容器 pointer-events: none，不影响后续交互；截图完必须 clear()。
 * - 位置按 getBoundingClientRect 计算，元素必须在视口内（先滚到可见再注入）。
 * - selector 找到多个元素时只取第一个；用 aria-label / 文本 / data-testid 类选择器，不用随机 class。
 * - 支持文本选择器扩展：selector 以 'text=' 开头时按 innerText 精确匹配可见元素。
 */
(function () {
  var ROOT_ID = '__um_annotate_root';
  var Z = 2147483646;

  function findByText(text) {
    // 文本完全相等的可见元素里取"最深"的那个：只包一个子元素的 <td> / <div> 容器与其子元素文本相同，
    // 按文档顺序会先命中容器，导致框比目标大一圈。
    var nodes = document.querySelectorAll('button, a, [role="button"], [role="menuitem"], [role="tab"], label, h1, h2, h3, h4, span, div, td, th, li, summary');
    var t = text.trim();
    var best = null;
    for (var i = 0; i < nodes.length; i++) {
      var el = nodes[i];
      if (!el.offsetParent && el.tagName !== 'BODY') continue;
      var own = (el.innerText || el.textContent || '').trim();
      if (own !== t) continue;
      if (!best || best.contains(el)) best = el; // 后出现且被当前最佳包含 → 更深
    }
    return best;
  }

  function resolve(selector) {
    if (typeof selector !== 'string') return null;
    if (selector.indexOf('text=') === 0) return findByText(selector.slice(5));
    try { return document.querySelector(selector); } catch (e) { return null; }
  }

  function clear() {
    var old = document.getElementById(ROOT_ID);
    if (old) old.parentNode.removeChild(old);
  }

  function mkRoot() {
    clear();
    var root = document.createElement('div');
    root.id = ROOT_ID;
    root.setAttribute('aria-hidden', 'true');
    root.style.cssText = 'position:fixed;inset:0;pointer-events:none;z-index:' + Z + ';';
    document.body.appendChild(root);
    return root;
  }

  function rectOf(el, pad) {
    var r = el.getBoundingClientRect();
    return { x: r.left - pad, y: r.top - pad, w: r.width + pad * 2, h: r.height + pad * 2 };
  }

  function drawBox(root, rc, color, stroke) {
    var d = document.createElement('div');
    d.style.cssText =
      'position:fixed;box-sizing:border-box;border:' + stroke + 'px solid ' + color +
      ';border-radius:4px;left:' + rc.x + 'px;top:' + rc.y + 'px;width:' + rc.w + 'px;height:' + rc.h + 'px;';
    root.appendChild(d);
  }

  function drawBadge(root, rc, label, color, size, pos) {
    var b = document.createElement('div');
    var half = size / 2;
    var x, y;
    if (pos === 'top-left') { x = rc.x - half; y = rc.y - half; }
    else if (pos === 'bottom-right') { x = rc.x + rc.w - half; y = rc.y + rc.h - half; }
    else if (pos === 'bottom-left') { x = rc.x - half; y = rc.y + rc.h - half; }
    else { x = rc.x + rc.w - half; y = rc.y - half; }
    b.textContent = String(label);
    b.style.cssText =
      'position:fixed;left:' + x + 'px;top:' + y + 'px;width:' + size + 'px;height:' + size + 'px;' +
      'border-radius:50%;background:' + color + ';color:#fff;font:700 ' + Math.round(size * 0.58) + 'px/' + size + 'px ' +
      '-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,"PingFang SC","Microsoft YaHei",sans-serif;' +
      'text-align:center;box-shadow:0 0 0 2px #fff,0 1px 3px rgba(0,0,0,.35);';
    root.appendChild(b);
  }

  function drawMask(root, rc) {
    var m = document.createElement('div');
    m.style.cssText =
      'position:fixed;left:' + rc.x + 'px;top:' + rc.y + 'px;width:' + rc.w + 'px;height:' + rc.h + 'px;' +
      'background:#9a9a9a;border-radius:4px;'; // 不透明：半透明会让下面的文字仍可辨认
    root.appendChild(m);
  }

  function drawDim(root, holes) {
    // 全屏半透明层，用 SVG mask 在每个目标处挖洞（多个洞之间不会产生 polygon 拼接的斜线伪影）。
    var W = window.innerWidth, H = window.innerHeight;
    var NS = 'http://www.w3.org/2000/svg';
    var svg = document.createElementNS(NS, 'svg');
    svg.setAttribute('width', W); svg.setAttribute('height', H);
    svg.setAttribute('viewBox', '0 0 ' + W + ' ' + H);
    svg.style.cssText = 'position:fixed;left:0;top:0;width:' + W + 'px;height:' + H + 'px;';
    var maskId = ROOT_ID + '_mask';
    var defs = document.createElementNS(NS, 'defs');
    var mask = document.createElementNS(NS, 'mask');
    mask.setAttribute('id', maskId);
    var full = document.createElementNS(NS, 'rect');
    full.setAttribute('x', 0); full.setAttribute('y', 0); full.setAttribute('width', W); full.setAttribute('height', H);
    full.setAttribute('fill', '#fff');
    mask.appendChild(full);
    holes.forEach(function (rc) {
      var h = document.createElementNS(NS, 'rect');
      h.setAttribute('x', rc.x); h.setAttribute('y', rc.y); h.setAttribute('width', rc.w); h.setAttribute('height', rc.h);
      h.setAttribute('rx', 4); h.setAttribute('fill', '#000');
      mask.appendChild(h);
    });
    defs.appendChild(mask);
    svg.appendChild(defs);
    var dim = document.createElementNS(NS, 'rect');
    dim.setAttribute('x', 0); dim.setAttribute('y', 0); dim.setAttribute('width', W); dim.setAttribute('height', H);
    dim.setAttribute('fill', 'rgba(0,0,0,.35)');
    dim.setAttribute('mask', 'url(#' + maskId + ')');
    svg.appendChild(dim);
    root.appendChild(svg);
  }

  function annotate(opts) {
    opts = opts || {};
    var color = opts.color || '#E5484D';
    var stroke = typeof opts.strokeWidth === 'number' ? opts.strokeWidth : 3;
    var size = typeof opts.badgeSize === 'number' ? opts.badgeSize : 26;
    var pos = opts.badgePosition || 'top-right';
    var targets = Array.isArray(opts.targets) ? opts.targets : [];
    var root = mkRoot();
    var applied = 0, missing = [], holes = [];

    targets.forEach(function (t) {
      var el = resolve(t.selector);
      if (!el) { missing.push(t.selector); return; }
      var pad = typeof t.padding === 'number' ? t.padding : 4;
      var rc = rectOf(el, pad);
      var kind = t.kind || 'box';
      if (kind === 'mask') { drawMask(root, rc); applied++; return; }
      holes.push(rc);
      if (kind === 'box' || kind === 'badge') drawBox(root, rc, color, kind === 'badge' ? Math.max(1, stroke - 1) : stroke);
      if (t.label != null && t.label !== '') drawBadge(root, rc, t.label, color, size, pos);
      applied++;
    });

    if (opts.dimOthers && holes.length) {
      // 遮罩要在最底层：插到 root 的第一个子节点前
      var dimRoot = document.createElement('div');
      root.insertBefore(dimRoot, root.firstChild);
      drawDim(dimRoot, holes);
    }

    return { ok: missing.length === 0, applied: applied, missing: missing };
  }

  annotate.clear = clear;
  window.__annotate = annotate;
  return { ok: true, version: '1.0.0' };
})();
