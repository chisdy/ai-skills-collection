# 采集指南：features/ 目录与内联浏览器操作序列

## 1. `features/` 目录逐文件说明

| 文件 | 谁写 | 内容 |
|---|---|---|
| `site-map.json` | `crawl_features.py` / `save_page.py` | `pages[]`：url、pageId、type、title、depth、loginWall、forms / lists 数、probes 数；`source: crawl / external / inline-browser` |
| `network.json` | 同上 | API 类请求记录，见 `network-to-api.md` |
| `summary.json` | `crawl_features.py` | 采集参数、页数、类型统计、拦截统计、耗时 |
| `<page-id>/page.json` | 同上 | `collect/features.js` 的输出：`pageType`、`h1`、`headings`、`breadcrumb`、`navigation{main,footerGroups,side}`、`forms[]`、`buttons[]`（kind: submit / write / read / navigate / unknown）、`lists[]`、`tables[]`、`controls{filters,ranges,sorts,searches,paginations,loadMore,tabs,accordions,modals}`、`auth`、`i18n`、`interactions`、`thirdParty`、`jsonLd`、`openGraph`、`entityHints`、`loginWall`、`redirectedToLogin`、`captureMethod` |
| `<page-id>/links.json` | 同上 | `collect/links.js`：同域链接、文本、位置（主导航 / 页脚），用于 BFS 与站点地图 |
| `<page-id>/probes.json` | 同上 | 只读探测记录：动作、触发的请求数、URL 变化 |
| `features.json` | `analyze_features.py` | 功能点 / 实体 / 角色 / 流程 / API / admin 反推 / 假设 |
| `features-summary.md` | 同上 | 上面的 Markdown 摘要，先读这个 |

`page-id` 由 URL 路径与 query 生成（`products.html--category-pendant`），同 URL 不同 hash 视为同页。

## 2. 路径 A（脚本）常用参数

```bash
V=/tmp/wc-venv/bin/python
$V scripts/crawl_features.py <url> -o features/                       # 自带 BFS：默认 20 页、深 3
$V scripts/crawl_features.py site-map.json -o features/               # 用外部页面清单（主控 discover_site.py 或手写）
$V scripts/crawl_features.py <url> -o features/ --max-pages 40 --max-depth 4 --wait 1500
$V scripts/crawl_features.py <url> -o features/ --storage-state state.json --admin-url https://site/admin   # 登录态 + 后台
$V scripts/crawl_features.py <url> -o features/ --no-probe            # 不做只读探测（页面脆弱 / 只想快）
$V scripts/crawl_features.py http://localhost:3000 -o features/ --allow-writes   # 仅自有 / 测试站点
python3 scripts/analyze_features.py features/ [--site-type ecommerce]
```

`storage_state` 的获取：`playwright codegen --save-storage=state.json <url>`，或用户在内联浏览器登录后由模型复制 cookie（**不要**把 state.json 交付或提交）。

外部 `site-map.json` 格式：`{"pages": [{"url": "...", "type": "list"}]}` 或纯 URL 数组；`type` 缺省按 URL 分类。

## 3. 路径 B（内联浏览器）操作序列

三个采集脚本都是自包含 IIFE，返回 JSON 且写到 `window.__wc.features` / `.links` / `.network`。每页三步：注入 → 存文件 → `save_page.py` 落盘。**全程不点任何 write / submit 按钮，不填表单；** 允许的交互只有：滚动、Tab 切换、展开折叠 / 下拉菜单、切换筛选 / 排序、分页、加载更多——且在做这些之前先把默认态采完。

### 3.1 cursor-ide-browser

已核对（2026-09）：`Runtime.evaluate` 可用；> 25000 字符的响应自动落到 `~/.cursor/browser-logs/cdp-response-*.json`，结构 `{"result": {"type", "value"}}`；`Network.*` 中启用类方法可用但响应体获取受限，功能采集用 `collect/network.js`（Performance API）即可。`Input.*` 被拒——用 `browser_click` 等专用工具做只读交互。

| 步 | 工具与参数 | 说明 |
|---|---|---|
| 1 打开 | `browser_navigate` url | 需要登录的站：先让用户在这个 tab 里自己登录，再继续 |
| 2 锁定 | `browser_lock` `{action: "lock"}` | 多步操作前锁定，结束后 unlock |
| 3 等加载 | `browser_cdp` `Runtime.evaluate` `document.readyState`，轮询到 `complete` 再等 800ms | SPA 首屏数据可能更晚，`browser_snapshot` 看到列表再采 |
| 4 滚动 | `browser_scroll` 到底再回顶，或 `Runtime.evaluate` `scrollTo(0, document.body.scrollHeight)` | 触发懒加载 / 无限滚动首批 |
| 5 features | `browser_cdp` `Runtime.evaluate` `{expression: <collect/features.js 全文>, returnByValue: true}` | 一般 20–80 KB，会落文件 |
| 6 links | 同上，`collect/links.js` | |
| 7 network | 同上，`collect/network.js` | 只有 URL，无方法 |
| 8 落盘 | `python3 scripts/save_page.py features/ --page <cdp 文件> --links <cdp 文件> --network <cdp 文件> [--login-wall] [--admin]` | 小结果不落文件时，把 `value` 另存为 JSON 再传（`save_page.py` 两种都认） |
| 9 只读探测（可选） | `browser_click` Tab / 排序 / 分页 → 重跑 `collect/network.js` 看新增的接口 → 手写进 `<page-id>/probes.json` 的 `actions[]` | 探测前用 `browser_snapshot` 确认目标不是写按钮 |
| 10 下一页 | 用 `links.json` 里的主导航链接或 `browser_snapshot` 里的链接重复 1–9 | 每种页面类型（landing / list / detail / auth / checkout / account / legal）至少一页 |
| 11 结束 | `browser_lock` `{action: "unlock"}` → `python3 scripts/analyze_features.py features/` | |

### 3.2 Playwright MCP

有 `browser_evaluate`（接收函数字符串）、`browser_network_requests`（**能给方法与状态**，优先于 `network.js`）、`browser_click` / `browser_select_option`。`browser_evaluate` 大返回值未必落文件——脚本已把结果存到 `window.__wc[name]`，用 `collect/_read.js` 分片：把 `__NAME__` 换成 `features`，循环 offset 0 / 60000 / 120000… 直到 `done: true`，每片存一个文件，`save_page.py --page-chunks c0.json c1.json …`。`browser_run_code_unsafe` 是任意代码执行工具，不写进序列。

| 步 | 工具 |
|---|---|
| 打开 / 等待 | `browser_navigate` → `browser_wait_for` |
| 滚动 | `browser_evaluate` `() => scrollTo(0, document.body.scrollHeight)` → `browser_wait_for` 500ms → 回顶 |
| 注入 | `browser_evaluate` `() => { <features.js 全文> }`（IIFE 已自带 return）；结果小直接存；大则 `_read.js` 分片 |
| 网络 | `browser_network_requests` → 另存 JSON 数组 → `save_page.py --network` |
| 探测 | `browser_click` / `browser_select_option` 后再 `browser_network_requests` 看增量 |

### 3.3 手写 `probes.json` 的最小格式

```json
{"enabled": true, "actions": [{"action": "sort", "detail": "价格从低到高", "requests": 1, "blocked": 0, "urlChanged": true, "urlAfter": "…?sort=price-asc", "requestPaths": ["/api/products"]}]}
```

## 4. 采集完整性自检

- `site-map.json.pages` 覆盖了每种页面类型至少一页；列表与详情都有
- 每个 `page.json` 的 `pageType` 与实际相符（错的手动改 `site-map.json` 的 `type`）
- `network.json` 至少有一条 API 类请求（没有 → 站点是纯静态 / SSR，实体只能靠 DOM，PRD 里说明）
- 脚本路径：`summary.json.network.blocked ≥ 1`（自检 POST 必被拦）且 `network.json.allowWrites == false`
- 登录墙后的页面：`loginWall: true` 的页面数写进 PRD"未覆盖"

## 5. 常见问题

- **只发现 1 页**：SPA 的导航在交互后渲染或链接是 `<button>`；加大 `--wait`，或用内联浏览器展开菜单后把链接手写进 `site-map.json` 再以外部清单跑
- **列表为空、大量 blocked 同域 POST**：读接口用了 POST（GraphQL 等）被拦；见 `network-to-api.md` §2
- **页面类型全是 content**：URL 没有语义（`/p/abc123`）；按 `h1` / `lists` / `forms` 手动改 `site-map.json` 的 `type`
- **只读探测超时**：控件被遮挡或需要 hover 才出现；不影响静态采集，用 `--no-probe` 或内联浏览器手动探
- **反爬 / 验证码**：脚本路径拿到的是挑战页（`textLength` 很小、`h1` 含 verify / 验证）；改内联浏览器路径由用户过验证
