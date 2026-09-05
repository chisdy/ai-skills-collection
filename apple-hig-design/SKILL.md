---
name: apple-hig-design
description: 按 Apple Human Interface Guidelines（HIG）设计、实现与审查 Apple 平台的应用界面，覆盖 iOS / iPadOS / macOS / watchOS / tvOS / visionOS，以及 Liquid Glass、SF Symbols、Dynamic Type、Widgets、App Icon。只要用户在写或改 SwiftUI / UIKit / AppKit 界面代码、讨论 iPhone / iPad / Mac / Apple Watch / Vision Pro 应用的导航、布局、排版、颜色、深色模式、无障碍、Tab Bar / Sidebar / Toolbar、Widget、App Store 审核中的设计问题，或者说"让它更像原生 app"、"符合苹果设计规范"、"HIG 审查"，都应使用此技能——即使用户没有明确提到 HIG。同时适用于给 AI 编码代理撰写 Apple 界面提示词的场景。
metadata:
  version: "1.0.0"
  author: chisdy
---

# Apple HIG Design

帮助你像一个熟悉 Apple 平台的设计师那样工作：先判断平台，再查 HIG 对应章节，用系统组件承载大部分行为，把无障碍当作设计输入而不是上线前的补丁。

## 为什么需要这个技能

Apple 的 HIG 是一本免费的、按平台组织的参考手册，不是要通读的教材。它回答的是"这个平台的用户已经习惯什么"，而模型在没有约束时会倾向于：

- 把设计当装饰：调颜色、加圆角、加渐变，却没有考虑导航是否可预测、主操作是否明显、大字号下是否还能用；
- 用自定义视图重造系统已经提供的控件（自绘 Tab Bar、假玻璃卡片），从而丢掉系统自带的无障碍、平台适配与未来演进；
- 把 iPhone 布局直接搬上 iPad / Mac，或者反过来。

这个技能把 HIG 中真正影响"是否像原生 app"的判断浓缩成一套流程和速查表，细节按需下沉到 `references/`。

## 三条设计原则

自 iOS 26 / macOS Tahoe 起，HIG 用三条原则概括整个设计语言。评估任何界面决策时先过这三条：

| 原则 | 含义 | 判断问题 |
|---|---|---|
| Hierarchy 层级 | 控件与导航构成一个漂浮在内容之上的功能层（下文统称"功能层"）；内容是主角 | 用户第一眼看到的是内容还是一堆控件？ |
| Harmony 和谐 | 软件形状呼应硬件与容器的几何（同心圆角、跟随窗口/屏幕曲率） | 嵌套圆角是否同心？元素是否尊重安全区？ |
| Consistency 一致 | 跨平台共用的模式，让用户不必"学习"你的 app | 返回、Tab、Toolbar 是否像其他 app 一样工作？ |

## 判断工作模式

进入任务前先确定自己在做哪一种事，输出形式不同：

1. **设计 / 实现界面**（写 SwiftUI / UIKit / AppKit，或产出设计方案）→ 走下面的"设计工作流"，先给出结构决策，再给代码。
2. **HIG 审查**（用户给出代码、截图或描述，问"哪里不像原生 / 有什么问题"）→ 走 `references/review-checklist.md`，按模板输出报告，不主动改代码，除非用户要求。
3. **回答具体 HIG 问题**（"Tab Bar 最多几个"、"Liquid Glass 能不能用在卡片上"）→ 直接回答，附上依据；数值优先查本文件的速查表，再查 `references/foundations.md`。

## 设计工作流

### 1. 平台先行

同样的功能，在不同设备上应该长得不一样。先确认目标平台（可能多个），并在回复开头用一句话写出这个平台的关键约束：

- **iOS**：单手或双手握持、拇指可达区在屏幕中下部；限制屏幕上的控件数量，次要操作靠滑动、长按、菜单来发现。
- **iPadOS**：窗口可任意缩放，先为全屏设计、尽量晚地切到紧凑布局；用可转换为 Sidebar 的 Tab Bar（`sidebarAdaptable`）。
- **macOS**：大屏、指针与键盘精确输入；用更少的层级展示更多信息，菜单栏承载全部命令，支持键盘快捷键、窗口自由缩放、Toolbar 个性化；**不支持 Dynamic Type**。
- **watchOS**：单屏、可一眼读完的交互，每次不到一分钟；Complications 与通知常常比 app 本身更重要；导航层级最小化，Digital Crown 用于纵向滚动。
- **tvOS**：焦点驱动，距离 3 米观看；内容避开安全区（上下 60pt、左右 80pt）；不能只靠颜色表示焦点。
- **visionOS**：眼睛看、手指捏，视觉舒适度优先；控件放在 Ornament 而不是塞进窗口；按钮中心间距 ≥ 60pt；颜色要省着用。

平台细节见 `references/platforms.md`。

### 2. 查这个功能对应的 HIG 章节

不要凭印象设计。确定要做的是哪一类东西——导航结构、Toolbar、Widget、Onboarding、设置页、搜索、拖放、模态——然后读 `references/components-patterns.md` 里对应小节。每个小节写明了 HIG 对该模式的核心要求以及常见误用。

### 3. 系统组件优先，自定义要有理由

`TabView`、`NavigationSplitView`、`Toolbar`、`List`、`Form`、`Menu`、`sheet`、`Button` 等系统组件自动获得 Liquid Glass 外观、无障碍支持、Dynamic Type、平台差异化，以及系统未来的演进。自绘一个"看起来像"的控件，意味着你要自己承担交互、动画、对比度、Reduce Motion、平台差异等全部责任。

允许自定义的情形：系统组件确实无法表达你的内容，或品牌表达发生在**内容层**（插画、图片、排版、图表）。功能层坚持系统组件。

给 AI 编码代理下指令时同样如此：写"用原生 `TabView` 做主导航"而不是"把 Tab Bar 做成玻璃的"；写"用 `ConcentricRectangle` 让内框与容器同心"而不是"圆角好看一点"。给出的是架构约束，而不是外观形容词。

### 4. 无障碍从第一稿开始

这些决策会改变布局本身，事后补救成本极高：

- 用系统 text style（`.body`、`.headline`…）而不是固定字号，让 Dynamic Type 生效；在最大无障碍字号下检查是否截断、是否需要改成堆叠布局；
- 触屏上的按钮命中区 ≥ 44×44pt（visionOS 60×60pt），其他控件不低于平台最小尺寸（见速查表），控件之间留足间距（带边框元素周围约 12pt，无边框约 24pt）；
- 文本对比度 ≥ 4.5:1（大字 ≥ 3:1），非文本元素与状态 ≥ 3:1，深浅两种外观都要查；
- 信息不能只靠颜色传达——成功/失败除了红绿还要有图标或文字；
- 每个可交互元素有 VoiceOver 标签，仅图标的按钮尤其要补；
- 响应 Reduce Motion / Reduce Transparency / Increase Contrast，避免自动消失的定时元素。

完整规则与量化表见 `references/foundations.md`。

### 5. 用真实设置验证，而不是只看静态预览

设计完成后列出要测的配置：最大与最小 Dynamic Type、浅色与深色、横竖屏或最小窗口、Reduce Motion / Transparency / Increase Contrast、RTL 语言。如果无法运行，至少在回复里写出"以下配置需要实机验证"，而不是默认它们没问题。

## 速查表（最常被问到的数值）

| 项目 | 值 | 备注 |
|---|---|---|
| 控件尺寸（推荐 / 最小） | iOS / iPadOS 44 / 28pt；watchOS 44 / 28pt；macOS 28 / 20pt；visionOS 60 / 28pt；tvOS 66 / 56pt | 按钮命中区按推荐值取下限（触屏 44pt、visionOS 60pt）；密集界面应更大 |
| 最小文字 / 默认正文 | iOS 11 / 17pt；macOS 10 / 13pt；watchOS 12 / 16pt；visionOS 12 / 17pt；tvOS 23 / 29pt | 细体字要更大 |
| 文本对比度 | 普通文本 4.5:1；大字（≥18pt 或 ≥14pt 粗体）3:1；非文本 3:1 | WCAG AA，Accessibility Inspector 采用 |
| 文本放大支持 | 至少 200%（watchOS 140%） | Dynamic Type 或自定义 |
| 控件周边留白 | 带边框 ≈12pt，无边框 ≈24pt | 减少误触 |
| Tab Bar 项数 | iOS 一般 ≤5；visionOS ≤6 | 更多用 Sidebar 承载 |
| Sidebar 层级 | ≤2 层 | 更深用三栏 Split View |
| watchOS 同排按钮 | 图标按钮 ≤3，文字按钮 ≤2 | |
| tvOS 安全区 | 上下 60pt，左右 80pt | 防过扫描裁切 |
| 清透 Liquid Glass 压暗层 | 底层内容偏亮时加 35% 黑色 | 见 liquid-glass.md |
| 字重 | 避免 Ultralight / Thin / Light | 小字更明显 |
| 图片 | 提供 @2x / @3x；保持原始宽高比 | |

## Liquid Glass 一页纸

Liquid Glass 是 iOS 26 / iPadOS 26 / macOS Tahoe 26 / watchOS 26 / tvOS 26 / visionOS 26 统一的控件材质。最常见的错误是把它当作"到处都能加的视觉效果"。

- **只在功能层**：Tab Bar、Toolbar、Sidebar、Sheet、Popover、浮动按钮。列表、卡片、图片、正文背景用标准材质或普通背景。
- **不要玻璃叠玻璃**：一个玻璃容器里再放玻璃按钮会互相争抢注意力，也会破坏采样模型。多个相邻玻璃元素放进 `GlassEffectContainer`。
- **颜色克制**：默认无色，只给主操作（如 Done）着色，且色放在背景而不是文字；不要因为品牌色是蓝的就把每个控件都染蓝。
- **同心几何**：嵌套的圆角要跟随外层容器，用 `ConcentricRectangle` 而不是硬编码半径。
- **用系统组件就基本不用手写**：标准组件自动获得材质；确有需要再用 `glassEffect()`；`regular` 用于文字多、背景复杂的场景，`clear` 只用于覆盖在照片视频之上。
- **App Icon 用 Icon Composer** 分层制作，支持 default / dark / clear / tinted 四种外观。

细节与 SwiftUI API 见 `references/liquid-glass.md`。

## 输出格式

**设计 / 实现模式**——回复按此顺序组织，让用户先看到决策再看到代码：

1. 目标平台与一句话约束
2. 结构决策：导航模型、用了哪些系统组件、为什么不自定义
3. 代码
4. 无障碍与适配说明（Dynamic Type、深色、Reduce Motion 如何处理）
5. 需实机验证的配置清单

**审查模式**——使用 `references/review-checklist.md` 中的报告模板，按严重度分为「阻塞 / 重要 / 建议」，每条给出 HIG 依据与修法。

## 边界

- HIG 是设计指南，**App Review Guidelines** 是上架审核规则，两者不同。若用户问的是审核被拒（如 4.2 最低功能、4.0 设计），提示他们两者都要对照，本技能只覆盖设计部分。
- 遵循 HIG 不等于所有 app 长得一样。品牌可以在内容层充分表达；要偏离平台惯例时，明确说出理由，而不是默认偏离。
- 数值会随系统版本变化。速查表给出的是当前 HIG 的值，对要求精确到点的场景，提醒用户核对 Apple Design Resources 中对应平台的模板。

## 参考文件索引

| 文件 | 何时读 |
|---|---|
| `references/foundations.md` | 需要布局、排版、颜色、深色模式、无障碍的完整规则或规格表时 |
| `references/liquid-glass.md` | 涉及 Liquid Glass、材质、App Icon、Icon Composer、glassEffect API 时 |
| `references/platforms.md` | 需要某个平台的详细特性、导航惯例、多平台移植时 |
| `references/components-patterns.md` | 设计导航、Toolbar、按钮、Widget、Onboarding、设置、搜索、模态、拖放等具体模式时 |
| `references/review-checklist.md` | 做 HIG 审查、输出审查报告时 |
