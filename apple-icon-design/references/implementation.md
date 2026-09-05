# 实现与检测：文件格式、Xcode 接入、验证流程

这份文件回答"规范知道了，怎么落到工程里、怎么证明落对了"。前半部分是各类图标资源的文件格式与接入方式，后半部分是检测流程（脚本 + Apple 命令行工具 + 实机）。

## 目录

1. Icon Composer `.icon` 包结构
2. 资产目录：App Icon（.appiconset / image stack）
3. 资产目录：模板图与自定义符号
4. 交替图标（alternate icons）
5. 非 Xcode 工具链（Tauri / Electron / 手工打包）
6. 检测流程总览
7. 脚本用法
8. Apple 命令行工具
9. 实机 / 模拟器验证
10. 错误信息对照

---

## 1. Icon Composer `.icon` 包结构

`.icon` 是一个目录包：`icon.json`（组合与渲染描述）+ `Assets/`（被 `image-name` 引用的 SVG / PNG）。三层嵌套：**document → groups → layers**。数组顺序即 z 序：先出现的在下。画布 1024 pt，`translation-in-points` 以画布中心为原点。

```jsonc
{
  "fill": { "linear-gradient": ["extended-srgb:0.10,0.40,0.90,1", "extended-srgb:0.05,0.20,0.60,1"] },
  "fill-specializations": [                       // 按外观覆盖背景（与 fill 二选一，同时存在时 fill 生效）
    { "appearance": "dark", "value": { "solid": "extended-srgb:0.08,0.08,0.10,1" } }
  ],
  // 不要写 "features" 键：Icon Composer 1.6（Xcode 26.6）起含该键的包一律打不开；旧文章里的 refractivity / specular-location 已失效
  "supported-platforms": { "squares": ["iOS", "macOS"], "circles": ["watchOS"] },
  "groups": [                                     // 必需；≤4 个
    {
      "name": "Mark",
      "lighting": "combined",                     // individual | combined
      "specular": true,                           // 或 "inside" / "outside"
      "translucency": { "enabled": true, "value": 0.2 },   // 两个键都必需
      "shadow": { "kind": "neutral", "opacity": 0.4 },     // neutral | layer-color | none；两个键都必需
      "blur-material": 0.0,
      "layers": [                                 // 1–4 个，底→顶
        { "name": "Glyph", "image-name": "glyph.svg", "glass": true,
          "fill-specializations": [
            { "value": { "solid": "extended-srgb:1,1,1,1" } },
            { "appearance": "dark", "value": { "solid": "extended-srgb:0.9,0.9,1,1" } }
          ],
          "position": { "scale": 1.0, "translation-in-points": [0, 0] }   // 两个键都必需；恒等时省略
        }
      ]
    }
  ]
}
```

要点：

- 颜色编码 `<space>:<components>`：`extended-srgb:r,g,b,a`、`display-p3:r,g,b,a`、`extended-gray:w,a`；没有 `:` 会报错。`linear-gradient` 必须正好 2 色，没有角度参数。
- `squares` 只接受 iOS / macOS（iPadOS 随 iOS），`circles` 只接受 watchOS；tvOS / visionOS 不是 Icon Composer 目标。
- **未知键被静默忽略**：拼错 `fil`、`ligthing` 不会报错但也不生效；`X` 与 `X-specializations` 同时存在时 `X` 胜出。所以"渲染成功"不等于"设置生效"，有疑问就渲染两版做像素对比。
- `image-name` 指向不存在的文件会被当作空图层**渲染成功**；必须自己核对（`check_app_icon.py` 会）。
- 位图图层按原始像素渲染不放大；用 1024 px 或 SVG。图层素材要"平"：无阴影、无渐变光泽、无高光。
- Tinted 不能覆盖背景 fill，Clear 完全不可覆盖——所以前景必须靠形状自立。

## 2. 资产目录：App Icon

**iOS / iPadOS 单尺寸 + 外观**（Xcode 15+）：

```json
{
  "images": [
    { "filename": "icon.png", "idiom": "universal", "platform": "ios", "size": "1024x1024" },
    { "appearances": [{ "appearance": "luminosity", "value": "dark" }],
      "filename": "icon-dark.png", "idiom": "universal", "platform": "ios", "size": "1024x1024" },
    { "appearances": [{ "appearance": "luminosity", "value": "tinted" }],
      "filename": "icon-tinted.png", "idiom": "universal", "platform": "ios", "size": "1024x1024" }
  ],
  "info": { "author": "xcode", "version": 1 }
}
```

- 深色变体：透明背景（系统提供深色底）；着色变体：灰度图。
- macOS：`idiom: "mac"`，16/32/128/256/512 pt × 1x/2x 共 10 条，都要有文件。
- watchOS：`platform: "watchos"` 单张 1024。
- tvOS：`Brand Assets.brandassets` 含 `App Icon.imagestack`（400×240，2–5 层，每层一个 `.imagestacklayer/Content.imageset`）、`App Icon - App Store.imagestack`（1280×768）、`Top Shelf Image.imageset`（1920×720）与 `Top Shelf Image Wide.imageset`（2320×720）。
- visionOS：`.solidimagestack`，3 层，每层 512×512 @2x。
- Parallax Previewer / Exporter 可导出 `.lsr`（tvOS）/ `.xlsr`（visionOS）直接拖入。
- Build Settings：`ASSETCATALOG_COMPILER_APPICON_NAME`（App Icons Source）；`Include all app icon assets` 关闭时只打包所选集合，可用于 Debug / Release 不同图标。
- **Xcode 26+ 项目里若存在同名 .icon 文件，它取代 .appiconset**。

## 3. 资产目录：模板图与自定义符号

模板图（菜单栏、快捷操作、自定义 Toolbar / Tab Bar glyph）imageset：

```json
{
  "images": [
    { "filename": "menubar.pdf", "idiom": "universal" }
  ],
  "info": { "author": "xcode", "version": 1 },
  "properties": {
    "template-rendering-intent": "template",
    "preserves-vector-representation": true
  }
}
```

PNG 版本则列 `menubar.png`（1x）与 `menubar@2x.png`（2x）；iOS 侧还需 3x。Tab Bar 紧凑图标另加 `"width-class": "compact"` 条目。代码侧对应 `NSImage.isTemplate = true` / `UIImage.withRenderingMode(.alwaysTemplate)` / SwiftUI `.renderingMode(.template)`。

自定义 SF Symbol：Editor > Add New Asset > **Symbol Image Set**（`.symbolset`），拖入 SF Symbols app 导出的 SVG；Xcode 校验模板，失败会报错。代码用 `Image("custom.name")` / `UIImage(named:)`——不要用 `systemName`。同名再放一个 PNG imageset 可作为 iOS 12 的回退，Interface Builder 按平台自动选。

Home Screen 快捷操作：`UIApplicationShortcutIcon(systemImageName:)` 优先；自定义用 `UIApplicationShortcutIcon(templateImageName:)`（35×35 pt 模板图）。Info.plist 静态定义时 `UIApplicationShortcutItemIconSymbolName` / `UIApplicationShortcutItemIconFile`。

## 4. 交替图标

- 每个交替图标是独立的 `.icon` 文件（或 `.appiconset`，含自己的 dark / tinted）。
- Build Settings `ASSETCATALOG_COMPILER_ALTERNATE_APPICON_NAMES = AppIcon-Blue AppIcon-Green`（空格分隔，不带扩展名）；Xcode 据此写 `CFBundleIcons` / `CFBundleAlternateIcons`，不要手改 Info.plist。
- 运行时：`UIApplication.shared.supportsAlternateIcons`；`try await UIApplication.shared.setAlternateIconName("AppIcon-Blue")`（`nil` 恢复主图标）；以 `alternateIconName` 为当前状态的唯一真值。
- App Store Connect 产品页优化实验也可引用这些集合。
- 验证：`plutil -extract CFBundleIcons xml1 -o - App.app/Info.plist`；`xcrun assetutil --info App.app/Assets.car | grep AppIcon`。

## 5. 非 Xcode 工具链

Tahoe 从 `Assets.car` 读取 Liquid Glass 图标，只有 `.icns` 的 app 会被缩小放进灰色容器。步骤：

```bash
# 1. 把 .icon 编译成 Assets.car；actool 会同时产出旧系统用的 AppIcon.icns 与 partial.plist
xcrun actool AppIcon.icon --compile out/ --platform macosx --minimum-deployment-target 12.0 \
      --app-icon AppIcon --output-partial-info-plist out/partial.plist
# 2. 把 out/Assets.car 与 out/AppIcon.icns 复制到 MyApp.app/Contents/Resources/
# 3. 把 partial.plist 里的两个键合入 Info.plist：
#      CFBundleIconName = AppIcon          (Assets.car 里的名字，Tahoe 使用)
#      CFBundleIconFile = AppIcon          (AppIcon.icns，旧系统使用)
# 4. 核对：xcrun assetutil --info MyApp.app/Contents/Resources/Assets.car | grep '"Name"'
```

把这步放进构建脚本；打包工具自带的 `icon` 子命令（如 `tauri icon`）会用扁平 PNG 覆盖 `.icns`，之后不要再跑它。

## 6. 检测流程总览

按"静态 → 渲染 → 实机"三层推进，每层都能拦下一类问题：

| 层 | 工具 | 拦截的问题 |
|---|---|---|
| 静态 | `check_app_icon.py`、`check_template_images.py`、`check_symbols.py` | 尺寸 / alpha / 预圆角 / 缺变体 / icon.json 结构 / 资源缺失 / 模板意图 / 单色 / 符号名与可用性 |
| 渲染 | `ictool`（六种外观）、`preview_icon_sizes.py`（小尺寸 + 蒙版 + 壁纸）、`actool` 编译 | 单色模式下看不清、小尺寸细节消失、深色壁纸上轮廓消失、包无法打开 |
| 实机 | Simulator / Device Hub / 真机 / Mac Dock / 菜单栏 | 陀螺仪光效、真实壁纸、Reduce Transparency、与系统图标并排的视觉重量 |

## 7. 脚本用法

所有脚本仅依赖标准库；安装 Pillow 后启用像素级检查。退出码 1 表示存在 ERROR，可放进 CI。

```bash
S=<skill-dir>/scripts

# App Icon：.icon 包 / .appiconset / 单张 1024 PNG；--render 用 ictool 渲染全部平台 × 外观
python3 $S/check_app_icon.py AppIcon.icon --render build/icon-renders
python3 $S/check_app_icon.py Assets.xcassets/AppIcon.appiconset
python3 $S/check_app_icon.py marketing-1024.png

# 效果预览：squircle/圆形蒙版、6 个尺寸、浅/深/复杂壁纸、tinted 模拟；.icon 会先经 ictool 渲染
python3 $S/preview_icon_sizes.py AppIcon.icon -o build/icon-preview.png
python3 $S/preview_icon_sizes.py icon-1088.png --shape circle      # watchOS

# SF Symbols 用法审计：名称存在性、旧别名、最低系统版本、受限符号、.resizable()、仅图标按钮
python3 $S/check_symbols.py Sources/ --min-ios 17.0 --min-macos 14.0

# 模板图：菜单栏 / 快捷操作 / Tab Bar / Toolbar / 复杂功能
python3 $S/check_template_images.py Assets.xcassets --kind menubar --filter "MenuBar|Status"
python3 $S/check_template_images.py Assets.xcassets/QuickAction-New.imageset --kind quickaction
```

输出分 `[ERROR]`（会被拒 / 不显示 / 打不开）、`[WARN]`（明显不符合规范）、`[INFO]`（建议与需人工确认的项）。把结果按这三级写进审查报告，不要把 INFO 当阻塞。

## 8. Apple 命令行工具

```bash
# Icon Composer 渲染器（Xcode 26+）：渲染即校验，能渲染就能在 Icon Composer 里打开
ICTOOL="$(dirname "$(xcode-select -p)")/Applications/Icon Composer.app/Contents/Executables/ictool"
"$ICTOOL" AppIcon.icon --export-image --output-file out.png --platform iOS \
    --rendition TintedDark --width 1024 --height 1024 --scale 2 --tint-color 0.55 --tint-strength 0.8
# --platform iOS|macOS|watchOS   --rendition Default|Dark|ClearLight|ClearDark|TintedLight|TintedDark

# 编译资产目录，顺便让 actool 校验 Contents.json 与图标尺寸
xcrun actool Assets.xcassets --compile out/ --platform iphoneos --minimum-deployment-target 17.0 \
    --app-icon AppIcon --output-partial-info-plist out/p.plist --warnings --errors

# 查看编译产物里有哪些图标 / 变体
xcrun assetutil --info out/Assets.car | grep -E '"Name"|Appearance|Idiom' | sort | uniq -c

# 快速缩放看小尺寸（不加蒙版）
sips -Z 40 icon-1024.png --out icon-40.png

# 去掉 alpha（ITMS-90717）
sips -s format png --matchTo '/System/Library/ColorSync/Profiles/sRGB Profile.icc' in.png --out out.png   # 先统一色彩配置
python3 -c "from PIL import Image; Image.open('in.png').convert('RGB').save('out.png')"                    # 再压平
```

## 9. 实机 / 模拟器验证

- **iOS**：Simulator 或真机长按主屏 → 编辑 → 自定义，切换 Default / Dark / Clear / Tinted，并换几张壁纸（纯色、照片、深色）。看 Spotlight、设置、通知里的小图。真机才有陀螺仪光移。
- **macOS**：Dock（浅/深色、放大动画）、Finder 各视图尺寸（16 px 列表到 512 px 预览）、Launchpad / 应用程序文件夹；菜单栏 extra 在浅 / 深色菜单栏、选中态、Reduce Transparency、与系统 extra 并排时的视觉重量。
- **watchOS**：表盘 App 视图（圆形裁切）、Dock、通知短视图。
- **tvOS**：聚焦时视差有无裁切。
- **visionOS**：注视时的层深与阴影。
- **无障碍设置**：Increase Contrast、Reduce Transparency、Bold Text（符号权重会变）、最大 Dynamic Type（符号与文字一起放大）。

## 10. 错误信息对照

| 信息 | 原因 | 处理 |
|---|---|---|
| `ITMS-90717 Invalid App Store Icon … alpha channel` | 1024 图含 alpha / 透明像素 | 压平为不透明 RGB PNG |
| `The data couldn't be read because it is missing.`（ictool） | icon.json 缺必需子键：`groups`、`shadow.opacity`、`translucency.value`、`position` 只给了一半 | 补齐键 |
| `… isn't in the correct format.` | 值类型或枚举错误：`shadow.kind: "chromatic"`（应为 `layer-color`）、`blur-material` 传布尔、`color-space-for-untagged-svg-colors: "srgb"` | 按第 1 节修正 |
| `Could not open "X.icon".` | icon.json 里存在 `features` 键（1.6 起任何取值都不接受），或 JSON 本身非法 | 删除 `features` 键；用 `python3 -m json.tool icon.json` 验证语法 |
| `Linear gradients require exactly 2 colors` | 渐变色数 ≠ 2 | 折叠为首尾两色 |
| `Invalid encoding of supported platforms` | `squares` 里放了 watchOS 或 `circles` 里放了 iOS | 交换 |
| 渲染成功但没变化 | 键拼错、或 `X` 遮住了 `X-specializations` | 像素对比两版；删掉 `X` |
| actool `The app icon set "AppIcon" has an unassigned child` | 文件在目录里但 Contents.json 未引用 | 删除或引用 |
| actool `… image is not a square` / `does not have the correct size` | 尺寸不匹配槽位 | 重新导出 |
| Tahoe Dock 里图标缩小带灰底 | 只有 .icns 或异形轮廓 | 提供 .icon / Assets.car |
| `Image(systemName:)` 空白、`UIImage(systemName:)` 为 nil | 符号名错误或高于部署目标 | `check_symbols.py`，`#available` 分支 |
| 菜单栏图标深色模式下看不见 / 一个实心方块 | 非模板图 / 无 alpha | `isTemplate = true`，素材改为黑 + 透明 |
