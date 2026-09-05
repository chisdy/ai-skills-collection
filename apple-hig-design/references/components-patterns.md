# 组件与模式

按"你正在做的东西"索引。每节给出 HIG 的核心要求、常见误用与对应 SwiftUI 入口。设计前读对应小节，不要凭印象。

## 目录

1. 导航结构：Tab Bar、Sidebar、Navigation Stack、Split View
2. Toolbar 与菜单
3. 按钮
4. 列表、表单与滚动
5. 模态：Sheet、Popover、Alert、Action Sheet
6. 搜索
7. 设置
8. Onboarding 与启动
9. Widgets 与 Live Activities
10. 通知
11. 拖放
12. 加载、空状态与反馈
13. 手势与输入

---

## 1. 导航结构

先决定 app 的**信息架构**，再选容器。三种基本形态：

| 形态 | 适用 | 容器 |
|---|---|---|
| 平铺（几个平级区域） | 大多数内容型 app | Tab Bar / Sidebar |
| 层级（逐层深入） | 设置、邮件、文件 | Navigation Stack / Split View |
| 内容驱动（自由跳转） | 游戏、书、地图 | 自定义 + 系统控件辅助 |

### Tab Bar

- 展示 app 的**顶层区域**，始终可见，一次点按到达。iOS 一般 ≤5 项，visionOS ≤6。
- 不要用 Tab 承载操作（"新建"不是一个 Tab）；不要因为当前区域用不到就禁用某个 Tab；每个 Tab 保持自己的导航栈。
- 图标用 SF Symbols，系统自动选 filled 变体；配简短标签。
- iOS 26 起 Tab Bar 漂浮在内容之上（Liquid Glass），滚动时可收起；内容要延伸到其下方。
- 搜索可以作为 Tab Bar 的独立角色（`Tab(role: .search)`），系统会把它单独放置。

### Sidebar

- 用于**更丰富的层级**（文件夹、播放列表、账户），≤2 层；更深用三栏 Split View，中间加内容列表。
- 组标题简短。图标默认跟随 app accent / 用户强调色；只有具有明确含义时用固定色（Mail 的 VIP 黄）。
- 不要默认隐藏 Sidebar；iPadOS 用边缘滑动手势，macOS 给显示/隐藏按钮或 View 菜单命令；visionOS 窗口通常扩展以容纳，不必隐藏。
- **可转换 Tab Bar**（`tabViewStyle(.sidebarAdaptable)`）：iPad 顶部 Tab Bar 可展开为 Sidebar；iPhone 显示底部 Tab Bar；Mac / tvOS 始终 Sidebar；visionOS 以 Ornament 显示、`TabSection` 内的二级 Tab 用 Sidebar。只需要 Sidebar 时用 `NavigationSplitView`。

### Navigation Stack 与返回

- 返回按钮必须像返回按钮：标题、位置、滑动返回手势都保持系统行为。
- 不要在 Stack 里再套 Tab Bar；不要在层级中途改变导航模型。
- 标题用 Large Title 让层级清晰，滚动后自动收小。

### Split View

- 两栏或三栏：Sidebar → 内容列表 → 详情。iPad 变窄时先隐藏第三栏，最后折叠为 Stack；Mac 三栏常驻。
- 详情列在没有选中项时显示有意义的占位（"选择一封邮件"），而不是空白。

## 2. Toolbar 与菜单

- Toolbar 放**当前屏幕最常用的操作**，按频率而非"全部功能"；其余进 `Menu`（"更多"按钮）。
- 用系统 Toolbar，让系统处理放置、溢出与滚动时最小化；不要手工做溢出菜单。
- 用 `ToolbarItemGroup` / `ToolbarSpacer` 分组表达关系；主操作（Done / Save）用 prominent 样式着色，其余保持单色。
- 图标用 SF Symbols 并配 accessibility label；同一操作在全 app 用同一符号。
- macOS：Toolbar 可让用户自定义；所有 Toolbar 命令也要在菜单栏里；右键菜单（`contextMenu`）只放当前对象相关的操作，且不能是唯一入口。
- iOS 26 起 Toolbar 是漂浮玻璃，多个 Toolbar 项共享一块玻璃背景；用 `sharedBackgroundVisibility(.hidden)` 让某项独立。
- 菜单项用动词短语、Title Case（英文）；破坏性操作用 `role: .destructive`；相关项分组分隔；不要超过一屏。

## 3. 按钮

- **触屏命中区 ≥44×44pt，visionOS ≥60×60pt**（HIG Buttons）；macOS 推荐 28pt、tvOS 66pt。周围留够空间让人视觉上分辨。
- 标签让人**立刻知道会发生什么**：动词开头（"Add to Cart" 而不是 "OK"）。图标按钮优先 SF Symbols，并补 accessibility label。
- 样式表达层级：一屏内通常只有一个 prominent / filled 主按钮；次要用 bordered / borderless；破坏性用红色语义色。
- 不要自绘按钮外观去模仿系统；用 `buttonStyle(.borderedProminent)` 等。
- 全宽按钮在 iOS 不自然——尊重系统边距；确要全宽需与硬件圆角和安全区协调。
- 按下、禁用、加载中都要有状态；禁用态说明原因或避免禁用（改为点击后提示）。
- 切换类操作用 `Toggle` 而不是变色按钮；多选一用 `Picker` / segmented control。

## 4. 列表、表单与滚动

- `List` / `Form` 是内容层的主力，用系统分组样式（inset grouped）与语义背景色。
- 行内滑动操作（`swipeActions`）提供快捷方式，但**每个滑动操作必须有非手势替代**（详情页按钮、菜单）。
- 支持 Pull to Refresh（`refreshable`）当内容可刷新时。
- 可滚动内容延伸到 Tab Bar / Toolbar 之下，用滚动边缘效果过渡，不要给栏加实色背景。
- Dynamic Type 大字号下允许行高增长、多行显示，不要固定行高截断。
- 长列表提供索引、搜索或分区；空列表给空状态（见第 12 节）。

## 5. 模态

模态打断当前上下文，只在**需要用户注意或完成独立任务**时使用。iPad / Mac 大屏能内联解决的就不要模态。

- **Sheet**：独立任务（新建、编辑、分享）。始终提供关闭方式（Cancel / Done）；有未保存修改时确认；支持 detents（半高）用于附属信息。iPad 上 Sheet 居中或 popover 化，Mac 用窗口级 sheet。
- **Popover**：iPad / Mac 上附着于触发控件的轻量内容；iPhone 自动变 Sheet。
- **Alert**：仅用于**必须知道的关键信息**，标题说明问题，按钮明确后果（"Delete" 而不是 "Yes"）；破坏性按钮用 destructive role；不要用 Alert 做营销或频繁确认。
- **确认对话 / Action Sheet**（`confirmationDialog`）：让用户在几个操作中选择或确认破坏性操作。
- **全屏模态**：仅沉浸式任务（相机、阅读器）。
- 不要模态叠模态；不要用定时自动关闭替代显式关闭。

## 6. 搜索

- 用系统 `searchable`，放在导航栏或作为 Tab Bar 的搜索角色，系统处理外观与位置（iOS 26 起搜索栏位于底部，便于触达）。
- 输入即过滤（可行时）；提供最近搜索与建议（`searchSuggestions`）、范围（`searchScopes`）。
- 结果为空时给出建议（改关键词、检查拼写），不是空白。
- 支持 Spotlight 索引让 app 内容能在系统搜索中出现。

## 7. 设置

- **能推断的不要问**：优先用系统设置（Dynamic Type、深色模式、语言）而不是 app 内重复一套。
- 设置项按使用频率与主题分组，用 `Form` 分区；每项一句话说明后果。
- 极少改动的偏好可以放到系统「设置 app」里（Settings bundle），但常用的放 app 内。
- macOS 用独立 Settings 窗口（⌘,），不是 Tab。
- 不要把"设置"当作功能的垃圾场；功能相关的选项放在使用它的地方。

## 8. Onboarding 与启动

- **最好的 Onboarding 是不需要 Onboarding**：界面自解释，用 TipKit 在上下文中提示功能，而不是一开始塞满教程。
- 若必须有前置流程：简短、愉快、不要求记忆；可跳过；跳过后不再重复出现，但能在设置 / 帮助里找回。
- 内容只关于你的 app，不要教用户怎么用系统。
- 启动画面（Launch Screen）与首屏结构一致、无文字与品牌营销；启动后立刻可用，不要被大下载阻塞。
- 不要在 Onboarding 里放许可协议——交给 App Store 页面；必须放时要不打断节奏。
- 权限请求放在**用到的那一刻**并说明理由，不要启动时一次要完。

## 9. Widgets 与 Live Activities

Widget 的三个品质：**可瞥视、相关、可个性化**。

- 选一个与 app 核心目的直接相关的简单想法；展示及时内容（Weather 优先今日高低温）。
- 不要做 app 图标的复制品；不要做"迷你 app"式布局。
- **信息密度平衡**：太稀显得多余，太密不可瞥视。放不下就用更大尺寸或用图形替代文字。
- **深链**（`widgetURL`、`Link`）直达对应内容，不要让人再导航。
- **交互**（`Button(intent:)` / `Toggle(intent:)`）只用于最重要的一两个操作；目标足够大；锁屏 widget 无交互、inline 只有一个点按目标。
- 支持所有相关 family 与位置（主屏、锁屏、StandBy、桌面、通知中心、CarPlay）；iOS/iPadOS/macOS 27 新增 `systemExtraLargePortrait`。
- **外观模式**：全彩、tinted、clear；SwiftUI 自动适配，特殊视图用 `widgetAccentedRenderingMode(.fullColor)`。在三种模式下测试。
- 用 `AppIntentConfiguration` 让用户配置（选城市、选账户）；`StaticConfiguration` 用于无配置的。
- 时间线刷新有预算，选合适的 reload policy；不要依赖频繁刷新。
- Live Activity：进行中的任务（外卖、比赛、计时），Dynamic Island 三种态都要设计，结束后及时移除。
- Complication（watchOS）：线条 ≥2pt，tinted 模式可用，环形/仪表表达随时间变化的数值。

## 10. 通知

- 只在**用户会关心**的时刻发；可分类可关闭（`UNNotificationCategory`）。
- 标题说清事件，正文补充，不要重复 app 名。
- 附加操作（Actions）让人不打开 app 就能处理。
- 尊重 Focus 与通知摘要；时间敏感级别只用于真正紧急的。
- 不要用通知做营销或催促打开。

## 11. 拖放

- 用系统拖放 API（`draggable` / `dropDestination` / `Transferable`），跨 app、跨窗口、Files/Finder 都能工作。
- 拖动预览反映实际内容；放置目标有清晰的高亮反馈；不支持的放置要明确拒绝。
- macOS：允许从**非激活窗口**直接拖出选中内容；考虑拖到 Finder 生成文件。
- iPad：拖放是多任务的核心，选中多个后可一起拖。
- 拖放必须有非手势替代（复制/粘贴、菜单、分享）。

## 12. 加载、空状态与反馈

- 即时反馈：点击即有状态变化；超过约 1 秒显示进度（`ProgressView`），能估算就用确定进度。
- 用占位骨架或缓存内容而不是空白屏；不要阻塞整屏等待。
- **空状态**（`ContentUnavailableView`）说明为什么空、下一步做什么（"还没有笔记，点 + 新建"）。
- 错误信息说清发生了什么、如何恢复；不暴露技术细节。
- 成功反馈轻量（触觉、短暂横幅），不要每次都弹 Alert。
- 触觉（Haptics）配合系统语义（成功/警告/错误/选择变化），不滥用。

## 13. 手势与输入

- 系统手势优先（点按、滑动、捏合、长按），不要重定义系统手势的含义（边缘滑动是返回）。
- 自定义手势必须有可发现的、非手势的等价操作。
- 键盘：Mac / iPad 支持快捷键与 Full Keyboard Access；文本输入用正确的 `keyboardType` / `textContentType` 让自动填充生效。
- 指针：悬停效果（`hoverEffect`，iPad / Mac）、指针形状随内容变化（`pointerStyle`，macOS 15+ / visionOS 2+）。
- Apple Pencil：书写与绘画场景用 PencilKit / Scribble；不要求 Pencil 才能用核心功能。
- 游戏手柄：tvOS / iOS 游戏支持标准映射。
- 语音：Siri / App Intents 让核心任务可通过语音与快捷指令完成，这同时是无障碍能力。
