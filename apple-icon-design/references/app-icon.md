# App Icon：设计规范、规格与 Icon Composer

App Icon 出现在主屏幕、Dock、搜索、通知、设置、分享面板与 App Store。自 iOS 26 / iPadOS 26 / macOS Tahoe 26 / watchOS 26 起，它不再是一张位图，而是**一组分层素材 + 系统实时渲染的 Liquid Glass 材质**；设计者的工作从"画一张最终图"变成"提供干净的图层，把光效交给系统"。

## 目录

1. 分层模型（各平台）
2. 形状、网格与蒙版
3. 设计原则
4. 视觉效果：交给系统
5. 六种外观变体
6. 规格表与尺寸
7. 平台注意事项
8. Icon Composer 工作流
9. 旧项目迁移与非 Xcode 工具链
10. 常见被拒 / 上传失败原因
11. macOS 文档图标
12. 自检清单

---

## 1. 分层模型（各平台）

| 平台 | 结构 | 系统施加的效果 |
|---|---|---|
| iOS / iPadOS / macOS / watchOS | 1 个背景层 + 1 至多个前景层（Icon Composer 中组织为 ≤4 个 group，每 group 1–4 layer） | Liquid Glass：镜面高光、折射、半透明、层间阴影；随尺寸自动调整，跟随设备陀螺仪产生光移 |
| tvOS | 2–5 层 image stack | 焦点时视差（parallax）：层间分离 + 透明产生深度，前景层裁切多于背景层 |
| visionOS | 背景层 + 1–2 个上层（最多 3 层）image stack | 3D 化：层间阴影、用上层 alpha 做浮雕感，注视时轻微膨胀 |

分层的意义：系统对**每一层**单独打光、加阴影、做折射，所以"把 Logo 拆成几个可重叠的实心形状"比"一张画好光影的位图"效果好得多。

**图层素材规则**（HIG Layer design）：

- 前景层边缘清晰锐利；柔边、羽化会让系统高光和阴影计算出错。
- 用前景层的**不透明度差异**制造深度与生动感（Photos 图标把中心拆成多层半透明色块）；先导入完全不透明的图层，在 Icon Composer 里调透明度，边看边调。
- 背景层用实色或渐变，且要对系统光照反应良好；Icon Composer 直接支持实色/渐变背景，一般不必导入背景图；若导入，必须满幅、不透明。
- 优先矢量（SVG / PDF），文字转轮廓；mesh 渐变、位图素材用 PNG（无损）。位图小于 1024px 会按原尺寸渲染而不是放大。

## 2. 形状、网格与蒙版

| 平台 | 提供的图层形状 | 系统蒙版后的形状 |
|---|---|---|
| iOS / iPadOS / macOS | 正方形 1024×1024 | 圆角矩形（squircle），曲率与系统其它圆角、设备边框同心 |
| tvOS | 横向矩形 | 圆角矩形（同心边） |
| visionOS / watchOS | 正方形 | 圆形 |

- **不要预先切圆角或切圆**：系统会自己蒙版。预蒙版的图层会让边缘锯齿，还会破坏镜面高光的计算；iOS 上四角透明的 1024 图更会直接触发 ITMS-90717 被拒。
- 主体内容居中，避免被圆角 / 圆形裁掉；watchOS 与 visionOS 的圆形裁切更狠，边缘留白要更大。
- 使用 Apple Design Resources 中的 **App Icon 模板**（Figma / Sketch / Photoshop / Illustrator）里的网格与关键线，网格已随 iOS 26 统一并与硬件同心。
- **macOS 26 的重大变化**：Mac 图标不再允许任意轮廓、不能出框。仍用旧式"带阴影的异形 .icns"的 app，会被系统缩小塞进一个灰色 squircle 容器（社区称 "icon jail"）。要摆脱它必须提供 Icon Composer 图标或至少满幅方形素材。

## 3. 设计原则

- **一个概念、少量形状**。找到能代表 app 本质的一个元素，用尽量少的形状表达；细节在系统加了高光阴影后会显得杂乱，小尺寸下更看不见。
- **填充的、可重叠的实心形状** 比线稿效果好：与半透明和模糊搭配自然产生深度。
- **简洁背景**：实色或渐变，突出前景；不必铺满画布。
- **跨平台一致**：iPhone / iPad / Mac / Watch 上应是同一个图标的不同几何调整，否则用户会以为是不同的 app。
- **文字只在对品牌不可或缺时使用**：文字不可本地化、不可无障碍、小尺寸难读；不要写 "Watch" / "Play" / "New" / "For visionOS" 这类说明性词。tvOS 若含文字，放在最上层以免视差裁切。
- **插画而非照片**；不要复刻 UI 控件或放 app 截图；避免极细线条与尖角（小尺寸失真，也不利于光效——WWDC25 明确建议"更圆的角、更粗的线"）。
- **不要复刻 Apple 硬件**，它们有版权。**SF Symbols 不能用于 app icon / logo**（许可条款明文禁止，包括"混淆性相似"的图形）。
- 避免使用"表情包"式的多元素叙事：clear / tinted 模式会丢掉你的配色，**能靠轮廓辨认的图标才在所有外观下都成立**。

## 4. 视觉效果：交给系统

- 不要在素材里烘入高光、层间投影、斜角、模糊、发光。系统效果是动态的，烘入的是静态的，两者会打架。
- 如确有自定义效果，用 Icon Composer、Device Hub 中的模拟器或真机仔细验证。
- 同一 group 内可选 **Combined**（整组当一个物体打光）或 **Individual**（每层单独）；group 级别可调 Specular（Off / Automatic / Inside / Outside）、Blur、Refraction、Translucency、Shadow（Neutral / Chromatic / Off）。iOS 26 一代系统中 Refraction 无可见效果，27 起生效。

## 5. 六种外观变体

iOS / iPadOS / macOS 用户可在主屏幕自选：**Default（浅色）/ Dark / Clear Light / Clear Dark / Tinted Light / Tinted Dark**。Icon Composer 里对应 Default / Dark / Mono（Mono 下切 Light/Dark 与 Tinted 开关）。

- **特征一致**：核心形状在所有变体中保持不变，不要按变体换元素——用户切外观后要还能找到你的 app。
- **深色变体以浅色为基础**：选与默认设计呼应的互补色，避免过亮；有颜色的背景通常比纯黑对比更好。Xcode 资产目录方式下，深色图标建议用**透明背景**，让系统的深色底透出来。
- **单色（Clear / Tinted）可读性**：至少把最醒目的元素设为**白色**，其余映射为灰阶（WWDC25 Icon Composer 场次）。tinted 资产目录变体必须是**灰度图**，系统只用它的亮度。Clear 模式直接坐在壁纸上，前景与玻璃底要有明暗差。
- 系统会**自动生成**你没提供的变体，但自动结果常偏灰、偏糊；重要的 app 都应显式提供。
- **交替图标（alternate icons）**：iOS / iPadOS / tvOS 与兼容 visionOS 的 app 可让用户在设置里换图标。每个交替图标都要与内容强相关、不能像别的 app；iOS 上每个交替图标**都需要自己的 dark / clear / tinted 变体**，且一律接受审核。

## 6. 规格表与尺寸

HIG 规格（图层 layout size）：

| 平台 | 图层形状 | 蒙版后 | 画布 | 风格 | 外观 |
|---|---|---|---|---|---|
| iOS / iPadOS / macOS | 正方形 | 圆角矩形 | 1024×1024 px | 分层（Liquid Glass） | Default、Dark、Clear Light/Dark、Tinted Light/Dark |
| tvOS | 横向矩形 | 圆角矩形 | 800×480 px（App Store 1280×768） | 分层（视差） | — |
| visionOS | 正方形 | 圆形 | 1024×1024 px（3 层） | 分层（3D） | — |
| watchOS | 正方形 | 圆形 | 1088×1088 px（Icon Composer）/ 1024 资产目录 | 分层 | — |

色彩空间：sRGB、Gray Gamma 2.2、Display P3（iOS / iPadOS / macOS / tvOS / watchOS）。每张 PNG 嵌入色彩配置。

**资产目录（.appiconset）尺寸**，只在不能用 Icon Composer、或需要为旧系统单独提供位图时才需要全套：

| 平台 | 槽位 |
|---|---|
| iOS / iPadOS | 推荐 **Single Size**：一张 1024×1024，Xcode 生成其余；All Sizes 时：iPhone 20/29/40/60 pt @2x @3x；iPad 20/29/40/76 pt @1x @2x、83.5 pt @2x；App Store 1024 @1x（**不得含 alpha**）。dark / tinted 各再一张 1024 |
| macOS | **必须全部提供**：16、32、128、256、512 pt 各 @1x @2x（共 10 张，512@2x = 1024 也是 App Store 图） |
| watchOS | Single Size 1024（资产目录）；系统缩放到 38–49mm 各表壳 |
| tvOS | App Icon 400×240 @1x / 800×480 @2x（image stack，2–5 层）；App Store 1280×768；Top Shelf 1920×720 / 2320×720 @1x @2x |
| visionOS | 512×512 @2x（=1024）×3 层 solid image stack |

系统会自动从主图缩放出设置（29pt）、Spotlight（40pt）、通知（20pt）等小图，所以**设计时要在 29–40 px 下自检可辨认**（用 `scripts/preview_icon_sizes.py`）。

## 7. 平台注意事项

- **tvOS**：留安全区。聚焦时图标缩放移动，边缘会被裁；前景层裁得比背景层多；安全区大小随层深与运动变化。
- **visionOS**：背景层不要做"凹陷/洞"形状，系统阴影和高光会让它凸出来而不是凹进去。
- **watchOS**：不要用黑色背景，会和表盘底融为一体；把黑色提亮。
- **macOS**：图标出现在 Dock（有自己的模糊与鲜艳度）、Finder、Launchpad；用 Icon Composer 预览 macOS 平台变体，几何可与 iOS 略有差异（Composition 按平台 Vary）。

## 8. Icon Composer 工作流

Icon Composer 随 Xcode 26+ 附带（Xcode > Open Developer Tool > Icon Composer），也可从 Apple Design Resources 单独下载。一份 `.icon` 文件覆盖 iPhone / iPad / Mac / Watch / App Store 的全部尺寸与外观；tvOS / visionOS 仍用资产目录 image stack。

1. **在设计工具里准备**：从 Apple Design Resources 下载最新模板（含网格、形状、画布）；画布 1024（Watch 1088）；按 z 序从后到前分层，颜色/文字/图形分开放层以便后续按外观调整；文字转轮廓；**删掉**模糊、阴影、高光、透明度、背景色/渐变；图层命名带序号。
2. **导出**：优先 SVG；SVG 不支持的特性（mesh 渐变、位图）用 PNG；**不要导出画布蒙版**。
3. **建 .icon 文件**：命名与 Xcode 目标里 App Icon 名一致（通常 `AppIcon`）。
4. **导入并分组**：拖入文件或文件夹（文件夹自动成 group）；整理为 ≤4 个 group，group 是系统真正渲染的"层"；同 group 内图层共享一套 Liquid Glass 设置。
5. **只显示支持的平台**（Document inspector），减少干扰。
6. **预览六种外观**：底部选平台 × 外观；Mono > Options 里切 Light/Dark、Tinted、色相。顶部可换背景色/背景图（拖入自己的截图）、开关网格、选预览尺寸、对比 26 与 27 两代渲染、关闭 Effects 看裸图。
7. **调整**：Color（fill、opacity、blend mode，可按外观 Vary）、Liquid Glass（group 的 Mode / Specular / Blur / Refraction / Translucency / Shadow，layer 的 Effects 开关）、Composition（按平台 Vary 位置与缩放）。
8. **加入 Xcode**：把 `.icon` 拖进项目，目标 General > App Icons and Launch Screen > App Icon 名称与文件名一致。Xcode 26+ **优先使用 .icon 而忽略同名 AppIcon 资产目录**；对低于 26 的部署目标，Xcode 构建时自动从 .icon 生成近似的位图。
9. **验证**：`scripts/check_app_icon.py AppIcon.icon --render out/` 用 `ictool` 渲染全部外观；Simulator / Device Hub / 真机切换主屏外观；Mac 上看 Dock 与 Finder。

`.icon` 文件本身是目录包（`icon.json` + `Assets/`），可以脚本生成与校验，细节见 `references/implementation.md`。

## 9. 旧项目迁移与非 Xcode 工具链

- **保留旧图标给旧系统**：加入 .icon 后 Xcode 会为旧系统自动生成"像玻璃的"位图；如果你想让旧系统继续显示原来的位图，就继续用资产目录，不加 .icon。
- **拆层**：把现有扁平图标拆成背景 / 中景 / 前景，去掉烘入的阴影、光泽、圆角；重画比"抠图"效果好。
- **Tauri / Electron / 手工打包的 Mac app**：Tahoe 从编译后的 `Assets.car` 读取 Liquid Glass 图标，只有 `.icns` 会进 "icon jail"。用 `actool` 把 `.icon` 编译成 `Assets.car`，Info.plist 同时写 `CFBundleIconName`（Assets.car 里的名字）与 `CFBundleIconFile`（旧系统用的 .icns），`Contents/Resources/` 里两者并存。
- **市场素材**：App Store 产品页、截图里的图标现在也是系统渲染版；用 Icon Composer 的导出功能生成营销图，不要再用旧的扁平 PNG。

## 10. 常见被拒 / 上传失败原因

| 现象 | 原因 | 处理 |
|---|---|---|
| ITMS-90717 "Invalid App Store Icon … can't be transparent nor contain an alpha channel" | 1024 图含 alpha 通道或透明像素（常见：预切圆角、设计工具默认导出 RGBA） | 铺满不透明背景、导出时去掉 Alpha；不要自己切圆角 |
| "Missing required icon file" / 图标槽位为空 | 资产目录缺 1024 或 mac 全尺寸 | 补齐；或改用 Icon Composer |
| 图标模糊、边缘锯齿 | 用了小图放大、预蒙版、JPG | 用 1024 源图或 SVG；不预蒙版 |
| Guideline 2.3.7 / 2.3.8（元数据）、4.0（设计） | 占位图标、与 app 功能不符、模仿其它 app 或 Apple 产品、与截图不一致 | 图标要代表真实功能，交替图标同样受审 |
| Guideline 5.2.5 / HIG | 复刻 Apple 硬件、使用 SF Symbols 或 Apple 商标元素 | 换成原创图形 |
| Tahoe 上图标变小、有灰底 | 只提供了 .icns / 异形轮廓 | 提供 .icon 或满幅方形素材 |
| 深色 / 着色模式下图标一片灰 | 依赖系统自动生成变体 | 提供 dark 与灰度 tinted 变体，或用 Icon Composer 显式调 Mono |

## 11. macOS 文档图标

app 支持自定义文档类型时可提供文档图标（折角纸样式）。不提供则系统用 app 图标 + 扩展名合成。

- 可提供 **背景填充**、**中心图**、**文字**三者任意组合；系统自己叠成折角形状并蒙版。
- 简单、少色，16×16 px 也要能认；小尺寸版可以减少细节（去掉网格线、对齐像素加粗）。
- 背景填充**右上角别放重要内容**（白色折角会盖住）。背景填充尺寸：512/256/128/32/16 pt 各 @1x @2x。
- 中心图为画布的一半（32pt 文档图标用 16pt 中心图）；四周留约 10% 边距、内容占约 80%。尺寸：256/128/32/16 pt @1x @2x。
- 扩展名不好懂时可给一个短词（如 `scene` 代替 `scn`），系统自动大写、自动缩放到底部。

## 12. 自检清单

1. 图层是**未蒙版的满幅正方形**（tvOS 矩形），四角不透明？
2. 素材里没有烘入阴影 / 高光 / 模糊 / 圆角？
3. 前景边缘锐利、形状实心、可重叠、线条不细、角不尖？
4. 一个核心概念，小于等于 4 个 group，背景为实色/渐变？
5. 没有文字（或文字确有必要且不是说明词）、没有照片 / 截图 / UI 控件 / Apple 硬件 / SF Symbols？
6. Default、Dark、Clear（L/D）、Tinted（L/D）六种外观都预览过，单色下至少一个白色元素、轮廓可辨？
7. 29 px 与 40 px 下主形状仍可辨认（`preview_icon_sizes.py`）？
8. 各平台一致；watchOS 无黑底、visionOS 无凹形、tvOS 留安全区？
9. 1024 App Store 图无 alpha、PNG、sRGB / P3 带配置文件？
10. 交替图标各自带变体，且与 app 内容相关？
11. Xcode：.icon 名称与目标设置一致；旧系统回退符合预期（`check_app_icon.py`）。
