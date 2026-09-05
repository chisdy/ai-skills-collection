# Tickets

演出票务 app。iOS 主 app（最低部署 iOS 16.0）+ macOS 菜单栏伴侣（最低 macOS 13）。

- `Assets.xcassets/AppIcon.appiconset` — 当前使用的 App Icon（设计师从 Figma 导出）
- `AppIcon.icon` — 正在尝试迁移到 Icon Composer 的分层图标（未完成）
- `Assets.xcassets/MenuBarIcon.imageset` — macOS 菜单栏图标
- `Sources/TicketApp/` — SwiftUI / AppKit 源码

> 评测说明：本目录的 PNG / JPG 不入库，运行 `python3 ../make_fixture.py` 生成后再执行评测。
