# 状态栏图标：macOS 菜单栏 Extra、iOS 状态栏与其它"状态类"图标

用户说"状态栏图标"时通常指三种不同的东西，先分清再动手：

| 用户可能指的 | 平台 | 你能做什么 |
|---|---|---|
| 菜单栏右侧常驻的小图标（Wi-Fi、电池旁边那种） | macOS | **菜单栏 extra**（`NSStatusItem` / SwiftUI `MenuBarExtra`）。可以放自定义模板图标，这是本文件的主体 |
| 屏幕顶部的时间、信号、电量条 | iOS / iPadOS | 系统区域，**app 不能放自定义图标**；只能选深浅样式、临时隐藏、保证下方内容不干扰可读性 |
| App 图标上的红色数字、Dock 图标角标、Widget/复杂功能里的小图标 | 全平台 | 角标由系统绘制；Widget / 复杂功能中的图标遵循界面图标规则并要在 tinted 模式下可读 |

## 目录

1. macOS 菜单栏 extra：设计规范
2. macOS 菜单栏 extra：状态表达与动态图标
3. macOS 菜单栏 extra：实现
4. iOS / iPadOS 状态栏
5. 角标、Dock、Widget 与复杂功能中的状态图标
6. 自检清单

---

## 1. macOS 菜单栏 extra：设计规范

HIG 要点（The menu bar > Menu bar extras）：

- **用符号表示**：可以自绘界面图标，也可以直接用 SF Symbol（原样或定制）。图标以"黑色 + 透明"定义形状，由系统上色，从而在浅色/深色菜单栏与选中态下都好看。**菜单栏高 24 pt**（HIG 数值）。
- **点击显示菜单，而不是 popover**：除非功能复杂到菜单放不下。
- **让用户决定是否显示**：通常在设置窗口里提供开关；首次设置时可以顺便询问。
- **不要依赖它的存在**：空间不够时系统会隐藏 extra，用户也可能关掉；同样的功能要有别的入口（Dock 菜单、主窗口、菜单栏命令）。
- 图标只表达"这个 app 在这里 + 当前状态"，不要塞文字说明。

尺寸与形式（Bjango《Designing macOS menu bar extras》等社区总结，HIG 未给出的部分）：

| 项 | 值 |
|---|---|
| 菜单栏 extra 工作区高度 | 固定 **22 pt**，素材不能更高（菜单栏本身 24 pt；带摄像头凹槽的 MacBook Pro 菜单栏更高，但 extra 区域不变） |
| 与系统图标视觉重量一致的图形尺寸 | 圆形约 **16×16 pt**；一般 16–18 pt |
| 边距 | 通常不加 padding，除非用于垂直居中；系统按 `NSStatusItem.squareLength`（= 菜单栏高）或 `variableLength` 排布 |
| 格式 | 单个 SVG / PDF（开 preserves vector），或 PNG @1x + @2x；也可代码绘制（日历日期、时钟等动态内容） |
| 颜色 | **模板图**（monochrome，`isTemplate = true` / 资产目录 Render As: Template）：系统忽略颜色只用 alpha，自动适配浅/深色菜单栏、选中态高亮与 Reduce Transparency 下的灰色菜单栏。全彩图标需要有明确理由（品牌可识别性通常不是），且要自己处理两种菜单栏 |
| 层次 | 模板图里用不透明度分级表达状态（音量、信号）；Apple 用约 35% 不透明度表示禁用/关闭 |
| 笔画 | 与系统菜单栏符号一致：中等粗细、清晰、无细节；SF Symbols 的 Regular / Medium 权重最接近 |

不要做的事：

- 把 App Icon 缩小当菜单栏图标（有材质、有颜色、有圆角，缩到 16 pt 是一团色块）。
- 用 22 pt 以上的素材"让它更显眼"；会被裁切或缩放。
- 用 emoji 或彩色位图充当状态图标。
- 在图标里放文字说明；要显示数值（下载速度、温度）用 `button.title` 与图标并列，并考虑 `variableLength` 与等宽数字。
- 闪烁或持续动画：菜单栏在用户视野边缘，动画会持续分散注意力；状态变化用一次性的符号替换（`symbolEffect(.replace)`）或形状差异表达。

## 2. macOS 菜单栏 extra：状态表达与动态图标

- **二态**（开/关、连接/断开）：换符号变体而不是换颜色——`record.circle` / `record.circle.fill`、`wifi` / `wifi.slash`、`bell` / `bell.slash`。模板图本来就只有一种颜色。
- **多级量**（电量、信号、进度）：SF Symbols 的 variable color（`NSImage(systemSymbolName:variableValue:accessibilityDescription:)`）或自绘多档模板图。
- **需要引起注意**：短暂的 badge 变体（`xxx.badge.exclamationmark`）、一次 bounce；不要常驻红点闪烁。
- **文字与图标并列**：`button.title` / `button.imagePosition = .imageLeading`；数字用等宽变体，避免宽度抖动。
- **动态绘制**（日期、时钟）：用 `NSImage(size:flipped:drawingHandler:)` 在 18×18 pt 画布上绘制，然后 `isTemplate = true`。
- 每次状态变化同时更新 `accessibilityDescription` / `toolTip`。

## 3. macOS 菜单栏 extra：实现

SwiftUI（macOS 13+）：

```swift
@main
struct StatusApp: App {
    @AppStorage("showMenuBarExtra") private var showMenuBarExtra = true   // 让用户决定
    @State private var isRecording = false

    var body: some Scene {
        MenuBarExtra(isInserted: $showMenuBarExtra) {
            Button(isRecording ? "停止录制" : "开始录制") { isRecording.toggle() }
                .keyboardShortcut("r")
            Divider()
            if #available(macOS 14, *) {
                SettingsLink()                       // macOS 14+ 才有
            } else {
                Button("设置…") {                    // macOS 13：用 AppKit 的标准选择器打开 Settings 场景
                    NSApp.sendAction(Selector(("showSettingsWindow:")), to: nil, from: nil)
                }
            }
            Button("退出") { NSApp.terminate(nil) }
        } label: {
            // 系统符号自动作为模板图渲染，跟随浅/深色菜单栏
            Image(systemName: isRecording ? "record.circle.fill" : "record.circle")
                .accessibilityLabel(isRecording ? "正在录制" : "未在录制")
        }
        .menuBarExtraStyle(.menu)   // HIG：优先菜单；.window 仅在内容确实复杂时使用

        Settings { SettingsView() }
    }
}
```

自定义模板图：资产目录 imageset 的 Attributes 里 **Render As: Template Image**（Contents.json `"template-rendering-intent" : "template"`），矢量图开 **Preserve Vector Data**；然后 `Image("MenuBarIcon")`。

AppKit：

```swift
let item = NSStatusBar.system.statusItem(withLength: NSStatusItem.squareLength) // 方形图标；带文字用 .variableLength
if let button = item.button {
    let image = NSImage(named: "MenuBarIcon")          // 或 NSImage(systemSymbolName:accessibilityDescription:)
    image?.isTemplate = true                            // 关键：让系统上色
    button.image = image
    button.imagePosition = .imageOnly
    button.toolTip = "MyApp"
    button.setAccessibilityLabel("MyApp 状态")
}
item.menu = menu                                        // 点击显示菜单；不要默认 popover
```

Info.plist：仅菜单栏、不显示 Dock 图标的 agent 应用设 `LSUIElement = YES`（Application is agent）。这类 app 更要保证 extra 被隐藏时有其它入口（如 Spotlight 打开设置窗口）。

验证：浅色 / 深色菜单栏、选中态（按下时高亮）、Reduce Transparency、Increase Contrast、多屏与凹槽 MacBook Pro、`NSStatusBar` 空间紧张时被隐藏后功能是否仍可达。用 `scripts/check_template_images.py Assets.xcassets --kind menubar` 检查资产。

## 4. iOS / iPadOS 状态栏

app 不能在状态栏放自定义图标；HIG（Status bars）只关心三件事：

- **遮住状态栏下方的内容**：状态栏背景默认透明；如果下面是可交互控件，用户会去点却点不到。让内容可滚动并使用 scroll edge effect（`ScrollEdgeEffectStyle` / `UIScrollEdgeEffect`）在状态栏后放模糊层，保持文字可读，不要暗示下面可交互。
- **全屏媒体时可临时隐藏**（Photos 浏览图片），但要能用简单可发现的手势（单击）恢复。
- **不要永久隐藏**：用户离开 app 才能看时间和 Wi-Fi 是糟糕体验。

样式与隐藏 API：

| 需求 | SwiftUI | UIKit |
|---|---|---|
| 文字/图标深浅 | 跟随 `preferredColorScheme` / 背景自动；一般不手动指定 | `preferredStatusBarStyle` 返回 `.lightContent` / `.darkContent` / `.default`（需 Info.plist `UIViewControllerBasedStatusBarAppearance = YES`，默认即是） |
| 隐藏 | `.statusBarHidden(true)` | `prefersStatusBarHidden` + `setNeedsStatusBarAppearanceUpdate()`；`preferredStatusBarUpdateAnimation` |
| 在容器中转交给子控制器 | — | `childForStatusBarStyle` / `childForStatusBarHidden` |

iPadOS 26 的菜单栏与状态栏共用顶部区域（下拉显示），全屏运行时菜单栏常隐藏，所以所有功能在 UI 里都要有入口。iPadOS 没有菜单栏 extra。

## 5. 角标、Dock、Widget 与复杂功能中的状态图标

- **App 图标角标（badge）**：系统绘制的红色椭圆 + 数字，只用于未读/待处理数量；用户可在通知设置关闭；不要用它做营销或显示与通知无关的数值。
- **Dock 图标角标（macOS）**：`NSApp.dockTile.badgeLabel = "3"`；同样只表达待处理数量。Dock 菜单（`applicationDockMenu`）是菜单栏 extra 的可靠备份。
- **Widget 中的图标**：Widget 可能以 full color / tinted / clear 显示，图标随之被着色或去色，所以用 SF Symbols 或单色 glyph，不要放 app icon 或多色 logo（HIG：小 logo 只在多来源内容时放右上角）。
- **watchOS 复杂功能**：tinted 模式下系统把图像去饱和并按表盘色着色；线宽 ≥ 2 pt；可提供 tinted 专用版本；透明区域决定着色，不要铺背景。
- **Live Activity / 灵动岛**：用 SF Symbols 表达状态，尺寸小、对比高、不依赖颜色。

## 6. 自检清单

1. 用户说的"状态栏图标"是 macOS 菜单栏 extra、iOS 状态栏样式，还是角标 / Widget？
2. 菜单栏图标是模板图（`isTemplate` / Render As Template）且单色？
3. 素材高 ≤ 22 pt，图形约 16–18 pt，PNG 有 @1x @2x 或用矢量（`check_template_images.py --kind menubar`）？
4. 状态靠形状 / 变体 / 不透明度表达，而不是颜色或闪烁？
5. 点击显示菜单（不是 popover），用户可在设置里关闭 extra，被隐藏时功能仍可达（Dock 菜单 / 主窗口）？
6. 浅色、深色、选中态、Reduce Transparency 下都看过？
7. `accessibilityDescription` / label 随状态更新？
8. iOS：状态栏下方内容有模糊层且不可交互；隐藏只在全屏媒体时且可恢复；样式与背景匹配？
9. 角标只表示待处理数量；Widget / 复杂功能图标在 tinted 模式下可辨认？
