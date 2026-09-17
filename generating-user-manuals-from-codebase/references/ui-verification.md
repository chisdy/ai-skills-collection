# 界面验证：启动、浏览器工具映射、逐功能验证序列

阶段 2 用；阶段 4 截图也复用这里的工具映射。目标是把 `_inventory.md` 里 `仅代码` 的行尽量变成 `实采`：真实标签、真实状态、真实确认框文案。

## 1. 能不能跑起来

| 看什么 | 启动方式（让用户执行或确认后由 agent 在后台执行） |
|---|---|
| `package.json` `scripts.dev` / `start` | `pnpm dev` / `npm run dev`；端口看输出或 `vite.config` / `next.config` |
| `docker-compose.yml` / `compose.yaml` | `docker compose up -d`；端口看 `ports:` |
| `Makefile` 的 `dev` / `run` | `make dev` |
| Python：`manage.py` / `uvicorn` / `flask run` | 按 README |
| Flutter / 原生移动 | 需要模拟器；内联浏览器不适用 → 让用户提供截图，或 Flutter Web 版跑起来 |
| CLI | 直接在终端跑 `--help` 与各子命令的 `--help`，输出即"界面" |
| 已部署的测试环境 URL | 直接用；**确认是测试环境**后才允许写操作验证 |

跑不起来（依赖缺失、需要内网服务、需要真实密钥）：不硬试超过两次，改为"仅代码"路径，并在大纲里明确标出哪些节没有截图。

**登录**：需要登录的系统由用户自己在内联浏览器 tab 里登录（agent 不输入用户凭据、不绕过验证码 / MFA）。多角色要分别验证时，让用户分别登录或提供测试账号。

## 2. 两条浏览器路径的工具映射

### 2.1 cursor-ide-browser

| 动作 | 工具与参数 | 说明 |
|---|---|---|
| 打开 | `browser_navigate` url | 已有 tab 时先 `browser_tabs` list |
| 锁定 / 解锁 | `browser_lock` `{action: "lock"}` … `{action: "unlock"}` | 多步操作前锁定，本轮结束解锁 |
| 等加载 | `browser_cdp` `Runtime.evaluate` `document.readyState`，轮询到 `complete` | SPA 再用 `browser_snapshot` 看到目标元素再继续 |
| 读标签 / 状态 | `browser_snapshot` | 主要事实来源；记 role / name / 禁用态 / 选中态 |
| 交互 | `browser_click` / `browser_type` / `browser_fill` / `browser_select_option` / `browser_press_key` / `browser_scroll` | 点击前先 snapshot 确认不是写按钮（非测试环境） |
| 定位 | `browser_get_bounding_box` ref；`browser_highlight` ref | 调试用；正式标注用 `annotate.js` |
| 注入脚本 | `browser_cdp` `Runtime.evaluate` `{expression: "<annotate.js 全文>", returnByValue: true}`，然后 `{expression: "window.__annotate({...})", returnByValue: true}` | `Input.*` 被拒，用专用工具做交互 |
| 截图 | `browser_take_screenshot` `{filename: "01-open-import.png", ref: "<CSS 选择器，可选>", type: "png"}` | `ref` 传 CSS 选择器可只截某容器（裁切）；返回值里有实际保存路径，`mv` 到 `docs/manual/assets/<feature-id>/` |
| 视口 | 无直接工具；用 `browser_cdp` `Emulation.setDeviceMetricsOverride` `{width:1280,height:800,deviceScaleFactor:1,mobile:false}` | 若被拒则接受当前视口并在编辑备注记录 |

### 2.2 Playwright MCP

| 动作 | 工具与参数 |
|---|---|
| 打开 / 等待 | `browser_navigate` → `browser_wait_for` `{text: "..."}` 或 `{time: 1}` |
| 读标签 / 状态 | `browser_snapshot` |
| 交互 | `browser_click` / `browser_type` / `browser_fill_form` / `browser_select_option` / `browser_press_key` / `browser_hover` |
| 注入脚本 | `browser_evaluate` `{function: "() => { <annotate.js 全文> }"}`，然后 `{function: "() => window.__annotate({...})"}` |
| 截图 | `browser_take_screenshot` `{filename: "docs/manual/assets/<feature-id>/01-open-import.png", target: "<ref 或选择器，可选>", scale: "css", type: "png"}`（相对路径按工作区根解析，可直接落到目标目录） |
| 视口 | `browser_resize` `{width: 1280, height: 800}` |
| 对话框 | `browser_handle_dialog`（原生 `confirm()` 弹窗时需要；先截图再处理） |

`browser_run_code_unsafe` 不写进序列。

## 3. 逐功能验证序列

对 `_inventory.md` 每一行：

1. **导航到入口**：按清单的入口路径走（点菜单，不直接改 URL——菜单文字本身是要验证的事实）。
2. **snapshot 记入口态**：菜单项文字、页面标题、主要按钮的 name 与禁用态、空状态文案。对照 i18n 结论，不一致以 snapshot 为准并记录。
3. **触发动作**（只读，或测试环境允许）：打开对话框 / 展开表单 / 切换 Tab。
4. **snapshot 记中间态**：对话框标题、字段标签、占位符、校验提示（可故意留空提交一次触发前端校验——这不产生写操作）、确认框原文。
5. **完成或取消**：测试环境完成并 snapshot 结果态（成功提示、列表变化、状态标签）；非测试环境点取消，结果态保持 `仅代码`。
6. **原始帧**（可选）：关键时刻 `browser_take_screenshot` 一张不带标注的图，存 `assets/_raw/<feature-id>/`，供阶段 3 写截图计划时参考；正式带标注的图在阶段 4 按大纲补拍。
7. **回填清单**：入口 / 文案 / 状态 / 限制列改成实采值，`验证状态` → `实采`，证据列追加 `snapshot@<日期>`。

多角色：每个角色至少验证权限矩阵里标 `未知` 的行；被拦时记下用户看到的提示（403 页文案 / 菜单隐藏 / 按钮禁用），这就是"其他读者该怎么办"的证据。

## 4. 零写操作与危险操作

- 非本地、非用户确认的测试环境：不提交任何创建 / 修改 / 删除 / 支付 / 发送 / 邀请。点任何按钮前先 `browser_snapshot` 看它的 name。
- 删除、批量操作、权限变更、支付这类危险动作：只在测试环境验证，且**先截确认框再取消**通常已足够——手册需要的是确认框原文与后果说明，不一定需要真的删掉。
- 表单校验提示可以通过"留空 / 填非法值后点提交"触发，前端拦截时不会产生请求；如果 snapshot 显示提交按钮会直接发请求（无前端校验），非测试环境不点。
- 发生了意外写操作：立刻停止，告知用户发生了什么、在哪，由用户决定清理。

## 5. 没有浏览器时

- 用户提供截图：按截图记标签与状态，证据列写 `截图:<文件名>`，验证状态 `实采（用户截图）`。
- 只有代码：全部 `仅代码`；正文里标签用中性措辞（"打开导入入口"），编辑备注列出所有需要人工核对的标签。
- CLI：`--help` 输出就是界面，直接引用；截图可用终端截图或代码块代替（代码块更好——可复制、可搜索）。

## 6. 完成标准

- `_inventory.md` 每行验证状态不再是空；`实采 / 仅代码 / 待确认` 三者的数量在阶段 3 的确认摘要里汇报。
- 权限矩阵里没有 `未知`，或 `未知` 已进编辑备注。
- 每个将在大纲里配截图的功能，至少有一张原始帧或明确的"阶段 4 补拍"标记。
- 浏览器 tab 已 `browser_lock` unlock。
