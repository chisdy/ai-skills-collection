---
name: website-clone-visual
description: 给一个网页 URL，把它的视觉与效果复刻成可运行的前端代码——页面布局、CSS 样式与设计 token、响应式断点、CSS / JS 动画与过渡、滚动显现、hover 态、图标与素材，最后做像素级对比校验。采集用 Playwright 脚本或 Cursor / Codex 的内联浏览器（两条路径共用同一批注入 JS），分析出复刻蓝图，按用户选择的技术栈（静态 HTML/CSS/JS、React 19 + Tailwind v4、Vue 3.5 + Tailwind v4）逐区块实现。只要用户说复刻 / 还原 / 仿照 / 照着做这个页面的样式、布局、动画、交互效果、图标、"做成和这个网站一样"、"像素级还原"、"提取这个站的设计 token / 配色 / 字体"、"这个网站用了什么动画库 / 图标库"、"对比我的复刻和原站差多少"，都应使用此技能——即使用户没有说"复刻"两个字。
metadata:
  version: "1.0.0"
  author: chisdy
---

# Website Clone — Visual

把一个网页的"长什么样、怎么动"变成你自己的前端代码。工作方式是先测量再实现：所有尺寸、颜色、字号、间距、动画参数都来自浏览器里的计算样式与 CSSOM，不凭截图估算；实现完用像素对比证明差距。

本技能只管视觉与效果，产出是前端页面代码。它**不**分析业务功能、**不**写 PRD / 信息架构、**不**推进后端。需要整站功能架构请用 `website-clone-functional`；既要功能又要视觉的完整复刻请用主控 `website-clone`。本技能可以单独安装、单独触发、单独跑完。

## 合规边界（开始前确认）

只服务于：学习 / 练习、重建自己拥有的站点、已获授权的复刻、竞品分析与设计研究。开始前用一句话确认用途；下面情况直接拒绝或缩小范围：

- 用户要把他人的商业站点复刻后上线冒充或直接商用（品牌、Logo、文案、图片原样照搬）
- 需要绕过登录墙、付费墙、验证码、反爬来获取内容——登录只能由用户用自己的账号在内联浏览器里完成
- 目标站 `robots.txt` / 服务条款明确禁止自动化访问且用户不是站点所有者（告知风险，由用户决定）

交付物里要标注版权风险：图片、字体、插画、文案、Logo 是原站资产，蓝图第 6 节的素材清单是标注位置；图标一律换成开源图标库（Lucide / Heroicons / Iconify）的等价符号。

## 最小问卷（缺什么问什么；主控传来的答案不重复问）

1. **URL 与范围**：哪个 / 哪些页面？单页还是跟着主导航多采几页？
2. **视口**：默认 1440 / 768 / 390，有别的要求吗？
3. **技术栈**：静态 HTML/CSS/JS、React 19 + Tailwind v4、Vue 3.5 + Tailwind v4（Vite + pnpm）？每次都问，不默认。
4. **图标库**：Lucide（默认）/ Heroicons / Iconify 任意集，还是保留原站内联 SVG？
5. **动画**：纯 CSS + IntersectionObserver（默认）/ Motion / GSAP？是否复刻交互（下拉、轮播、Tab）还是只做静态观感？
6. **登录态**：页面要登录才能看吗？有的话走内联浏览器路径由用户登录。

## 五步流程

```
1 采集 capture  →  2 分析 blueprint  →  3 选栈  →  4 逐区块复刻  →  5 校验 compare（差异 > 阈值回到 4）
```

### 1. 采集：契约 + 双适配器

采集结果落到一个固定结构的目录（契约），无论用哪条路径采：

```
capture/
  site.json                 页面索引
  assets/                   下载的素材 + manifest.json（download_assets.py）
  icons-map.json            图标映射候选（map_icons.py）
  blueprint.md              复刻蓝图（analyze_capture.py）
  <page-id>/
    manifest.json  dom.html  styles.json  styles/*.css
    computed.json  computed.768.json  computed.390.json     可见元素计算样式 + rect
    tokens.json  animations.json  hover.json  libs.json
    icons.json  icons/*.svg  sections.json  sections.<w>.json
    links.json  assets.json  screenshots/<w>.png  screenshots/sections/*.png
```

页面内提取逻辑全部在 `scripts/collect/*.js`（自包含 IIFE，结果同时写到 `window.__wc[name]` 并返回）：`dom` / `styles` / `computed` / `tokens` / `animations` / `libs` / `icons` / `sections` / `assets` / `links`，以及供 MCP 分片读大结果的 `_read.js`。两条路径注入的是同一批文件，所以产出可以互相补。

**路径选择规则**

| 环境 | 走哪条 |
|---|---|
| 能跑 Python + Playwright | **路径 A** 脚本全量采集（默认） |
| 页面需登录 / 有反爬 / 想边看边采 / 装不上 Playwright | **路径 B** 内联浏览器（`cursor-ide-browser` 或 Playwright MCP），登录与验证码交用户接管 |
| 两者都有 | A 全量 + B 补漏（hover 细节、下拉菜单、轮播中间帧）+ A 做像素对比 |
| 都没有 | `curl` 拿 HTML / CSS + 用户提供截图，明确告知保真度上限 |

**路径 A**

```bash
# 安装（PEP 668：用 venv 或 uv，不要裸 pip）
python3 -m venv /tmp/wc-venv && /tmp/wc-venv/bin/pip install -r scripts/requirements.txt && /tmp/wc-venv/bin/playwright install chromium
# 采集：单页；--follow-nav 跟主导航多页；或传 site-map.json
/tmp/wc-venv/bin/python scripts/capture_site.py <url> -o capture/ [--follow-nav --max-pages 8] [--storage-state state.json]
```

脚本做的事：三个视口分别加载 → 滚动前跑一次 `animations.js` → 自动滚到底再回顶 → 再跑一次 `animations.js`（得到滚动显现 diff）→ 注入其余 collect → CDP `CSS.forcePseudoState` 采 hover 态 → 全页截图与区块裁片 → 跨域样式表 fetch 回本地 → 调 `download_assets.py`。

**路径 B**：按 `references/capture-guide.md` 的操作序列逐步执行（两套 MCP 工具名不同，那里有两张映射表）。要点：视口用 `Emulation.setDeviceMetricsOverride`（cursor-ide-browser 没有 resize 工具）；hover 用 `CSS.forcePseudoState`（没有 hover 工具）；`Runtime.evaluate` 注入每个 `collect/*.js` 的文本，`returnByValue: true`；大结果 cursor-ide-browser 会自动落文件，Playwright MCP 用 `_read.js` 分片；每个结果用 `python3 scripts/save_result.py <name> capture/<page-id> --from-cdp <落盘文件>`（或 `--from-chunks` / `--from-json`）写到契约位置，它会像脚本一样展开 `dom.html` / `styles/` / `icons/` 并把 `manifest.json` 的 `captureMethod` 记为 `inline-browser`。

### 2. 分析：生成蓝图

```bash
python3 scripts/map_icons.py capture/            # 图标 → Lucide / Heroicons 候选（Iconify API；断网只给关键词）
python3 scripts/analyze_capture.py capture/      # → capture/blueprint.md
```

两者仅标准库，内联浏览器路径也能跑。蓝图结构：1 页面清单 → 2 设计 token（`:root` 变量、颜色角色、字体、字号 / 间距阶梯、圆角、阴影）→ 3 断点 → 4 原站技术栈与动画库 → 5 图标清单与映射建议 → 6 素材与版权 → 7 逐页区块表（布局模式、列数、gap、padding、背景、各视口变化、裁片路径）+ 响应式变化 + 动画与 hover → 8 建议的复刻顺序。

**先读蓝图，再按需查原始文件**：写某个区块时按 `path` 去 `computed.json` 查该元素的精确值；`computed.json` 体量大，不要整份读进上下文。

### 3. 选栈

问卷第 3–5 题在这里落定。原站用了什么不等于复刻要用什么：原站 Webflow / WordPress，复刻仍按用户选的栈；原站用 GSAP，简单的入场与滚动显现用 CSS + IntersectionObserver 就够，只有时间线 / 滚动绑定 / SVG 路径动画才建议引入 GSAP 或 Motion（`references/animations.md` 有决策表）。各栈的项目骨架、token 落地方式、组件划分、图标接入在 `references/stack-static.md` / `stack-react.md` / `stack-vue.md`。

### 4. 逐区块复刻

1. **先落 token**：蓝图第 2 节 → CSS 变量（静态 / Vue）或 Tailwind v4 `@theme`（React / Vue + Tailwind）。原站有 `:root` 变量就沿用命名。
2. **断点与容器**：第 3 节 → 媒体查询或 `screens`；容器最大宽度看 `sections.json` 里 hero / 主内容的 `rect.w` 与 `maxWidth`。
3. **字体**：`@font-face` 与字体服务链接照搬（版权见第 6 节；商业字体换开源近似体并告知）。
4. **图标层**：按确认后的 `icons-map.json` 建图标组件 / 引入库；无法映射的内联 `icons/*.svg`。
5. **按第 7 节顺序逐区块**：区块的布局模式、列数、gap、padding、背景来自表格；内部元素的字号、颜色、间距、圆角、阴影按 `path` 查 `computed.json`；图片用 `assets/` 下载件（或占位并标注）。写完一个区块对照一次 `screenshots/sections/NN-*.png`。
6. **响应式**：按各视口的 `sections.<w>.json` / `computed.<w>.json` 差异写媒体查询：列数变化、隐藏元素、字号变化、padding 收缩。
7. **动画**：`@keyframes` 原样搬；transition 按分组写回对应选择器；滚动显现用 IntersectionObserver 切 class（fixture 里叫 `is-visible`，原站叫什么看 `scrollReveal[].classesAdded`）；hover 态照 `hover.json` 的 before/after；全部包在 `@media (prefers-reduced-motion: no-preference)` 里或提供 reduce 分支。
8. **可访问性底线**：语义标签沿用 `sections.json` 的 `tag` / `role`；图标按钮保留 `aria-label`（`icons.json` 里有）；焦点态不丢。

不要做的事：凭截图估尺寸；把原站的 class 名和 CSS 整份复制粘贴（那是抄，不是复刻，且带着死代码）；用 `!important` 硬调；为了像素一致写死像素宽度导致响应式失效。

### 5. 校验

```bash
/tmp/wc-venv/bin/python scripts/compare_pages.py <原站 URL> <本地 URL> -o compare/ [--map pages.json]
```

同视口双截图 → 像素差异 % 与热力图（Pillow）→ 区块 boundingBox 偏差 → 本地 4xx/5xx 资源 → 字体回退。ERROR（差异 > 3%、资源 404、标题字体回退）必须修；WARN（差异 > 1.5%、区块偏差 > 8px）按优先级修。差异集中在哪 100px 带里报告会指出来，回到对应区块。无 Python 时用内联浏览器双截图肉眼比 + 两边各跑一次 `sections.js` 比 `rect`。完整清单在 `references/verify-checklist.md`。

## 速查

| 想知道 | 看哪 |
|---|---|
| 页面有几个区块、每块什么布局 | `blueprint.md` §7 表格 → `sections.json` |
| 某个按钮的精确样式 | `computed.json` 按 `path` 检索（`classes` / `text` 也能搜） |
| 主色 / 字号阶梯 / 间距阶梯 | `blueprint.md` §2 → `tokens.json` |
| 断点 | `blueprint.md` §3 → `styles.json.mediaQueries` |
| 入场 / 滚动 / hover 动画参数 | `blueprint.md` §7 动画小节 → `animations.json` / `hover.json` |
| 原站用了 GSAP / Swiper / Tailwind 吗 | `blueprint.md` §4 → `libs.json` |
| 图标换成哪个 Lucide 名 | `icons-map.json`（`needsReview` 的要人工确认）→ `icons/*.svg` |
| 图片在哪 | `assets/manifest.json`（URL → 本地文件） |
| 原站完整 CSS | `styles/*.css`（只做参考，不整份复制） |
| 差在哪 | `compare/compare-report.md` + `*.diff.png` |

## 常见误判

- **networkidle 超时不是失败**：埋点心跳 / 长轮询会让它永不触发，脚本会降级为 `load` 继续；结果照常可用。
- **滚动显现为 0 不一定没有**：候选元素在首屏就可见时两次快照一样；看 `revealCandidates` 数与 `transitionElements` 里 `opacity, transform` 组，再看 `libs.json` 有没有 AOS / ScrollReveal。
- **`computed.json` 里没有某元素**：不可见（display none、尺寸 0、折叠菜单）或超过 `--max-elements` 截断；前者要先展开再采（路径 B），后者加参数重采。
- **颜色权重最高的是白色 / 黑色**：那是背景和正文，主色看"主色候选"标签和饱和度，不看排名。
- **`icons.json` 里有 `unknown` 字体图标**：class 含 `icon` 的自定义字体，等价符号靠语义线索与截图裁片人工挑。
- **Logo 被映射到图标库**：`map_icons.py` 会把 class 含 `logo` / `brand` 的标成不映射；漏了的手动改回内联 SVG。
- **hover 态没采到**：`hover.json.method` 为 `page.hover` 说明 CDP 不可用，只采到鼠标真实悬停的效果；带 `transition` 但没变化的元素可能靠 JS 切 class，需路径 B 手动看。
- **原站是 SPA 且 `links.json` 只有几个链接**：导航在交互后渲染，加大 `--wait` 或路径 B 手动展开菜单后再采。
- **像素差异大但看起来一样**：先看页面尺寸是否相同（文档高度差 → 某区块 padding / 内容缺失）、字体是否回退（报告里有）、是否有随机内容（轮播 / 时间 / 随机推荐），排除后再对区块。
- **跨域样式表 `blocked`**：脚本会 fetch 回来存 `styles/`；路径 B 里用 `browser_navigate` 打开该 CSS URL 抄回来即可。

## 参考索引

- `references/capture-guide.md`：内联浏览器路径的完整操作序列；cursor-ide-browser 与 Playwright MCP 两张工具映射表；CDP 方法可用性记录；契约目录逐文件说明
- `references/blueprint.md`：蓝图各节怎么读、token 命名规范、区块表字段含义、多页合并规则
- `references/animations.md`：动画分类（入场 / 滚动 / hover / 循环 / 时间线）→ 实现方案决策表；IntersectionObserver 模板；GSAP / Motion 何时值得引入；reduced-motion
- `references/icons.md`：四类图标来源的识别与替换策略；Lucide / Heroicons / Iconify 接入；映射表确认流程
- `references/stack-static.md` / `stack-react.md` / `stack-vue.md`：三种栈的骨架、token 落地、组件划分、图片与字体接入、构建
- `references/verify-checklist.md`：交付前清单与 compare 报告分级处理
- `scripts/`：`capture_site.py`、`download_assets.py`、`analyze_capture.py`、`map_icons.py`、`compare_pages.py`、`save_result.py`（内联浏览器路径落盘助手）、`collect/*.js`、`requirements.txt`
