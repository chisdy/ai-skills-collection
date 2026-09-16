/* collect/network.js — 内联浏览器路径的网络请求补充采集（只读）。
   脚本路径用 Playwright 的 page.on("response") 记录 XHR / fetch；内联浏览器没有这个钩子，
   这里用 Performance API 读出本页已发生的 xhr / fetch / 文档请求：URL、发起类型、耗时、传输字节。
   局限：拿不到 HTTP 方法、请求体与响应内容（方法按 GET 记，analyze_features.py 会标 methodUnknown）。
   Playwright MCP 有 browser_network_requests 时优先用它（能拿方法与状态）。
   结果写到 window.__wc.network 并返回。 */
(() => {
  const abs = (u) => { try { return new URL(u, location.href).href; } catch (e) { return u; } };
  const entries = performance.getEntriesByType("resource").filter((e) => /^(xmlhttprequest|fetch|beacon|other)$/.test(e.initiatorType) || /\.json(\?|$)|\/api\/|\/graphql|\/v\d+\//.test(e.name));
  const seen = new Set();
  const out = [];
  for (const e of entries) {
    if (seen.has(e.name)) continue;
    seen.add(e.name);
    let u; try { u = new URL(e.name); } catch (x) { continue; }
    out.push({
      url: e.name, host: u.hostname, path: u.pathname, queryKeys: Array.from(new Set(Array.from(u.searchParams.keys()))).sort(),
      initiator: e.initiatorType, sameSite: u.hostname.replace(/^www\./, "") === location.hostname.replace(/^www\./, ""),
      durationMs: Math.round(e.duration), transferBytes: e.transferSize || null, status: e.responseStatus || null,
    });
  }
  const result = { url: location.href, page: abs(location.pathname + location.search), count: out.length, entries: out, methodKnown: false, note: "Performance API：无请求方法 / 请求体 / 响应内容；写请求（POST 等）若发生也会出现在这里但无法区分" };
  window.__wc = window.__wc || {};
  window.__wc.network = result;
  return JSON.parse(JSON.stringify(result)); // 去掉 undefined 键：与 _read.js 分片 / 脚本路径落盘字节一致
})();
