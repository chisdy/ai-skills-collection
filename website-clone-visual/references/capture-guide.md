# 采集指南：契约目录与内联浏览器操作序列

## 1. 契约目录逐文件说明

`capture/<page-id>/`（`page-id` 由 URL 路径生成：`/` → `index`，`/products.html?category=x` → `products.html--category-x`）

| 文件 | 来源 | 内容 | 主要用途 |
|---|---|---|---|
| `manifest.json` | 脚本 / `save_result.py` | URL、标题、视口、`captureMethod`（`script` / `inline-browser`）、文件清单、告警 | 判断采集是否完整 |
| `dom.html` | `collect/dom.js` | 渲染后的 outerHTML，去 `<script>` 与埋点属性 | 看结构与 class 命名、查文案 |
| `styles.json` + `styles/*.css` | `collect/styles.js` | 每张样式表的索引与 cssText；`mediaQueries`（断点）、`keyframes` 名、`blockedHrefs` | 断点、原始 CSS 参考（不整份复制） |
| `computed.json` / `computed.<w>.json` | `collect/computed.js` | 可见元素 ≈40 个布局 / 排版 / 颜色属性（默认值已剔除）+ `rect`；`path` 为 CSS 路径 | 写区块时查精确值 |
| `tokens.json` | `collect/tokens.js` | `:root` 变量、`@font-face`、颜色 / 字号 / 字重 / 字体 / 间距 / gap / 圆角 / 阴影频次 | 蓝图 §2 |
| `animations.json` | `collect/animations.js` ×2 | `@keyframes` 帧、animation / transition 元素、`getAnimations()`、`scrollReveal`（两次调用 diff） | 蓝图 §7 动画 |
| `hover.json` | 脚本 CDP / 手动 | 带 transition 元素与 a / button 的 hover 前后差异 | hover 态 |
| `libs.json` | `collect/libs.js` | 框架 / 动画库 / CSS 框架 / 图标库 / 建站平台，附证据 | 蓝图 §4、选动画方案 |
| `icons.json` + `icons/*.svg` | `collect/icons.js` | 内联 SVG（hash 去重）、精灵图、icon-font class、小图片；语义线索 | 图标映射 |
| `sections.json` / `sections.<w>.json` | `collect/sections.js` | 一层区块清单：类型猜测、标题、rect、布局模式 / 列数 / gap、padding、背景、内容统计 | 蓝图 §7 区块表、compare 区块对照 |
| `links.json` | `collect/links.js` | 同域链接、主导航、SPA 提示 | `--follow-nav` |
| `assets.json` | `collect/assets.js` | 图片 / 背景图 / 视频 / 字体 / favicon / 样式表 / 脚本 URL | `download_assets.py` |
| `screenshots/<w>.png` | 截图 | 各视口全页截图；`sections/NN-kind.png` 主视口区块裁片 | 观感核对 |

站点级：`capture/site.json`（页面索引）、`capture/assets/`（下载件 + `manifest.json`）、`capture/icons-map.json`、`capture/blueprint.md`。

## 2. 路径 A（脚本）常用参数

```bash
capture_site.py <url> -o capture/                 # 单页三视口
capture_site.py <url> --follow-nav --max-pages 8  # 跟主导航
capture_site.py site-map.json -o capture/         # 用主控 discover_site.py 的清单
--viewports 1920x1080,1024x768,375x812            # 自定义视口，第一个为主视口
--storage-state state.json                        # 登录态（用 playwright codegen --save-storage 生成，或内联浏览器登录后导出）
--wait 2000                                       # SPA 首屏慢时加大
--max-elements 3000                               # 长页面 computed 截断时加大
--no-hover / --no-assets / --no-screenshots       # 加速
```

## 3. 路径 B（内联浏览器）操作序列

两套 MCP 的能力不对等，先按环境选表。共同原则：

- 每个 `collect/*.js` 用 Read 读出全文，作为一段表达式执行（它们是 IIFE，末尾带返回值）。执行后结果也在 `window.__wc[name]`，可以稍后再读。
- 结果 JSON 用 `scripts/save_result.py <name> capture/<page-id> --from-...` 落到契约位置；它会像脚本路径一样展开 `dom.html`、`styles/*.css`、`icons/*.svg` 并维护 `manifest.json`。
- `animations.js` 必须执行两次：滚动前一次、滚到底回顶后一次；第二次返回值里才有 `scrollReveal`。
- 登录 / 验证码：解锁浏览器让用户操作，完成后再继续；不要尝试自动填写验证码。
- 采集只读：不点击提交、下单、评论等写操作按钮；展开菜单 / Tab / 轮播是允许的。

### 3.1 cursor-ide-browser（Cursor 内置）

已在冒烟测试中核对（2026-09）：`Emulation.setDeviceMetricsOverride`、`Emulation.clearDeviceMetricsOverride`、`DOM.enable`、`CSS.enable`、`DOM.getDocument`、`DOM.querySelector`、`CSS.forcePseudoState`、`Runtime.evaluate` 均**可用**；`nodeId` 在多次 `browser_cdp` 调用间**保持有效**（页面导航后失效，需重新 `DOM.getDocument`）。超过 25000 字符的响应自动落到 `~/.cursor/browser-logs/cdp-response-*.json`，结构为 `{"result": {"type", "value"}}`。`Input.*` 被拒；没有 hover / resize 工具。内联浏览器 DPR 为 2，截图像素尺寸是 CSS 像素的两倍。

| 步骤 | 工具 | 参数要点 |
|---|---|---|
| 0 列出 / 锁定 | `browser_tabs` action=list → `browser_lock` action=lock | 采集期间锁定，避免用户操作改变页面状态 |
| 1 打开 | `browser_navigate` url | 不传 `position` |
| 2 设视口 | `browser_cdp` `Emulation.setDeviceMetricsOverride` `{width:1440,height:900,deviceScaleFactor:1,mobile:false}` | 移动视口 `mobile:true`；完事 `Emulation.clearDeviceMetricsOverride` |
| 3 等加载 | `browser_cdp` `Runtime.evaluate` `document.readyState` | 轮询到 `complete` 后再等 800ms（`await new Promise(r=>setTimeout(r,800))` 用 `awaitPromise:true`） |
| 4 滚动前动画快照 | `browser_cdp` `Runtime.evaluate` expression=`animations.js` 全文, `returnByValue:true` | 结果先不存 |
| 5 滚到底回顶 | `browser_scroll` 多次，或 `Runtime.evaluate` 一段 async 滚动脚本 `awaitPromise:true` | 步长 0.8 视口高，每步 200ms |
| 6 滚动后动画 | 同 4 | 这次的返回值存 `animations.json` |
| 7 其余 collect | `Runtime.evaluate` 依次执行 `dom` `styles` `tokens` `libs` `icons` `assets` `links` `computed` `sections` | `computed` / `dom` 一般会落文件；用 `save_result.py --from-cdp <file>` |
| 8 截图 | `browser_take_screenshot` fullPage=true filename=`<w>.png` | 保存在系统临时目录（工具输出里有路径），`save_result.py ... --screenshot <path> --viewport 1440` 复制进契约 |
| 9 hover 采样 | `DOM.enable` → `CSS.enable` → `DOM.getDocument depth 0` → `DOM.querySelector {nodeId, selector}` → `CSS.forcePseudoState {nodeId, forcedPseudoClasses:["hover"]}` → `Runtime.evaluate` 读该元素与子元素的 `getComputedStyle` → `forcePseudoState []` 清除 | 选取 `animations.json.transitionElements` 的 `path` 作为 selector，前后差异手工整理成 `hover.json`：`{method:"cdp:CSS.forcePseudoState", changed:[{path, changes:{prop:[before,after]}}]}` |
| 10 其他视口 | 回到 2，换 768 / 390；只跑 `computed` 与 `sections`，`save_result.py --viewport 768` | |
| 11 跨域样式表 | `styles.json.blockedHrefs` 里的 URL 用 `browser_navigate` 打开，`Runtime.evaluate document.body.innerText` 抄回 `styles/NN-name.css` | 或 `curl -o` |
| 12 素材 | `python3 scripts/download_assets.py capture/` | 无 Python：按 `assets.json` 用 `curl` 循环 |
| 13 解锁 | `browser_lock` action=unlock | |

### 3.2 Playwright MCP（`plugin-playwright-playwright` 等）

有 `browser_resize`、`browser_hover`、`browser_evaluate`、`browser_network_requests`。`browser_evaluate` 接收一个函数字符串；大返回值未必落文件，所以用 `_read.js` 分片。`browser_run_code_unsafe` 是任意代码执行工具，不写进序列。

| 步骤 | 工具 | 参数要点 |
|---|---|---|
| 1 打开 | `browser_navigate` url | |
| 2 设视口 | `browser_resize` width=1440 height=900 | |
| 3 等加载 | `browser_wait_for` time=1 或 text=页面上某段文字 | |
| 4 滚动前动画 | `browser_evaluate` function=`() => { <animations.js 全文> }` | IIFE 直接放在函数体里 `return (…)();` |
| 5 滚动 | `browser_evaluate` 一段 async 滚动函数 | |
| 6 滚动后动画 | 同 4；结果落 `animations.json` | |
| 7 其余 collect | 对每个脚本：`browser_evaluate` 执行（结果已在 `window.__wc[name]`）；若返回被截断，用 `_read.js`：把 `__NAME__` 换成脚本名，`browser_evaluate` 循环 offset 0, 60000, 120000… 直到 `done:true`，每片存一个文件 | `save_result.py <name> <page-dir> --from-chunks c0.json c1.json …` |
| 8 截图 | `browser_take_screenshot` fullPage=true filename=`<w>.png` | |
| 9 hover | `browser_hover` ref/element → `browser_evaluate` 读 computed → 移开再读 | 或同样用 CDP（若该 MCP 暴露） |
| 10 其他视口 | `browser_resize` 后重跑 `computed` / `sections` | |
| 11 网络 | `browser_network_requests` 可辅助确认字体 / 图片 URL 与状态码 | |

### 3.3 手工整理 hover.json 的最小格式

```json
{ "method": "cdp:CSS.forcePseudoState", "sampled": 12, "unchanged": 4,
  "changed": [ { "path": "body > header > nav > a:nth-of-type(2)", "changes": { "color": ["rgb(107, 98, 91)", "rgb(31, 26, 23)"] } } ] }
```

## 4. 采集完整性自检

- `manifest.json.files` 至少包含 `dom.html`、`styles.json`、`computed.json`、`tokens.json`、`animations.json`、`libs.json`、`icons.json`、`sections.json`、`assets.json`、`screenshots/<w>.png`
- `animations.json.phase == "after"`（否则只跑了一次）
- `computed.json.truncated == false`（否则加大上限）
- `styles.json.blockedHrefs` 为空或对应 `styles/` 里已有 fetch 回来的文件
- 多视口：`computed.<w>.json` 与 `sections.<w>.json` 存在
- 两条路径混用时，同名 JSON 的顶层 key 集合应一致（同一批 collect 脚本保证这点）

## 5. 常见问题

- **页面要登录**：路径 B 解锁 → 用户登录 → 继续；或用户登录后用 Playwright MCP / 脚本的 storage state（`playwright codegen --save-storage=state.json <url>`）走路径 A。
- **无限滚动 / 懒加载**：滚动步骤多滚几轮直到高度不再增长；`computed` 上限要相应加大。
- **弹窗 / Cookie 横幅**：先关掉再采，否则会进入 `sections.json` 并遮住截图；关掉的动作记录在 `manifest.warnings`。
- **多语言 / 深色模式**：一个状态一个 `page-id`（如 `index--dark`），在 `manifest` 里注明。
- **反爬 / 403**：路径 B 通常能过（真实浏览器 + 用户在场）；不要尝试伪造 UA / 绕过验证。
