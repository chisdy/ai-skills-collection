# 图标审查：清单与报告模板

当用户给出图标素材、资产目录、`.icon` 包、代码或截图，想知道"哪里不合规范 / 为什么在设备上不好看 / 会不会被拒"时使用。审查不主动改素材或代码，除非用户要求；能跑脚本就先跑脚本，把脚本输出当证据，不当结论。

## 审查步骤

1. **分类与范围**：这是 App Icon、界面图标、状态栏图标中的哪一类（可多类）？目标平台与最低系统版本？拿到的是源文件、资产目录、编译产物还是截图？写进报告开头。
2. **先跑能跑的检测**（见 `implementation.md` 第 7 节）：App Icon → `check_app_icon.py`（`.icon` 加 `--render`）+ `preview_icon_sizes.py`；界面图标代码 → `check_symbols.py --min-*`；模板图 → `check_template_images.py --kind`。把 ERROR / WARN / INFO 逐条转成发现。
3. **按清单人工过**：脚本看不出"概念是否清晰"、"是否像别的 app"、"单色下是否还认得"。每项记录：通过 / 不通过 / 无法从材料判断。
4. **每条发现给依据与修法**：说明违反了哪条 HIG / Xcode 文档要求、用户或审核会看到什么后果、改成什么样；能给命令或代码就给。
5. **分级**：
   - **阻塞**：会被拒、不显示、或在某种外观下不可辨认——1024 图含 alpha、预圆角、符号名不存在 / 高于部署目标、菜单栏图非模板图、SF Symbols 用于 app icon、复刻 Apple 硬件、Clear / Tinted 下前景消失、图标与 app 功能无关。
   - **重要**：能用但明显不专业——烘入的阴影高光、细线尖角、文字说明词、缺 dark / tinted 变体、`.resizable()` 破坏 Dynamic Type、仅图标按钮无标签、Toolbar 用带圈符号、菜单栏图标 22 pt 以上、彩色状态图标。
   - **建议**：更好——减少 group 数、用 SVG 替代 PNG、替换旧符号名、用 variable color 表达量、光学居中微调。
6. **列出需实机验证的项**：陀螺仪光效、真实壁纸、Reduce Transparency、与系统图标并排的视觉重量、Dock 放大。

## 清单

### A. App Icon —— 素材与结构

- [ ] 图层为满幅、未蒙版的正方形（tvOS 矩形），四角不透明；没有预切圆角 / 圆形
- [ ] 素材里没有烘入的阴影、高光、斜角、模糊、发光、背景渐变（这些留给 Icon Composer）
- [ ] 前景边缘锐利，形状实心可重叠，无极细线与尖角
- [ ] 一个核心概念；group ≤ 4，每 group 1–4 层；背景为实色 / 渐变
- [ ] 素材为 SVG（文字转轮廓）或 1024 px PNG；无 JPG
- [ ] 无文字（或确属品牌必需且非说明词）、无照片 / 截图 / UI 控件、无 Apple 硬件、无 SF Symbols
- [ ] 跨平台一致（iPhone / iPad / Mac / Watch 是同一图标的几何调整）

### B. App Icon —— 外观与效果

- [ ] Default / Dark / Clear Light / Clear Dark / Tinted Light / Tinted Dark 六种都预览过（`ictool` 渲染或 Icon Composer）
- [ ] 各外观核心特征一致，未按外观换元素
- [ ] 单色模式：至少一个白色元素，其余灰阶；Clear 下在浅、深、复杂壁纸上都可辨认
- [ ] 深色变体以浅色为基础、不过亮；资产目录方式下深色透明背景、着色灰度
- [ ] 29–40 px 下主形状可辨认（`preview_icon_sizes.py`）
- [ ] 平台注意：watchOS 无黑底；visionOS 背景无凹形；tvOS 前景留安全区
- [ ] 交替图标各自有变体、与内容相关、不与他人混淆

### C. App Icon —— 工程与审核

- [ ] 1024 App Store 图：PNG、正方形、无 alpha、sRGB / P3 带配置文件
- [ ] `.icon` 名称与目标 App Icon 设置一致；或 `.appiconset` 槽位齐全（macOS 10 张）
- [ ] icon.json：`groups` 存在、无 `features` 键、平台归类正确、fill 编码正确、引用素材存在（`check_app_icon.py`）
- [ ] 旧系统回退行为符合预期（自动生成 vs 保留旧位图）
- [ ] 非 Xcode 工具链：Assets.car + CFBundleIconName 与 .icns + CFBundleIconFile 并存
- [ ] 图标代表真实功能，不模仿其它 app（App Review 2.3.x / 4.0）

### D. 界面图标 —— 选型与一致性

- [ ] 有 SF Symbol 的地方用了 SF Symbol；自定义图标有理由
- [ ] 同一动作全 app 同一符号（标准动作表）；Back / Close 用系统符号
- [ ] Tab Bar 用 fill 变体，Toolbar 用无边框 outline；不在 Toolbar 里用 `xxx.circle`
- [ ] 自定义 glyph 尺寸、细节量、笔画、透视一致；与相邻文字同重；光学居中
- [ ] 自定义图标为 PDF / SVG；PNG 有 @1x @2x（@3x）
- [ ] 图标不含不必要文字；含字符的已本地化
- [ ] 深浅两种外观都好看，或提供两份素材

### E. 界面图标 —— 代码

- [ ] 符号名全部存在、非旧别名、不高于最低部署版本（`check_symbols.py`）
- [ ] 受限 Apple 符号只用于指代对应产品且未修改
- [ ] 大小用 `.font` / `imageScale` / `SymbolConfiguration`，无 `.resizable()` / 固定 frame（插画用途除外）
- [ ] 渲染模式明确（iOS 16+ 默认可能非单色），颜色用系统色 / 语义色
- [ ] 与文字一起时用 `Label` 或基线对齐
- [ ] 动画有目的、数量克制、响应 Reduce Motion
- [ ] 自定义 SF Symbol：模板通过校验、插值源一致、模板版本匹配部署目标

### F. 状态栏 / 菜单栏图标

- [ ] 明确是 macOS 菜单栏 extra、iOS 状态栏样式，还是角标 / Widget 图标
- [ ] 菜单栏图标是模板图（`isTemplate` / Render As Template）、单色、靠 alpha 定形
- [ ] 高 ≤ 22 pt，图形约 16–18 pt，无多余 padding；PNG @1x @2x 或矢量（`check_template_images.py`）
- [ ] 状态用变体 / 形状 / 不透明度表达，不靠颜色，不闪烁
- [ ] 点击显示菜单而非 popover；用户可关闭；被隐藏时功能仍可达（Dock 菜单等）
- [ ] 浅 / 深色菜单栏、选中态、Reduce Transparency 下可见；`accessibilityDescription` 随状态更新
- [ ] iOS：状态栏下有模糊层且不可交互；仅全屏媒体时隐藏且可恢复
- [ ] 角标只表示待处理数量；Widget / 复杂功能图标在 tinted 下可读

### G. 无障碍（所有类别）

- [ ] 仅图标控件有 VoiceOver 标签；装饰图已隐藏
- [ ] 图标随 Dynamic Type 缩放（SF Symbols 用 text style；自定义用 `@ScaledMetric`）
- [ ] 图标与背景对比 ≥ 3:1，浅深两色
- [ ] 状态不只靠颜色
- [ ] RTL：该翻转的翻了（方向、文字）、不该翻的没翻（Logo、时钟、✓）

## 报告模板

```markdown
# 图标审查：<app / 模块名>

## 审查范围
- 图标类别：<App Icon / 界面图标 / 菜单栏 extra …>
- 平台与最低版本：<iOS 26 / macOS Tahoe，部署目标 iOS 17 …>
- 材料：<AppIcon.icon / Assets.xcassets / Sources/ / 截图>
- 已运行的检测：<check_app_icon.py --render、preview_icon_sizes.py、check_symbols.py --min-ios 17 …>
- 未覆盖：<看不到的部分>

## 总体判断
<两三句：最大的问题是什么、会在哪一步（审核 / 主屏 / 深色模式）暴露、先改哪一件>

## 阻塞
1. **<问题>** — <位置：文件 / 行 / 图层>
   - 现状：…（脚本输出或观察）
   - 依据：<HIG / Xcode 文档 / App Review 条目，以及用户会看到什么>
   - 修法：<具体做法，命令或代码>

## 重要
1. …

## 建议
1. …

## 通过项
<列出检查过且没问题的类别，让"没发现问题"有分量>

## 需实机验证
- [ ] 主屏六种外观 × 浅/深/复杂壁纸
- [ ] 29–40 px 尺寸（Spotlight、设置、通知）
- [ ] Dock / 菜单栏浅深色、Reduce Transparency、Increase Contrast
- [ ] <平台特定：Watch 圆形裁切 / tvOS 视差 / visionOS 层深>
```

## 写发现时的语气

解释"为什么"而不是引用条目编号。不写"违反 HIG：图标含 alpha"，而写"这张 1024 图的四个角是透明的，说明导出时已经切了圆角。系统会用自己的 squircle 再蒙一次，边缘会出现锯齿和双重圆角；App Store Connect 校验会直接以 ITMS-90717 拒收。把源文件的圆角蒙版关掉、导出为不透明 RGB PNG 即可，圆角交给系统"。读者拿到的是能立刻执行的修法和背后的原因。
