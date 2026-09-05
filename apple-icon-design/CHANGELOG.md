# Changelog

版本号写在 `SKILL.md` 的 `metadata.version`（Agent Skills 规范不支持顶层 `version` 字段，值必须是字符串）。

变更历史放在这里而不是 `SKILL.md` 正文：`SKILL.md` 的每一行都会进入模型上下文，历史对执行图标任务没有帮助。

## 1.0.0

首个版本。下面记录不显然的设计决策及其理由。

### 来源

规范部分取自 Apple HIG 原文（Foundations：App icons、Icons、SF Symbols、Images、Right to left；Components：Status bars、The menu bar、Tab bars、Toolbars、Home Screen quick actions、Complications、Widgets；Technologies：SF Symbols）、Xcode 文档 *Configuring your app icon*、*Creating your app icon using Icon Composer*、*Configuring your app to use alternate app icons*、SF Symbols 文档 *Creating custom symbol images for your app*、WWDC25 *Say hello to the new look of app icons* 与 *Create icons with Icon Composer*。社区材料：Bjango *Designing macOS menu bar extras*（22 pt 工作区、16–18 pt 图形、模板图）、Sharp Objects / DEV 社区对 Icon Composer `icon.json` 结构与错误信息的逆向整理、多篇关于 macOS Tahoe "icon jail" 与 Tauri / Electron 迁移的文章、App Store 审核 ITMS-90717 的实践帖。

### 为什么把"图标"拆成三类而不是按平台组织

用户提需求时说的是"app icon"、"toolbar 图标"、"菜单栏图标"，而不是"iOS 图标"。三类图标的规则彼此几乎相反：App Icon 要有材质和层次，界面图标要平和单色，菜单栏图标只有 alpha。按类别组织能让模型一开始就选对规则集；平台差异（squircle 与圆形、22 pt 与 35 pt）在每类内部用表格处理。`status-bar-icons.md` 开头专门放了一张"用户可能指什么"的表，因为 iOS 上 app 根本不能放状态栏图标，这个歧义如果不先消除，后面的所有建议都会答非所问。

### 为什么脚本是技能的一半

图标问题的很多结论是二值的、可机器判定的：1024 图有没有 alpha、四角是否透明、符号名是否存在、是否高于部署目标、icon.json 是否符合 ictool 能接受的结构、模板图是否单色。让模型"看图判断"既慢又不可靠，而且在纯文本环境下根本看不到图。四个脚本把这些判断变成命令，并按 ERROR / WARN / INFO 分级直接对应审查报告的阻塞 / 重要 / 建议。`check_symbols.py` 读系统自带的 `CoreGlyphs.bundle`（名称、别名、逐平台最低版本、受限符号），因此不需要维护符号列表，也永远与本机系统一样新。`check_app_icon.py --render` 调 Xcode 26 的 `ictool` 把六种外观真的渲染出来，因为"Clear / Tinted 下还认得出来吗"只能靠看渲染结果回答。

脚本仅依赖标准库、Pillow 可选，是为了在没有装任何东西的 CI 或用户机器上也能跑出结构层面的结论，装了 Pillow 再补像素级检查。

### 为什么 `preview_icon_sizes.py` 要自己画 squircle 与壁纸

设计师和模型都习惯在 1024 px 看图标；真正的用户在 60 pt 主屏、40 pt Spotlight、29 pt 设置里看，还叠在自己的壁纸上，且 iOS 26 起还可能是 Clear / Tinted。contact sheet 把这些条件一次摆出来，是发现"细线消失、文字糊掉、深色壁纸上没有轮廓"最便宜的方法。用超椭圆近似 iOS 蒙版而不是精确曲线，因为目标是可读性判断而非像素级还原。

### 为什么 `.icon` 的 JSON 细节写进 `implementation.md`

Icon Composer 是 GUI 工具，但模型没有 GUI；能让模型交付 App Icon 的唯一路径是直接生成 `icon.json` + SVG。Apple 没有公开 schema，而 `ictool` 的错误信息（"The data couldn't be read because it is missing"）不指出是哪个键。第 1 节的结构注释与第 10 节的错误对照表都是实测得来的：哪些键必需成对出现（`shadow.kind` + `opacity`、`translucency.enabled` + `value`、`position.scale` + `translation-in-points`）、`features` 只接受两个值、`squares` / `circles` 平台归类、未知键静默忽略、`X` 遮住 `X-specializations`。这些是让"生成即可打开"成立的最小知识。其中一条在评测中被推翻并修正：社区文章（基于独立下载的 Icon Composer 1.2）说 `features` 键接受 `refractivity` / `specular-location`，但 Xcode 26.6 自带的 1.6 版 `ictool` 对含该键的包一律报 `Could not open`——本机两个版本并存时实测如此。脚本现在把任何 `features` 键报为 ERROR 并说明版本差异。

### 为什么不设 `disable-model-invocation: true`

与 `apple-hig-design` 同理：需要它的人多数不会说"按图标规范来"，而是说"帮我做个 app icon"、"这个 tab 图标怎么是空白的"、"菜单栏图标在深色模式下很丑"。描述因此写得偏"推"，列出了文件名（AppIcon.appiconset、.icon、Icon Composer）、API 名（systemName、status item）、错误码（ITMS-90717）与症状描述作为触发词。

### 与 `apple-hig-design` 的边界

`apple-hig-design` 的 `foundations.md` 有一小节 App Icon / SF Symbols 概述；本技能是那一节的展开，并接管了所有图标资源与检测。SKILL.md 末尾互相指路：界面整体的导航 / 布局 / Liquid Glass 控件层问题回到 `apple-hig-design`。

### evals

三个用例覆盖三类图标与三种模式：App Icon 审查（ITMS-90717 根因 + 打不开的 `.icon` + dark / tinted）、菜单栏 extra 重做（图标 + AppKit / SwiftUI 代码）、SF Symbols 用法审计与修复（不存在的名字、高于部署目标、旧别名、`.resizable()`、Toolbar 带圈符号、无障碍标签）。fixture 工程 `evals/apple-icon-design/fixture-repo/` 里的每个缺陷都对应脚本的一条输出，用于验证"模型会不会先跑脚本再下结论"；其中的 PNG / JPG 不入库，由 `evals/apple-icon-design/make_fixture.py` 生成，仓库只保留文本文件。第一轮评测：用技能 24/24，基线 20/24；基线丢分点是审查报告分级与实机验证清单、菜单栏 extra 的两条 HIG 行为规则（出菜单而非 popover、用户可隐藏）、以及旧别名的版本判断（`creditcard.and.123` 的新名需要 iOS 26）。最后一条促使 `check_symbols.py` 的别名提示改为先核对新名在部署目标上是否可用。断言放在仓库根 `evals/apple-icon-design/evals.json`，不进技能目录。
