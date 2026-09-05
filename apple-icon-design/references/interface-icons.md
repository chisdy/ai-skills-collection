# 界面图标：SF Symbols 与自定义 Glyph

界面图标（HIG 称 interface icon / glyph）出现在 Toolbar、Tab Bar、菜单、按钮、列表行、Widget、通知操作、快捷操作、Watch 复杂功能里。它与 App Icon 相反：**不要**有材质、光影与个性，用简化形状和一点颜色传达一个直接的意思。所有界面图标都以"黑色 + 透明"定义形状，由系统上色。

## 目录

1. 选型顺序
2. SF Symbols：核心概念
3. SF Symbols：代码要点（SwiftUI / UIKit / AppKit）
4. 自定义 glyph 的设计规则
5. 自定义 SF Symbol（模板与注解）
6. 位图 glyph 尺寸参考
7. 标准动作对应的符号
8. RTL 与本地化
9. 无障碍
10. 自检清单

---

## 1. 选型顺序

1. **系统 SF Symbol**（9000+ 个）：免费获得权重匹配、Dynamic Type 缩放、深色模式、RTL 变体、本地化变体、渲染模式、动画、VoiceOver 默认描述。
2. **自定义 SF Symbol**（从相似符号导出模板改绘）：仍获得上述所有能力，且与系统符号视觉一致。用 SF Symbols app 的**组件库**生成 enclosed / slash / badge 变体，不要手绘变体。
3. **矢量 glyph**（PDF / SVG 模板图）：系统只做缩放与着色，权重不随文字变化。
4. **位图 glyph**（PNG @1x/@2x/@3x）：最后的选择，需要按尺寸类别供多套。

界面图标不允许：SF Symbols 用于 app icon / logo；修改标记为受限（带 Info 角标）的 Apple 产品符号；复刻 Apple 硬件（只能用 SF Symbols 里的设备符号，且不可修改）。

## 2. SF Symbols：核心概念

**可用性随系统版本**：某年发布的符号不能在更早系统上用，否则 `Image(systemName:)` 渲染为空、`UIImage(systemName:)` 返回 nil。符号名也会改（旧名作为别名保留，但 SF Symbols app 里搜不到）。`scripts/check_symbols.py` 用系统自带的 `CoreGlyphs.bundle` 元数据核对名称、别名、最低版本与受限符号。

**渲染模式**（符号被分成 primary / secondary / tertiary 层）：

| 模式 | 行为 | 何时用 |
|---|---|---|
| Monochrome | 一种颜色涂所有层 | 默认 Toolbar / Tab Bar；单色最稳 |
| Hierarchical | 一种颜色，按层级递减不透明度 | 想有深度又不想引入第二色 |
| Palette | 每层一种颜色 | 与品牌配色系统协调；只给 2 色时二三层同色 |
| Multicolor | 符号自带语义色（`leaf` 绿、`trash.slash` 红） | 表达真实世界意义；部分层仍可接受自定义色 |

iOS 16 起**未指定模式时不再默认单色**（如 `airpodsmax` 默认 hierarchical）；需要单色时用 `.symbolRenderingMode(.monochrome)` / `preferringMonochrome()`。用系统色而不是硬编码色，符号才会跟随深色模式、鲜艳度与无障碍设置。每种模式都要在实际尺寸与背景下确认可辨认。

**渐变**（SF Symbols 7 / iOS 26）：从单一源色生成线性渐变，所有模式与自定义符号可用；大尺寸效果最好。

**可变颜色（variable color）**：按 0–100% 的值逐层点亮，表达**变化中的量**（音量、信号、进度）；不要拿它表达深度（那是 hierarchical 的事）。可标注哪些层不参与（如 `speaker.wave.3` 的喇叭本体）。

**权重与比例**：9 档权重对应 SF 字重，让符号与相邻文字**同重**；3 档 scale（small / medium 默认 / large）相对 cap height 定义，用来调整符号相对文字的强调度而不破坏字重匹配。

**设计变体**：outline（默认，像文字，适合 Toolbar、列表）、fill（更重，适合 iOS Tab Bar、滑动操作、用 accent 色表示选中）、slash（不可用/关闭）、enclosed（circle / square / rectangle，小尺寸更清晰）。很多容器自动决定变体：iOS Tab Bar 取 fill，Toolbar 取 outline，一般不用手动指定；HIG 现在要求 Toolbar 里**优先用无边框符号**（不要 `xxx.circle`），因为 Liquid Glass 分组本身已提供容器与 hover/选中态。还有按语言 / 书写系统自动切换的本地化变体。

**动画**：Appear / Disappear、Bounce、Scale、Pulse、Variable Color、Replace（Down-up / Up-up / Off-up；Magic Replace 为相关符号的默认）、Wiggle、Breathe、Rotate、Draw On / Off（SF Symbols 7）。原则：每个动画要有明确的沟通目的（反馈、状态变化、进行中），克制数量，考虑 app 的语气，响应 Reduce Motion。

## 3. SF Symbols：代码要点

```swift
// 与文字一起：用 Label，自动对齐、间距、VoiceOver
Label("分享", systemImage: "square.and.arrow.up")

// 大小：跟文字走，不要 .resizable() / .frame()
Image(systemName: "bell.badge")
    .font(.title2)                  // 跟随 Dynamic Type
    .imageScale(.large)             // 相对文字再放大一档
    .fontWeight(.semibold)          // 与相邻文字同重

// 渲染模式与颜色
Image(systemName: "cloud.sun.rain.fill")
    .symbolRenderingMode(.palette)
    .foregroundStyle(.gray, .yellow, .blue)   // 多色即 palette，可省略上一行
Image(systemName: "wifi", variableValue: 0.66)

// 变体与动画
Image(systemName: "heart").symbolVariant(isLiked ? .fill : .none)
    .contentTransition(.symbolEffect(.replace))
Image(systemName: "arrow.down.circle").symbolEffect(.bounce, value: downloads)

// 基线对齐
HStack(alignment: .firstTextBaseline) { Image(systemName: "calendar"); Text("今天") }

// 仅图标按钮必须有可读标签
Button { share() } label: { Image(systemName: "square.and.arrow.up") }
    .accessibilityLabel("分享")
```

UIKit：`UIImage(systemName:)` + `UIImage.SymbolConfiguration(textStyle:)` / `(pointSize:weight:scale:)` / `(paletteColors:)` / `(hierarchicalColor:)`，赋给 `imageView.preferredSymbolConfiguration`；Bar item 会自动配置符号，不要手动设。用 `firstBaselineAnchor` 对齐。`imageView.addSymbolEffect(.bounce)`。
AppKit：`NSImage(systemSymbolName:accessibilityDescription:)`（描述参数不要传 nil）、`NSImage.SymbolConfiguration`、`imageView.symbolConfiguration`。

常见错误：

- `.resizable().frame(width:height:)`：符号退化为普通位图，丧失字重、基线与 Dynamic Type。仅在把符号当"插画"用时才允许。
- `.font(.system(size: 30))` 固定字号：不随 Dynamic Type；要固定大小又要缩放用 `@ScaledMetric`。
- 直接 `.frame()` 而不改 font：只改布局框，符号不变。
- `.foregroundColor` 而非 `.foregroundStyle`：多色与层级样式需要后者。
- 旧系统上用新符号：`#available` 分支或换旧符号 / PNG 回退资产（资产目录里同名 Symbol Image Set + PNG 会自动按平台选）。

## 4. 自定义 glyph 的设计规则

- **高度简化、可识别**：熟悉的视觉隐喻，直接关联它触发的动作或代表的内容；细节越多越像噪点。
- **全 app 一致**：无论只用自定义还是混用系统符号，尺寸、细节程度、笔画粗细（权重）、透视要统一；视觉重量不同的图标可微调尺寸求一致。
- **与相邻文字同重**（除非刻意强调其中一方）。
- **光学对齐**：不对称图标（下载箭头）几何居中会显得偏低；把微调量做成素材内的 padding，让几何居中 = 光学居中。调整通常只有 1–2 pt 却影响很大。
- **选中态**：用在 Toolbar / Tab Bar / Button 等系统组件里不需要单独提供，系统自动处理。
- **包容性**：性别中立的人形，避免跨文化难懂的图形。
- **文字**：只在表达文字概念（如格式化）时使用；单个字符要本地化；表示"一段文字"用抽象线条并提供 RTL 翻转版。
- **格式**：PDF / SVG 矢量，系统自动适配高分屏；PNG 需按 @1x @2x @3x 提供多套。
- **深浅色**：同一素材两种外观都好看就共用；否则在资产目录里提供 light / dark 两份合成一个命名图（如满月图标浅色下需描边，深色不需要）。
- **替代文本**：每个自定义图标都要有 accessibility label。

## 5. 自定义 SF Symbol（模板与注解）

流程：SF Symbols app 中找相似符号 → File > Duplicate as Custom Symbol → File > Export Template（SVG）→ 在矢量工具里修改 → 导出 SVG（精度 ≥ 7 位小数）→ File > Validate Templates → 拖回 SF Symbols app → 注解（渲染模式、可变颜色、动画层）→ File > Export Symbol → 拖入 Xcode 资产目录 Symbol Image Set → `Image("custom.name")`。

模板结构：

- `Symbols` 层最多 27 个变体 `<weight>-<S|M|L>`；**变量模板**只需 `Ultralight-S`、`Regular-S`、`Black-S` 三个插值源（路径数与控制点数必须相同、全部 path-based），系统插值其余 24 个；已显式提供的变体优先于插值。
- 比例因子：S 0.783、M 1.0、L 1.29。
- `Guides` 层：各 scale 的 Baseline / Capline 与每变体的 `left-margin-<variant>` / `right-margin-<variant>`（可为负，用于带 badge 的符号光学对齐；命名必须遵循此模式）。
- `Notes` 层：`template-version` 必须保留。不要用隐藏路径（会被算进轮廓）。
- 为支持多色 / 层级：描边转路径、纯色填充、无阴影等效果、形状闭合；注解通过 CSS class `multicolor-<i>:<color>` / `hierarchical-<i>:<level>` 写在 SVG 里；`-sfsymbols-variable-threshold` 表达可变颜色阈值；`-sfsymbols-clear-behind` 让重叠处不透底。
- 模板版本：v2 仅单色（iOS 14）；v3 含多色 / 层级注解与自定义边距（iOS 15+）；v4 含可变颜色（iOS 16+）。导出的模板不是源文件，编辑要回到 SF Symbols app。
- 设计目标：与系统符号在细节量、光学重量、对齐、位置、透视上一致；为动画准备时用完整形状 + erase 层而不是抠洞。

## 6. 位图 glyph 尺寸参考

优先 SF Symbols；以下数值用于不得不提供位图 / PDF 时（来自历史 HIG 与 Apple Design Resources 模板，容器真实尺寸随系统版本变化）。

| 位置 | 图形尺寸（pt） | 备注 |
|---|---|---|
| iOS Tab Bar（常规） | 圆形 25、方形 23、宽 31×23、高 23×31 | 系统显示 fill 变体 |
| iOS Tab Bar（紧凑，横屏 iPhone） | 圆形 18、方形 17、宽 23×17、高 17×23 | 资产目录 Width Class = Compact 提供第二套 |
| iOS Toolbar / Navigation Bar | 约 24（目标区 28） | 紧凑约 18 |
| Home Screen 快捷操作 | 35×35 模板 | 单色 template，不要用 emoji |
| 通知操作图标 | SF Symbol | 显示在操作标题尾部 |
| macOS Toolbar | 约 16–19 @1x（PDF/模板） | 系统按 controlSize 调整 |
| macOS 菜单项 / 菜单栏 extra | 见 `status-bar-icons.md` | |
| watchOS 复杂功能 | 随表壳 38–49mm 与模板变化（如 Circular Small Simple 16–21.5、Modular Small Simple 26–34.5、Extra Large Simple 91–121） | 线宽 ≥ 2pt；着色模式下系统去饱和，可提供 tinted 版 |
| Settings / Spotlight / 通知里的 app 图标 | 29 / 40 / 20 pt | 由 App Icon 自动缩放，不单独设计 |

## 7. 标准动作对应的符号

HIG 要求同一动作在整个 app（菜单、Toolbar、快捷操作、通知操作）用同一个符号。表内是当前 HIG 使用的名称，其中 `document.*` 与 `text.page.*` 一族是 SF Symbols 6（iOS 18 / macOS 15）起的新名，旧系统上要用旧名（`doc.on.doc`、`doc.on.clipboard`、`doc.text.magnifyingglass`）或 `#available` 分支；部署目标低于 iOS 18 时先用 `check_symbols.py --min-ios <版本>` 核对再照抄：

| 动作 | 符号 | 动作 | 符号 |
|---|---|---|---|
| 剪切 | `scissors` | 搜索 | `magnifyingglass` |
| 复制 | `document.on.document` | 查找 | `text.page.badge.magnifyingglass` |
| 粘贴 | `document.on.clipboard` | 筛选 | `line.3.horizontal.decrease` |
| 完成 | `checkmark` | 分享 | `square.and.arrow.up` |
| 取消 / 关闭 / 取消选择 | `xmark` | 打印 | `printer` |
| 删除 | `trash` | 账户 | `person.crop.circle` |
| 撤销 / 重做 | `arrow.uturn.backward` / `arrow.uturn.forward` | 喜欢 / 不喜欢 | `hand.thumbsup` / `hand.thumbsdown` |
| 新建 / 撰写 | `square.and.pencil` | 置顶 / 置底 | `square.3.layers.3d.top.filled` / `.bottom.filled` |
| 复制项 | `plus.square.on.square` | 上移 / 下移一层 | `square.2.layers.3d.top.filled` / `.bottom.filled` |
| 重命名 | `pencil` | 闹钟 | `alarm` |
| 移动到 / 文件夹 | `folder` | 归档 | `archivebox` |
| 附件 | `paperclip` | 日历 | `calendar` |
| 添加 | `plus` | 更多 | `ellipsis` |
| 选择 | `checkmark.circle` | 粗体 / 斜体 / 下划线 | `bold` / `italic` / `underline` |
| 上标 / 下标 | `textformat.superscript` / `.subscript` | 左 / 中 / 两端 / 右对齐 | `text.alignleft` / `.aligncenter` / `.justify` / `.alignright` |

返回与关闭按钮用系统标准符号，不要用文字 "Back" / "Close" 代替。

## 8. RTL 与本地化

- SF Symbols 自带 RTL 变体和阿拉伯 / 希伯来等本地化变体，自动切换；自定义符号可指定方向性。
- **要翻转**：表示文字或阅读方向的图标（左对齐线条）、表示前进/后退运动的图标（喇叭声波）、进度类控件两端的图形。
- **不翻转**：Logo、通用标记（✓）、真实物体（时钟）、只是为右手使用者倾斜的物体（铅笔、放大镜柄）。
- 复杂图标看组成部分：斜杠 / 放大镜 / 禁止符保持视觉语言一致；代表真实 UI 的 badge 跟 UI 一起翻；工具类保留握持方向、底图可翻。
- 含字母的图标若与阅读无关，考虑改成不含文字的替代图。

## 9. 无障碍

- 仅图标的控件必须有 `accessibilityLabel`（SwiftUI）/ `accessibilityLabel`（UIKit）/ `accessibilityDescription`（AppKit）。很多 SF Symbols 有默认描述（`heart` → "love"），复杂符号没有，且默认描述是英文符号名。
- 装饰性图标标记为隐藏（`.accessibilityHidden(true)` / `isAccessibilityElement = false`）。
- 图标跟随 Dynamic Type：SF Symbols 用 `.font(text style)` 自动；自定义图用 `@ScaledMetric`。最大字号下考虑改为堆叠布局或隐藏纯装饰图。
- 对比度：图标与背景 ≥ 3:1（非文本元素），浅深两种外观都测。
- 不要只靠颜色区分状态：成功/失败除颜色外还要形状差异（`checkmark.circle` / `xmark.octagon`）。
- 动画符号响应 Reduce Motion（`@Environment(\.accessibilityReduceMotion)`）。

## 10. 自检清单

1. 能用 SF Symbol 的地方是否都用了？自定义图标是否有充分理由？
2. 所有符号名在最低部署版本上可用？没有旧别名与拼写错误？（`check_symbols.py`）
3. 符号大小用 `.font` / `imageScale` 而不是 `.resizable()` / 固定 frame？与相邻文字权重匹配、基线对齐？
4. 渲染模式在实际尺寸、浅深两色下都可辨认？多色只在有语义时用？
5. Tab Bar 用 fill、Toolbar 用无边框 outline；同一动作全 app 同一符号（第 7 节表）？
6. 自定义 glyph 尺寸 / 笔画 / 透视一致，光学居中，矢量格式，深浅两色都测？
7. 自定义 SF Symbol 通过 Validate Templates，插值源路径数一致，注解齐全，模板版本与部署目标匹配？
8. RTL 下该翻的翻了、不该翻的没翻？
9. 每个仅图标控件有 VoiceOver 标签，装饰图已隐藏？
10. 动画有沟通目的、数量克制、响应 Reduce Motion？
