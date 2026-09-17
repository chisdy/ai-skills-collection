# 截图与标注规范

阶段 4 用。目标：读者一眼找到该点哪里、该看哪里；不多截、不乱标、不泄露数据。工具映射见 `ui-verification.md` §2。

## 1. 何时截

截：

- 动作位置不显然（藏在菜单里、图标按钮、右键、悬停才出现）。
- 界面状态需要确认（成功提示长什么样、状态标签怎么显示、空状态）。
- 结果需要对照（导出后列表变化、权限不足时看到什么）。
- 产品概览页：一张主界面区域图，编号标出主要区域。

不截：

- 纯文字能说清的步骤（"点击右上角的 **保存**"）。
- 每一步都截——多步流程只截 **2–4 个关键帧**：入口、关键动作（通常是确认框或表单）、结果。
- 登录页、加载动画、与任务无关的页面。

## 2. 怎么截

| 项 | 规则 |
|---|---|
| 视口 | 桌面默认 1280×800；移动端按设备预设（375×812 等）。全书一致。 |
| 裁切 | 贴近目标但保留定位上下文——至少能看出在哪个页面 / 面板。优先用元素截图（`ref` / `target` 传容器选择器）而不是全页再手裁；对话框直接截对话框本身。 |
| 主题 | 统一浅色；系统跟随暗色时先切浅色。 |
| 数据 | 演示数据、脱敏；不出现真实姓名 / 邮箱 / 手机 / 密钥 / token / 内部 URL / 客户内容。先看 snapshot，有真实数据就用 `mask` 遮住或换数据。 |
| 光标 | 不含鼠标指针、不含 tooltip（除非 tooltip 就是要说明的内容）。 |
| 语言 | 界面语言与手册输出语言一致。 |
| 顺序 | Markdown 里文字在前、图在后；两张图之间必有文字。 |

## 3. 标注决策树

```
要指的东西是什么？
├─ 一个元素（按钮 / 输入框 / 菜单项）           → box（高亮框，紧贴元素，padding 4）
├─ 两个以上要按顺序操作的元素（同一张图内）       → badge（编号角标 1、2、3…按阅读顺序），每个自带细框
├─ 一片区域（面板 / 表格 / 侧栏）               → box，padding 8
├─ 要把注意力集中到局部                          → dimOthers: true（整页压暗，只露目标）
└─ 要盖住无关或敏感内容                          → mask
```

- 单图标注 **≤ 4**；超过就拆成两步、两张图。
- 编号角标位置全书一致：默认框外右上角；界面右上角被遮时改左上角，并在该功能内保持一致。
- 一套颜色：默认红 `#E5484D`；界面本身红色多（危险按钮、错误态）时改蓝 `#0B6BCB`，并在 `_outline.md` 头部记下本书用色。
- 一种线宽（3px）、一种角标样式。不画箭头、不加文字标签——需要解释的用正文与 alt。
- 标注只指"这一步要做的事"，不指"顺便看看的东西"。

## 4. 操作序列

每张正式截图：

1. 走到该步的界面状态（按 `ui-verification.md` §3 的序列，滚到目标可见）。
2. `browser_snapshot` 拿到目标的 role / name，据此写选择器：优先 `[aria-label="…"]`、`text=按钮原文`、`[data-testid="…"]`、稳定 `id`；不用随机 class、不用第 N 个子元素。
3. 注入 `scripts/collect/annotate.js` 全文（每个页面只需一次，导航后要重注入）。
4. 调用 `window.__annotate({ targets: [...], color, dimOthers })`；检查返回值 `missing` 为空，否则修选择器重试一次。
5. `browser_take_screenshot`：
   - cursor-ide-browser：`{filename: "<nn>-<step-slug>.png", ref: "<容器选择器，可选>"}`，然后按返回的实际路径 `mv` 到 `docs/manual/assets/<feature-id>/`。
   - Playwright MCP：`{filename: "docs/manual/assets/<feature-id>/<nn>-<step-slug>.png", target: "<ref 或选择器，可选>", scale: "css"}`。
6. `window.__annotate.clear()`。
7. 在正文里引用，并在 `_inventory.md` 该功能的证据列追加 `截图:<路径>@<日期>`。

原生 `confirm()` / `alert()` 弹窗截不到 DOM 标注——Playwright 路径用 `browser_handle_dialog` 前先截；cursor-ide-browser 路径记下弹窗文案，正文用引用块代替截图。

已核对（2026-09，cursor-ide-browser）：

- `browser_take_screenshot` 的 `filename` 只是文件名，实际落在系统临时目录（返回值 `Saved to:` 给出完整路径），要 `mv` 到 `docs/manual/assets/`。
- 多个 tab 时 `Runtime.evaluate` 与 `browser_take_screenshot` 都要传 `viewId`，否则可能作用到另一个 tab。
- `browser_navigate` 是整页加载，会丢失已注入的 `__annotate`；hash 变化（`location.hash = …`）不会。注入前先 `typeof window.__annotate === 'function'` 判断。
- 表格单元格这类没有稳定选择器的目标：先用 `Runtime.evaluate` 给它们临时加 `id`（如 `email-0`），再用 `#email-0` 做 `mask` 目标；截完 `clear()` 即可，临时 id 不影响页面。
- `mask` 是不透明色块（半透明会让下面的文字仍可辨认）；`dimOthers` 用 SVG mask 挖洞，多个目标之间不会有拼接伪影。
- 元素截图（`ref: ".modal"`）会按元素实际尺寸裁切，是对话框类截图的首选；内容区这类高度撑满视口的容器仍会截出大片空白，改截更内层的元素（`.table`）。

## 5. 命名与引用

- 路径：`docs/manual/assets/<feature-id>/<nn>-<step-slug>.png`，`nn` 两位序号，`step-slug` 英文小写短横线（`01-open-import-dialog.png`）。原始帧放 `assets/_raw/`，不被正文引用。
- 引用：

  ```markdown
  2. 点击 **导入文件**。
     ![导入对话框，文件选择区域已高亮](assets/orders-import/02-import-dialog.png)
  ```

- alt 规则：描述界面状态 + 被标注的动作 / 元素；≤ 155 字；不用"截图""图片"二字；同一元素多次出现用同样的措辞。装饰性图（几乎不该有）才用空 alt。
- 图下可选一行说明（斜体），用于补充 alt 放不下的信息（如"仅管理员可见此按钮"）。
- 更新手册时：界面变了就重截并覆盖同名文件，`_inventory.md` 里的日期更新；不要新增 `-v2` 文件。

## 6. 截图自检（阶段 5）

- [ ] 每张图正文里有且只有一处引用；引用路径存在。
- [ ] 每张图 alt 非空、描述状态与动作、不含"截图"二字。
- [ ] 一图一焦点；标注 ≤ 4；编号顺序与正文步骤顺序一致。
- [ ] 无真实用户数据、密钥、内部 URL、真实客户内容；有疑问的已 `mask`。
- [ ] 视口、主题、用色、角标位置全书一致。
- [ ] 多步流程 2–4 帧，无连续两张图之间缺文字。
- [ ] `_raw/` 不被引用；`_inventory.md` 证据列有截图路径与日期。
