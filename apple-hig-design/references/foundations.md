# Foundations：布局、排版、颜色、无障碍

HIG「Foundations」部分中对实现影响最大的规则与规格。SKILL.md 的速查表是这里的摘要；需要完整依据或规格表时读本文件。

## 目录

1. 布局 Layout
2. 排版 Typography
3. 颜色 Color 与深色模式
4. 无障碍 Accessibility
5. SF Symbols
6. 图片与资源

---

## 1. 布局 Layout

### 通用原则

- **分组**：用留白、背景形状、颜色、材质或分隔线表示关联，但内容与控件必须仍然清晰可辨。
- **重要信息给足空间**：不要让次要细节挤占首屏；次要信息放到窗口其他区域或下一层视图。
- **内容延伸到边缘**：背景、全屏图、可滚动内容都要延伸到屏幕/窗口边界。Sidebar、Tab Bar 等控件漂浮在内容之上而非同一平面，内容不足以铺满时用 `backgroundExtensionEffect()`（UIKit：`UIBackgroundExtensionView`）在控件下方补出内容的延伸感。
- **控件与内容的分界用滚动边缘效果**（scroll edge effect），而不是给控件区加实色背景。
- **阅读顺序决定位置**：最重要的元素靠顶部与前导侧（leading）；注意 RTL 语言会镜像。
- **对齐**表达组织与层级；配合缩进表达信息结构。
- **渐进披露**：集合放不下时要提示还有更多（露出部分项、Disclosure 控件、可滚动暗示）。
- **控件间距**：不相关的控件挤在一起会难以区分，按逻辑分组并留够间隔。

### 自适应

必须处理的变化：屏幕尺寸/分辨率/色彩空间、横竖屏、Dynamic Island 与相机控制、外接显示器 / Display Zoom / iPad 可缩放窗口、Dynamic Type、本地化（RTL、日期数字格式、文本长度）。

- 尊重系统安全区（safe area）与布局参考线（layout guide），用 SwiftUI 或 Auto Layout 让布局跟随 trait 变化。
- 先测最大与最小两种布局，再测中间态。
- 画面比例变化时缩放而非改变素材宽高比。

### 平台布局要点

| 平台 | 要点 |
|---|---|
| iOS | 尽量同时支持横竖屏；避免全宽按钮（要尊重系统边距并与硬件圆角协调）；只有沉浸式体验才隐藏状态栏 |
| iPadOS | 窗口可缩到最小尺寸，为全屏优先设计，尽量晚地切紧凑布局；变窄时优先隐藏第三栏（Inspector）；测试半屏/三分之一/四分之一等系统常用尺寸；考虑可转换 Tab Bar（`sidebarAdaptable`） |
| macOS | 不要把控件或关键信息放窗口底部（用户常把底边拖出屏幕）；避开顶部相机凹槽（`NSPrefersDisplaySafeAreaCompatibilityMode`） |
| tvOS | 布局不会随电视尺寸自动适配，要在多种尺寸上验证；主要内容内缩上下 60pt、左右 80pt；焦点元素放大时不得遮盖重要信息；网格间距一致，半露的离屏内容左右对称 |
| visionOS | 重要内容和控件靠窗口中央；内容不越出窗口边界（系统控件在窗口上下方外侧）；窗口外的控件用 Ornament；可交互元素中心间距 ≥ 60pt |
| watchOS | 内容延伸到屏幕两边，表盘边框就是天然留白；一排最多 3 个图标按钮或 2 个文字按钮；可能给别人看的视图支持自动旋转 |

### Size Class

iOS/iPadOS 用 regular / compact 两种 size class 描述宽高。不要按具体设备型号写死布局，按 size class 与实际可用尺寸响应。

---

## 2. 排版 Typography

### 可读性

- 遵守各平台默认与最小字号（见下表）。细体字要用更大字号。
- **避免 Ultralight / Thin / Light**，优先 Regular / Medium / Semibold / Bold。
- 少用字体家族：混用多种字体会模糊层级、破坏一致性。
- 层级靠字重、字号、颜色的组合表达；字号变化时保持相对层级。
- 响应字号变化时**优先放大用户关心的内容**：Tab 标题不必随正文放大，游戏里对话比伤害数字重要。

| 平台 | 默认正文 | 最小 |
|---|---|---|
| iOS / iPadOS | 17pt | 11pt |
| macOS | 13pt | 10pt |
| tvOS | 29pt | 23pt |
| visionOS | 17pt | 12pt |
| watchOS | 16pt | 12pt |

### 系统字体

- **San Francisco (SF)**：SF Pro（iOS/iPadOS/macOS/tvOS/visionOS）、SF Compact（watchOS）、SF Mono、各语言变体，含 Rounded 变体。
- **New York (NY)**：衬线体，可单独用或与 SF 搭配。
- 通过 `Font.Design.default` / `.serif` / `.rounded` / `.monospaced` 获取，**不要把系统字体嵌进 app**。
- 变量字体自带动态光学尺寸与自动字距，不需手动选 Text/Display。
- SF Symbols 与 SF 字重一一对应，可与文本精确匹配。

### Text Style 与 Dynamic Type

优先使用内建 text style（`.largeTitle` `.title` `.title2` `.title3` `.headline` `.body` `.callout` `.subheadline` `.footnote` `.caption` `.caption2`），它们自动支持 Dynamic Type 与无障碍超大字号。需要时用 symbolic trait 微调（`bold()`、`leading(.tight/.loose)`）；三行以上正文不要用 tight leading。

iOS / iPadOS 默认（Large）规格：

| Style | 字重 | 字号 | 行高 |
|---|---|---|---|
| Large Title | Regular | 34 | 41 |
| Title 1 | Regular | 28 | 34 |
| Title 2 | Regular | 22 | 28 |
| Title 3 | Regular | 20 | 25 |
| Headline | Semibold | 17 | 22 |
| Body | Regular | 17 | 22 |
| Callout | Regular | 16 | 21 |
| Subheadline | Regular | 15 | 20 |
| Footnote | Regular | 13 | 18 |
| Caption 1 | Regular | 12 | 16 |
| Caption 2 | Regular | 11 | 13 |

macOS 内建规格（不支持 Dynamic Type）：Large Title 26 / Title 1 22 / Title 2 17 / Title 3 15 / Headline 13 Bold / Body 13 / Callout 12 / Subheadline 11 / Footnote 10 / Caption 1 10 / Caption 2 10。

支持 Dynamic Type 时要做到：

- 布局在所有字号下都能用——在 设置 > 辅助功能 > 显示与文字大小 > 更大字体 开到最大验证；
- 有意义的图标随字号放大（SF Symbols 自动）；
- 尽量不截断：标签允许多行；可滚动区域里若必须截断，要能进入详情读全文；
- 大字号下考虑改成堆叠布局、减少列数（`isAccessibilityCategory`）；
- 层级不因字号改变而错位：主要元素始终在上方。

### 自定义字体

可以用，但要满足同等可读性与无障碍行为（Dynamic Type、Bold Text）。建议只用在展示性文字上，界面与阅读文本用系统字体。

### 平台差异

- macOS 不支持 Dynamic Type，用动态系统字体变体与标准控件文字一致。
- visionOS 正文与标题字重更粗，新增 Extra Large Title 1/2；优先 2D 文本，最大化与背景对比；点位标签要始终面向用户（billboarding）；不要靠阴影提升对比。
- watchOS Complications 用 SF Compact Rounded。

---

## 3. 颜色 Color 与深色模式

### 原则

- **一种颜色一种含义**：如果品牌色表示"可点"，就不要再拿它装饰不可点的文字。
- 所有颜色在 **浅色、深色、增强对比度** 三种情境下都要成立。自定义颜色要提供 light/dark 变体及高对比变体；即使 app 只支持一种外观也要提供两套，Liquid Glass 的自适应依赖它。
- 在不同光照与设备（True Tone、P3/sRGB、不同电视）下测试。
- 用户选颜色时用系统 `ColorPicker`。
- 半透明元素会改变其后颜色的观感，注意工具栏下方的内容。

### 语义色（Dynamic System Colors）

用途定义而非色值定义。**不要硬编码系统色值**，不要重定义语义（不要拿 separator 色当文字色、secondaryLabel 当背景）。

iOS 背景两套：`systemBackground / secondarySystemBackground / tertiarySystemBackground`（普通视图）与 `systemGroupedBackground / secondary… / tertiary…`（分组表格）。Primary 整体视图、Secondary 组内分组、Tertiary 再下一层。前景：`label / secondaryLabel / tertiaryLabel / quaternaryLabel / link / placeholderText / separator / opaqueSeparator`。

macOS 用户可以改系统强调色；app accent color 只在用户选择"多色"时生效，Sidebar 图标除非指定固定色否则跟随用户强调色。

### 包容性

- 不要只靠颜色区分对象、表示可交互或传递关键信息，同时给文字或形状。
- 红绿、蓝橙组合对色盲用户尤其困难。
- 颜色的文化含义因地区而异。

### Liquid Glass 上的颜色

见 `liquid-glass.md`「颜色」小节。

### 色彩管理

给图片嵌入色彩配置；需要广色域时用 Display P3、16 bit/通道、PNG；必要时在 asset catalog 为 sRGB 与 P3 分别提供资源，避免相近 P3 色在 sRGB 屏上无法区分、渐变被裁切。

### 平台差异

- tvOS：配合 logo 的有限调色板；**不要只用颜色表示焦点**，焦点用缩放与响应动画表示。
- visionOS：颜色省着用，尤其在玻璃上；用在粗体与大面积；沉浸体验里保持亮度均衡，避免在极暗背景上显示闪烁的亮物体。
- watchOS：背景色用于传达信息（Activity 圆环）而非纯装饰；长时间停留的界面避免全屏背景色；Complication 要在 tinted 模式下可用。

---

## 4. 无障碍 Accessibility

好的无障碍界面是 **直觉的**（熟悉一致的交互）、**可感知的**（不依赖单一通道）、**可适应的**（支持系统辅助功能设置）。用 Xcode Accessibility Inspector 审计；App Store 的 Accessibility Nutrition Labels 用来声明支持情况。

### 视觉

- 支持文本放大至少 **200%**（watchOS 140%），首选 Dynamic Type。
- 对比度（WCAG AA，Accessibility Inspector 采用）：

| 文本 | 最小对比度 |
|---|---|
| < 18pt 或 < 14pt 粗体 | 4.5:1 |
| ≥ 18pt 或 ≥ 14pt 粗体 | 3:1 |
| 非文本（图标、控件边界、选中态等） | 3:1 |

  默认达不到时，至少在 Increase Contrast 开启后达到；深浅两种外观都要查。
- 优先系统色，它们自带无障碍变体。
- 信息不能只靠颜色。允许用户自定义图表配色等。
- 为 VoiceOver 描述界面：每个可交互元素有标签，仅图标的按钮尤其要补；装饰性图片标为装饰。

### 听觉

- 音频与视频信息给文字替代：字幕（Captions）、多语言字幕（Subtitles）、音频描述、文稿。
- 音频提示配套触觉反馈；关键音频提示配视觉提示（尤其游戏与空间应用）。

### 行动

- 控件尺寸（HIG 分推荐与最小两档）：

| 平台 | 推荐（默认） | 最小 |
|---|---|---|
| iOS / iPadOS | 44×44pt | 28×28pt |
| macOS | 28×28pt | 20×20pt |
| tvOS | 66×66pt | 56×56pt |
| visionOS | 60×60pt | 28×28pt |
| watchOS | 44×44pt | 28×28pt |

  按钮的命中区按推荐值取下限（HIG Buttons：触屏至少 44×44pt，visionOS 60×60pt）；最小值只适用于确有空间约束的次要控件。
- 间距与尺寸同样重要：带边框元素周围约 12pt，无边框约 24pt。
- 常用操作用最简单的手势；避免自定义多指/双手手势。
- 每个手势都有非手势替代（滑动删除也要有按钮）。
- 支持 Voice Control（元素标签要准）、Siri 与快捷指令、Full Keyboard Access、Switch Control、AssistiveTouch、Pointer Control；不要覆盖系统快捷键。

### 认知

- 交互简单、一致，优先系统手势。
- 少用定时自动消失的元素，优先显式关闭。
- 音视频不自动播放，或至少提供可见的停止控件与全局关闭选项。
- 响应 **Dim Flashing Lights**。
- 响应 **Reduce Motion**：减少自动与重复动画、缩放、Z 轴深度变化、模糊进出；把位移过渡换成淡入淡出；弹簧动画收紧；动画跟随手势。
- 为 **Assistive Access** 优化：识别核心功能、去掉非关键流程、一屏一事、难以撤销的操作二次确认。

### visionOS 舒适度

元素保持在视野内、优先横向布局、别在多处快速切换注意力、减慢外围动画、镜头运动要温和、不要把内容锁在头部、减少大幅重复手势。

---

## 5. SF Symbols

- 数千个符号，与 SF 字体同权重、三种尺度、多种渲染模式（单色、分层 hierarchical、调色板 palette、多色）。
- 随 Dynamic Type 自动缩放，与相邻文本自动对齐。
- 界面图标优先用 SF Symbols；自定义符号用 SF Symbols app 导出模板制作，保持同样的权重与尺度系统。
- Tab Bar 中系统会自动选用 filled 变体。
- 不要用符号表达与其系统语义相悖的操作（例如拿 `trash` 表示"归档"）；符号有明确含义的（如 Apple 服务品牌符号）不得挪用。

---

## 6. 图片与资源

- 所有位图提供 @2x、@3x（Mac 为 @1x、@2x），否则在 Retina 上模糊。
- 始终按原始宽高比显示。
- 可能的话用矢量 PDF/SVG 与 SF Symbols。
- Apple Design Resources 提供各平台的 Figma / Sketch 模板、Dynamic Type 尺寸表、安全区与参考线，精确到点的需求以其为准。
