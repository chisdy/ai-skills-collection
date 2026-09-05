# Liquid Glass 与材质

Liquid Glass 是 WWDC25 引入、贯穿 iOS 26 / iPadOS 26 / macOS Tahoe 26 / watchOS 26 / tvOS 26 / visionOS 26 的统一控件材质：具有玻璃的光学特性（折射、镜面高光、随背景与设备运动变化）与流体般的形变。它**只属于功能层**（控件与导航），不是可以随处涂抹的视觉效果。

## 目录

1. 分层模型
2. 规则与反模式
3. 颜色
4. 几何与同心
5. SwiftUI API 速览
6. 无障碍与性能
7. App Icon 与 Icon Composer
8. 标准材质（内容层）
9. 上线前清单

---

## 1. 分层模型

| 层 | 内容 | 材质 |
|---|---|---|
| 内容层 Content | 文本、图片、列表、地图、图表、文档、卡片、视频 | 标准材质 / 普通背景 / 颜色 |
| 功能层 Navigation & Controls | Tab Bar、Toolbar、Sidebar、Sheet、Popover、菜单、浮动按钮、搜索栏 | **Liquid Glass** |
| 叠加层 Overlay | 玻璃之上的文字与符号 | Vibrancy |

原理：玻璃透过它显示下方内容，让控件"漂浮"于内容之上而不遮挡；内容始终是主角。若内容本身也是玻璃，层级就消失了，采样也会互相干扰。

HIG 原文要点：「Don't use Liquid Glass in the content layer」；例外只有内容层中具有瞬时交互态的控件（Slider、Toggle 拖动时呈现玻璃态以强调交互）。

## 2. 规则与反模式

| 做 | 不做 |
|---|---|
| 用系统 `TabView`、Toolbar、`Button`、`Menu`、`sheet` 等，自动获得材质 | 用自定义视图重造标准控件的"玻璃版" |
| 玻璃限于功能层 | 给列表、卡片、图片、正文背景加玻璃 |
| 多个相邻玻璃元素放进 `GlassEffectContainer` | 玻璃叠玻璃（玻璃卡片里放玻璃按钮） |
| 只给主操作或状态着色 | 用品牌色染每个控件 |
| 嵌套圆角同心 | 每个形状各自随意的圆角半径 |
| 在 Reduce Transparency / Increase Contrast / Reduce Motion 下测试 | 假定系统材质就万事大吉 |
| 用 Icon Composer 做分层图标 | 在位图里手绘伪造玻璃效果 |

自定义玻璃只在两种情况下合理：系统组件表达不了你的内容；或某个功能性元素确实需要浮在媒体之上。即便如此也要克制——「Limit these effects to the most important functional elements in your app」。

### regular 与 clear

- **regular**：会模糊并调整背景亮度以保证前景可读；绝大多数系统组件用它。用于背景可能影响可读性、或含大量文字的组件（Alert、Sidebar、Popover）。
- **clear**：高透明，优先展示底层内容。仅用于漂浮在照片、视频等视觉丰富背景之上的组件。底层内容偏亮时加一层 **35% 不透明度的黑色压暗层**；底层足够暗或已使用 AVKit 标准播放控件（自带压暗）时不需要。

## 3. 颜色

- 默认无色，从背后内容取色，可视为"透明玻璃"。
- 给玻璃本身着色 = "彩色玻璃"，用于**强调主操作**（系统 prominent 按钮样式，如 Done）。着色放在**背景**而不是文字或符号。
- Toolbar、Tab Bar 等小元素上的符号和文字默认单色，随下方内容明暗自动切换深浅；Sidebar 等大元素更不透明以保证可读。
- 不要给多个控件的背景同时着色。
- 背景本身色彩丰富时，Toolbar / Tab Bar 用单色外观，或选有足够区分度的强调色；内容单色为主时，用品牌色做 app accent color 是合理的。
- 注意内容层与功能层颜色重叠：可滚动内容的**默认静止态**（页面顶部）必须保证控件可读。

## 4. 几何与同心

Harmony 原则的具体体现：控件形状呼应硬件与容器的曲率。

- 嵌套圆角矩形的曲线要"相关"，内层跟随外层。SwiftUI 用 `ConcentricRectangle`（从容器推导圆角）而不是 `RoundedRectangle(cornerRadius: 12)` 硬编码。
- 系统组件已经这样做了；自定义布局中的图片框、卡片内按钮、Sheet 内容要跟上。
- 组件高度普遍增大、形状更柔和；排版更大、更粗、左对齐。移植旧界面时不要用固定高度对抗系统组件的新尺寸。

## 5. SwiftUI API 速览

```swift
// 标准组件：什么都不用做，Xcode 26+ 编译即自动获得材质
TabView { ... }
    .tabViewStyle(.sidebarAdaptable)   // iPad 可在 Tab Bar / Sidebar 间切换

// 自定义功能性元素才手动加玻璃
Text("Now Playing")
    .padding()
    .glassEffect()                      // 默认 .regular，胶囊形
    .glassEffect(.regular.tint(.accentColor).interactive(), in: .rect(cornerRadius: 16))
    .glassEffect(.clear)                // 仅覆盖媒体时

// 多个相邻玻璃元素：共享采样、允许形变合并
GlassEffectContainer(spacing: 20) {
    HStack {
        Button { } label: { Image(systemName: "play.fill") }
            .glassEffect()
            .glassEffectID("play", in: namespace)
        // ...
    }
}

// 同心圆角
Image(...)
    .clipShape(ConcentricRectangle())

// 内容不足以铺满时，在 Sidebar / Inspector 下方延伸内容感
ContentView()
    .backgroundExtensionEffect()

// 选择退出某组件的共享玻璃背景
.sharedBackgroundVisibility(.hidden)
```

UIKit / AppKit：标准控件同样自动获得材质；自定义用 `UIGlassEffect` / `NSGlassEffectView`；导航栏可配置 `barMinimizationBehavior`（滚动时收起）。

注意事项：

- 玻璃无法采样另一块玻璃，重叠的玻璃元素必须在同一个 `GlassEffectContainer` 里。
- 形变（morph）只在同一容器内、用 `glassEffectID` 关联的元素之间发生。
- 从 iOS 18 的"opt-in"变为 iOS 26 的"opt-out"：使用 Xcode 26+ 编译即默认启用，兼容期可用 `UIDesignRequiresCompatibility` Info.plist 键暂时保留旧外观，但这只是一个版本周期的过渡手段，Xcode 27 起可能不再生效。

## 6. 无障碍与性能

系统 Liquid Glass 自动响应：

- **Reduce Transparency** → 更多磨砂、更不透明
- **Increase Contrast** → 更硬的边界与对比
- **Reduce Motion** → 减弱形变与高光动画

这也是优先系统组件的理由：自绘的"像玻璃"视图不会自动获得这些行为。自定义视图里手动读取：

```swift
@Environment(\.accessibilityReduceTransparency) private var reduceTransparency
@Environment(\.accessibilityReduceMotion) private var reduceMotion
```

性能：实时折射与采样有开销，老设备上过多自定义玻璃会掉帧；内容可读性永远优先于效果。

## 7. App Icon 与 Icon Composer

- 图标现在是**分层的**，系统实时施加高光、折射、阴影；新的图标网格在各设备上统一并与硬件同心。
- iOS / iPadOS / macOS 提供 **default（浅色）/ dark / clear / tinted** 四种外观，用户可在主屏幕选择。
- 设计建议：视觉一致、光学平衡；用实心、填充、可重叠的半透明形状构成简化设计；**把遮罩、模糊等效果留给系统**，不要烘进素材。
- 用 **Icon Composer** 导入分层素材，一份文件覆盖 iPhone / iPad / Mac / Watch / App Store，可按外观与平台微调。
- 仍支持传统扁平位图，但要完整参与新设计语言需用 Icon Composer。

## 8. 标准材质（内容层）

内容层用标准材质表达结构与层次，不用 Liquid Glass。

- iOS / iPadOS：`ultraThin / thin / regular（默认）/ thick`，越厚越不透明、对小字对比越好；越薄越能保留背景语境。配套 vibrant 颜色：label 系列（default / secondary / tertiary / quaternary）、fill 系列、separator。避免在 thin / ultraThin 上用 quaternary。
- macOS：`NSVisualEffectView.Material` 按语义选（sidebar、titlebar、menu…），不要按看起来的颜色选；混合模式 behind-window / within-window。
- tvOS：导航与系统体验用 Liquid Glass；图片视图、按钮获得焦点时呈玻璃；内容层用标准材质分层。
- visionOS：窗口统一使用不可修改的系统 glass 材质，没有独立深色模式；窗口优先半透明；自定义组件用 thin（可交互/选中）、regular（分区，如 Sidebar）、thick（在 regular 背景上的深色元素）；文字用 vibrancy 的 label / secondaryLabel / tertiaryLabel 表达层级。
- watchOS：全屏模态默认带材质背景，不要移除或替换。

选材质看语义而不是颜色——系统设置会改变它的观感。材质之上用系统 vibrant 颜色保证可读。

## 9. 上线前清单

1. 凡是有系统组件的地方，是否都用了系统组件？
2. Liquid Glass 是否基本只出现在功能层？
3. 有没有不小心给普通内容加了玻璃背景？
4. 有没有玻璃叠玻璃？相邻玻璃是否在 `GlassEffectContainer` 里？
5. 着色是否只用在真正需要强调的控件上？
6. 嵌套圆角是否同心？
7. 是否在 Reduce Transparency / Increase Contrast / Reduce Motion 下测过？
8. 自定义玻璃组件是否真的必须自定义？
9. App Icon 是否跟上了当前平台设计（分层、四种外观）？
