---
name: apple-icon-design
description: 按 Apple 官方规范设计、实现与检测 Apple 平台的各类图标——App Icon（Liquid Glass 分层、Icon Composer .icon、六种外观变体、App Store 1024 图、交替图标、tvOS / visionOS image stack、macOS 文档图标）、界面图标（SF Symbols 选型与代码用法、自定义 glyph、自定义 SF Symbol 模板、Tab Bar / Toolbar / 快捷操作尺寸）、状态栏与菜单栏图标（macOS 菜单栏 extra 模板图、iOS 状态栏样式、角标 / Widget / 复杂功能中的图标）。附带脚本可校验 .icon 包与 .appiconset、渲染六种外观、生成小尺寸预览、审计源码中的 SF Symbol 名称与可用性、检查模板图。只要用户提到 app icon / 应用图标 / 图标设计 / 图标规范 / 图标审查、SF Symbols、systemName、菜单栏图标、status item、AppIcon.appiconset、.icon 文件、Icon Composer、ITMS-90717、图标被 App Store 拒、图标在深色或着色模式下难看、图标小尺寸看不清，或者要为 iPhone / iPad / Mac / Apple Watch / Apple TV / Vision Pro 应用产出或检查任何图标资源，都应使用此技能——即使用户没有说"规范"或"HIG"。
metadata:
  version: "1.0.0"
  author: chisdy
---

# Apple Icon Design

帮助你像一个同时懂设计与 Xcode 的图标设计师那样工作：先分清用户要的是哪一类图标，再套用对应规范；把光效、圆角、着色交给系统，把精力放在形状与层次上；每次交付前用脚本和渲染工具证明它在设备上真的可用。

## 为什么需要这个技能

图标是 app 里最容易"看起来差不多、实际全错"的东西。模型在没有约束时倾向于：

- 把 App Icon 当一张画：烘入阴影高光、预切圆角、加文字，结果在 iOS 26 的 Liquid Glass 渲染下光效打架、边缘锯齿，1024 图还因为 alpha 通道被 App Store Connect 拒收（ITMS-90717）；
- 把 SF Symbol 当普通图片：`.resizable().frame()` 丢掉字重与 Dynamic Type，用了不存在或高于部署目标的符号名导致空白，不知道 iOS 16 起默认渲染模式可能不是单色；
- 把 App Icon 缩小塞进菜单栏、把彩色位图当状态图标，深色菜单栏下一团色块或一个实心方块；
- 只看 1024 px 的效果图，从不在 29–40 px、深色壁纸、Clear / Tinted 模式下检查可辨认性。

这个技能把 Apple HIG（App icons、Icons、SF Symbols、Status bars、The menu bar）、Xcode / Icon Composer 文档、SF Symbols 自定义符号规范和社区实践（Bjango 菜单栏 extra、Icon Composer JSON 逆向、Tahoe "icon jail"）浓缩成三类图标的规范 + 一套可执行的检测流程。

## 先分类：三类图标，三套规则

| 类别 | 出现在哪 | 核心规则 | 详细参考 |
|---|---|---|---|
| **App Icon** | 主屏、Dock、App Store、设置、通知 | 分层素材（背景 + ≤4 组前景），满幅方形不预蒙版，效果交给系统；六种外观都要成立 | `references/app-icon.md` |
| **界面图标** | Toolbar、Tab Bar、菜单、按钮、Widget、复杂功能 | 优先 SF Symbols，与文字同重同基线；自定义 glyph 单色矢量、全 app 一致 | `references/interface-icons.md` |
| **状态栏 / 菜单栏图标** | macOS 菜单栏 extra、iOS 状态栏、角标 | 菜单栏 extra 是 ≤22 pt 单色模板图，靠形状表达状态；iOS 状态栏不可放自定义图标 | `references/status-bar-icons.md` |

工程接入（icon.json 结构、Contents.json 模板、交替图标、actool、错误信息对照）在 `references/implementation.md`；审查用 `references/review-checklist.md`。

## 判断工作模式

1. **设计 / 生成图标素材或方案** → 走"设计工作流"：先确定类别与平台，给出结构决策（分几层、用哪个符号、什么尺寸），再产出文件或代码，最后跑检测。
2. **实现 / 接入**（把设计稿放进 Xcode、写 SwiftUI/UIKit 图标代码、配置 .icon / .appiconset、Tauri/Electron 打包） → 查 `references/implementation.md` 对应小节，改完运行脚本验证。
3. **审查 / 检测**（"这个图标有什么问题"、"为什么被拒"、"深色模式下看不清"） → 先跑脚本拿证据，再按 `references/review-checklist.md` 输出分级报告；不主动改素材，除非用户要求。
4. **回答具体问题**（"菜单栏图标多大"、"tinted 变体要不要灰度"） → 直接回答并给依据；数值先查下面的速查表，再查对应 reference。

## 速查表

**App Icon**

| 项 | 值 |
|---|---|
| 画布 | iOS / iPadOS / macOS 1024×1024 方形；watchOS 1088（Icon Composer）/ 1024（资产目录）；tvOS 800×480（App Store 1280×768）；visionOS 1024 ×3 层 |
| 蒙版 | 系统施加：iOS / iPadOS / macOS squircle，watchOS / visionOS 圆形，tvOS 圆角矩形。**素材不预切** |
| 分层 | Icon Composer：≤4 group × 1–4 layer；tvOS 2–5 层；visionOS ≤3 层 |
| 外观 | Default / Dark / Clear Light / Clear Dark / Tinted Light / Tinted Dark；资产目录方式 dark 用透明背景、tinted 用灰度 |
| App Store 1024 | PNG、不透明、**无 alpha**、sRGB / P3 带配置文件 |
| macOS 资产目录 | 16 / 32 / 128 / 256 / 512 pt × @1x @2x 共 10 张，缺一不可；Tahoe 上只有 .icns 的 app 会进灰色容器 |
| 禁止 | SF Symbols、Apple 硬件、截图 / UI 控件、说明性文字、照片、模仿他人 |
| 自动缩放尺寸 | 设置 29 pt、Spotlight 40 pt、通知 20 pt、主屏 60 pt——在 29–40 px 自检 |

**界面图标**

| 项 | 值 |
|---|---|
| 选型顺序 | 系统 SF Symbol → 自定义 SF Symbol（模板改绘）→ 矢量 glyph（PDF/SVG）→ 位图（@1x @2x @3x） |
| 大小 | SwiftUI `.font(textStyle)` + `.imageScale`；UIKit `SymbolConfiguration(textStyle:)`；不用 `.resizable()` / 固定 frame |
| 渲染模式 | Monochrome / Hierarchical / Palette / Multicolor；iOS 16+ 未指定时可能非单色，需要单色请显式声明 |
| 变体 | Tab Bar 用 fill、Toolbar 用无边框 outline（不用 `xxx.circle`）；容器大多自动决定 |
| Tab Bar glyph | 常规圆形 25 / 方形 23 pt；紧凑 18 / 17 pt |
| Toolbar glyph | 约 24 pt，命中区 ≥ 28 pt |
| 快捷操作 | 35×35 pt 单色模板 |
| 无障碍 | 仅图标控件必须有 label；对比 ≥ 3:1；装饰图隐藏；动画响应 Reduce Motion |

**菜单栏 extra（macOS）**

| 项 | 值 |
|---|---|
| 尺寸 | 工作区高 22 pt（菜单栏 24 pt）；图形约 16–18 pt |
| 格式 | 模板图（`isTemplate` / Render As Template）：黑 + 透明，PNG @1x @2x 或矢量 |
| 状态 | 换符号变体（`wifi` / `wifi.slash`）或不透明度，不用颜色、不闪烁 |
| 行为 | 点击出菜单（非 popover）；用户可在设置关闭；被隐藏时功能另有入口 |
| iOS 状态栏 | 不能放自定义图标；只能选深浅样式、全屏媒体时临时隐藏、下方内容加模糊层 |

## 设计工作流

1. **确认类别、平台与最低系统版本**。这决定用 Icon Composer 还是资产目录、能用哪一年的 SF Symbols、是否需要 @3x 位图。缺信息时按 Xcode 26+ / iOS 26 目标处理，并说明假设。
2. **App Icon：先定概念再分层**。一个能代表 app 本质的元素、少量实心可重叠形状、实色或渐变背景。写出图层清单（底→顶）和每层的颜色 / 不透明度意图，再产出 SVG（文字转轮廓、无阴影高光、不蒙版）。用 `.icon` 交付：`icon.json` 结构见 `references/implementation.md` 第 1 节。同时说明单色模式下哪个元素设为白色。
3. **界面图标：先查有没有现成符号**。用 SF Symbols app 或标准动作表（`references/interface-icons.md` 第 7 节）找系统符号；只有确实没有时才自定义，且从相似符号导出模板改绘以保持权重一致。代码里用 `Label` / `.font` / `symbolRenderingMode`，给仅图标控件加 `accessibilityLabel`。
4. **菜单栏图标：从 SF Symbol 出发**。16–18 pt 的单色形状，`MenuBarExtra` 或 `NSStatusItem` + `isTemplate = true`，用符号变体表达状态。
5. **交付前检测**（见下节），把脚本输出与渲染图一起交给用户，并列出需要实机确认的项。

## 检测流程

脚本在 `scripts/`，仅依赖标准库，装 Pillow 后启用像素级检查；退出码 1 表示存在阻塞问题。运行方式和更多选项见 `references/implementation.md` 第 7–8 节。

```bash
S=<本技能目录>/scripts
# App Icon 结构与素材（.icon / .appiconset / 1024 PNG）；--render 用 Xcode 自带 ictool 渲染六种外观
python3 $S/check_app_icon.py AppIcon.icon --render build/renders
# 效果预览：squircle / 圆形蒙版 × 29–180 px × 浅 / 深 / 复杂壁纸 × tinted 模拟
python3 $S/preview_icon_sizes.py AppIcon.icon -o build/preview.png
# SF Symbols 用法审计：名称存在、旧别名、最低系统版本、受限符号、.resizable()、仅图标按钮
python3 $S/check_symbols.py Sources/ --min-ios 17.0 --min-macos 14.0
# 模板图：菜单栏 / 快捷操作 / Tab Bar / Toolbar / 复杂功能
python3 $S/check_template_images.py Assets.xcassets --kind menubar --filter "MenuBar|Status"
```

读结果时：`[ERROR]` 会被拒、不显示或打不开；`[WARN]` 明显偏离规范；`[INFO]` 是建议或需人工确认。渲染出的 PNG 一定要打开看：脚本判断不了"Clear 模式下前景还认得出来吗"，你要用眼睛判断，并把结论写给用户。

## 交付格式

- **设计方案**：先给结构（类别、平台、图层 / 符号选择、尺寸、外观策略），再给文件（SVG / icon.json / Contents.json / 代码），最后给检测结果与实机验证清单。
- **审查报告**：按 `references/review-checklist.md` 的模板输出——范围、总体判断、阻塞 / 重要 / 建议三级发现（每条含现状、依据、修法）、通过项、需实机验证项。
- **具体问答**：先给答案和数值，再给一句依据（HIG 哪一节 / Xcode 哪个行为），需要时附代码或命令。

## 常见误判

- "把 1024 图切好圆角再交" —— 系统会再蒙一次；四角透明还会触发 ITMS-90717。交满幅方形。
- "深色变体就是把背景改黑" —— 资产目录方式下深色变体应透明背景，系统提供深色底；Icon Composer 里则按外观 Vary 颜色。
- "tinted 变体随便给一张" —— 系统只用亮度，要给灰度图，且最醒目元素应为白色。
- "SF Symbol 可以做 app icon 的一部分" —— 许可禁止，包括混淆性相似。
- "`Image(systemName:)` 渲染空白是 SwiftUI bug" —— 几乎总是符号名不存在或高于部署目标，跑 `check_symbols.py`。
- "菜单栏图标用彩色更醒目" —— 深色菜单栏、选中态、Reduce Transparency 下都要自己适配；模板图免费获得这些。
- "Tahoe 上图标变小有灰底是系统 bug" —— 是只提供了 .icns / 异形轮廓；提供 .icon 或 Assets.car。
- "iOS 能放自定义状态栏图标" —— 不能；用户说的可能是 macOS 菜单栏 extra 或 Live Activity。

## 参考文件

| 文件 | 何时读 |
|---|---|
| `references/app-icon.md` | 设计或审查 App Icon：分层模型、六种外观、规格表、Icon Composer 工作流、迁移、被拒原因、文档图标 |
| `references/interface-icons.md` | 界面图标：SF Symbols 概念与代码、自定义 glyph 规则、自定义 SF Symbol 模板、尺寸表、标准动作符号、RTL、无障碍 |
| `references/status-bar-icons.md` | 菜单栏 extra 设计与实现、iOS 状态栏、角标 / Widget / 复杂功能图标 |
| `references/implementation.md` | icon.json 与 Contents.json 结构、交替图标、非 Xcode 工具链、脚本与 Apple 命令行工具用法、错误信息对照 |
| `references/review-checklist.md` | 审查步骤、分级标准、七类清单、报告模板 |

相关技能：界面整体的 HIG 审查（导航、布局、Liquid Glass 控件层）用 `apple-hig-design`；本技能只负责图标。
