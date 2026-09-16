/* collect/_read.js — 分片读取 window.__wc[name]，供 Playwright MCP 的 browser_evaluate 这类"大返回值不落文件"的工具使用。
   用法（把三个参数替换后整段作为表达式执行）：
     ((name, offset, size) => { ... })("computed", 0, 60000)
   返回 { name, total, offset, size, done, chunk }。循环 offset += size 直到 done 为 true，把 chunk 依次拼接后 JSON.parse。
   脚本路径（capture_site.py）不需要这个文件：page.evaluate 一次就能拿完整结果。
   cursor-ide-browser 的 browser_cdp Runtime.evaluate 大响应会自动落文件，通常也不需要。 */
((name, offset, size) => {
  const store = window.__wc || {};
  if (!(name in store)) return { name, error: `window.__wc.${name} 不存在——先执行 collect/${name}.js` };
  if (!store.__json) store.__json = {};
  if (!store.__json[name] || store.__json[name].__src !== store[name]) {
    store.__json[name] = { __src: store[name], text: JSON.stringify(store[name]) };
  }
  const text = store.__json[name].text;
  const chunk = text.slice(offset, offset + size);
  return { name, total: text.length, offset, size: chunk.length, done: offset + size >= text.length, chunk };
})("__NAME__", 0, 60000);
