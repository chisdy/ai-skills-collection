# Changelog

版本号写在 `SKILL.md` 的 `metadata.version`。变更历史与设计决策放这里，不进 `SKILL.md` 正文。

## 1.0.0

首个版本。技能组 `website-clone`（主控）/ `website-clone-visual`（本技能）/ `website-clone-functional` 之一，可独立安装与使用。

### 为什么采集层是"契约 + 双适配器"

模型可能在两种环境里工作：能跑 Python 的终端，或只有 Cursor / Codex 内联浏览器（MCP）的会话。两者各有不可替代之处——脚本能一次性、可重复地采三视口 + 滚动 + hover + 截图；内联浏览器能让用户当场登录、过验证码、展开只有交互后才出现的菜单。如果两条路径各写一套提取逻辑，产出格式会漂移，分析脚本要维护两份解析。因此把"页面里怎么提取"全部收进 `scripts/collect/*.js`（自包含 IIFE，结果既返回又写到 `window.__wc`），Python 用 `page.evaluate` 注入，MCP 用 `Runtime.evaluate` / `browser_evaluate` 注入同一段文本；落盘结构（契约目录）固定，`save_result.py` 让 MCP 路径也能生成与脚本路径完全一致的文件。分析、映射、校验只认契约目录，不关心谁采的。

### 为什么两套 MCP 要分开写操作序列

冒烟测试核对了当前工具清单：`cursor-ide-browser` 没有 hover 和 resize 工具、拒绝 `Input.*` CDP，但允许 `Emulation.setDeviceMetricsOverride` 与 `CSS.forcePseudoState`，且 `nodeId` 跨调用有效、大响应自动落文件；Playwright MCP 有 `browser_resize` / `browser_hover` / `browser_evaluate` 但大返回值未必落文件。能力不对等，写成一张表会让模型在其中一个环境里调用不存在的工具。`_read.js` 分片读取只为 Playwright MCP 存在。

### 为什么 collect 脚本里重复了 `cssPath`

`computed` / `animations` / `sections` / `icons` / `assets` 都要给元素一个稳定的 key，用同一个 `cssPath` 实现。它们必须是自包含文件（MCP 路径逐个注入，没有模块系统），所以每个文件各带一份约 12 行的实现，而不是引一个共享文件。改动时要同步五处——这是有意为之的取舍。

### 为什么 `computed.json` 剔除默认值、限 1500 个元素

一个中等页面有 2–5 千个元素，每个 40 个属性，不剔除默认值的 JSON 会到几十 MB，模型也读不完。剔除默认值、去掉 SVG 内部节点、只采可见元素后通常在 1–3 MB；再由蓝图承担"先读什么"的职责，`computed.json` 只按 `path` 查。`--max-elements` 留给长页面。

### 为什么 hover 用 CDP `CSS.forcePseudoState` 而不是真的移鼠标

真实悬停一次只能采一个元素、要等过渡、还会触发 JS 的 mouseenter 副作用（下拉、Tooltip）；`forcePseudoState` 只改样式匹配，不触发事件，批量采 30 个元素只要几秒。CDP 不可用时降级为 `page.hover`，并在 `hover.json.method` 里标明。

### 为什么滚动显现靠"两次快照 diff"

滚动显现的实现五花八门（AOS、ScrollReveal、手写 IO、GSAP ScrollTrigger），无法从 CSS 静态判断。但它们的共同点是：滚动前后元素的 `opacity` / `transform` / `class` 会变。所以 `animations.js` 第一次调用存快照，第二次调用返回 diff；外层（脚本或 MCP 序列）负责在两次之间滚动。这比识别每个库都可靠。

### 为什么图标一律映射到开源库

原站图标的来源（Font Awesome Pro、定制字体、内联 SVG）往往有授权限制，且复刻不需要与原站字节级一致。Lucide / Heroicons 等覆盖了绝大多数语义；`map_icons.py` 用语义线索 + Iconify 搜索给候选，最终由用户确认。Logo 和插画是例外：不映射、标注版权。

### 为什么 `analyze_capture.py` / `map_icons.py` / `download_assets.py` / `save_result.py` 仅标准库

内联浏览器路径的用户可能装不了 Playwright（PEP 668、公司机器、无网），但分析与映射不需要浏览器。仅标准库保证这条路径能一直走到蓝图；Pillow 只在裁片与像素对比时可选。

### 为什么校验用 `reduced_motion="reduce"` + `animations="disabled"` 截图

否则轮播、浮动动画、入场动画会让两次截图天然不同，像素差异失去意义。代价是动画本身要单独人工核对，`verify-checklist.md` 有清单。

### 为什么本技能不做功能与后端

视觉复刻与功能架构是两种工作：前者的输入是样式与几何，后者的输入是交互与请求。混在一个技能里会让 SKILL.md 超长、问卷混乱。功能由 `website-clone-functional` 负责，完整复刻由 `website-clone` 主控串起来；本技能的 description 只"推"视觉领域的触发词。

### 故意重复的文件

`_common.py` 与 `collect/links.js` 在三个技能里各有一份：`openskills install` 按目录安装，用户可能只装其中一个，任何跨目录引用都会在这种情况下断掉。
