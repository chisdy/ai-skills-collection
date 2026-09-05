# Changelog

版本号写在 `SKILL.md` 的 `metadata.version`（Agent Skills 规范不支持顶层 `version` 字段，值必须是字符串）。

变更历史放在这里而不是 `SKILL.md` 正文：`SKILL.md` 的每一行都会进入模型上下文，历史对执行设计任务没有帮助。

## 1.0.0

首个版本。下面记录不显然的设计决策及其理由。

### 来源

以 Bitrig 的 [Apple Human Interface Guidelines (HIG): Beginner's Guide](https://bitrig.com/blog/apple-human-interface-guidelines) 与 [Liquid Glass Design: Best Practices](https://bitrig.com/blog/liquid-glass-best-practices) 为骨架，量化规则与平台细节取自 HIG 原文（Foundations：Layout / Typography / Color / Accessibility / Materials；Getting started：Designing for iOS / macOS / watchOS / visionOS；Components：Sidebars / Tab bars / Buttons / Widgets；Patterns：Onboarding）、Apple 开发者文档 *Adopting Liquid Glass*、WWDC25 Platforms State of the Union（三原则 Hierarchy / Harmony / Consistency）与 WWDC26 *Modernize your UIKit app*、*WidgetKit foundations*。

### 为什么组织成"流程 + 速查表 + 按需参考"，而不是 HIG 缩写本

Bitrig 文章的核心观点是 HIG 不该通读，而应像文档一样按需查。技能沿用这个理念：`SKILL.md` 只放每次都会用到的东西——三原则、模式判定、五步工作流、最常被问的数值、Liquid Glass 一页纸、输出格式；HIG 的章节内容下沉到五个 `references/` 文件，索引表告诉模型什么时候读哪个。这样每次触发只加载约 140 行，而不是把整套 HIG 灌进上下文。

### 为什么"平台先行"是第一步

模型最常见的失败是把 iPhone 布局搬到 iPad / Mac（或反过来）。HIG 每个平台页面都从显示、人机工程、输入、交互时长四个维度描述差异；把这四个维度放进 `platforms.md` 的对照表，并要求在回复开头用一句话写出平台约束，是让模型在写第一行代码前就切换心智模型的最便宜手段。

### 为什么强调"给 AI 编码代理下架构约束而不是外观形容词"

Bitrig 两篇文章都指出：对代理说"把 Tab Bar 做成玻璃的"会诱导它自绘一个玻璃组件；说"用原生 `TabView`"才是有效指令。这条经验对本技能的使用者（往往就是在用 agent 写 Apple app 的人）价值很高，因此写进 SKILL.md 步骤 3，而不是埋在参考里。

### 为什么不设 `disable-model-invocation: true`

与 `plan-review` / `implementation-review` 不同，这个技能的价值在于**用户没意识到需要它时**自动介入——写 SwiftUI 界面的人多数不会主动说"按 HIG 来"。描述因此写得偏"推"，列出 SwiftUI / UIKit / AppKit、各平台名、常见组件名作为触发词。

### 三种工作模式

设计 / 实现、审查、答疑三种模式输出形式不同：设计模式先给结构决策再给代码，让用户先看到"为什么用 `NavigationSplitView`"而不是直接淹在代码里；审查模式用 `review-checklist.md` 的模板，按阻塞 / 重要 / 建议分级并给 HIG 依据与修法，这与仓库里两个 review 技能的分级习惯一致；答疑模式直接回答并给依据。

### 数值的取舍

速查表只放"最常被问且跨版本稳定"的数值（44pt、11/17pt、4.5:1、200%、12/24pt 留白、60/80pt tvOS 安全区等）。完整的 text style 规格表放在 `foundations.md`，并在 SKILL.md「边界」里提醒精确到点的场景要核对 Apple Design Resources——HIG 的规格会随系统版本微调，技能不应假装自己是权威来源。

### 明确与 App Review Guidelines 的边界

Bitrig 文章 FAQ 特意区分 HIG 与 App Review Guidelines。用户遇到审核被拒时容易混淆两者，技能在「边界」里说明只覆盖设计部分，并点名 4.0 / 4.2 两条常见条目让用户知道去哪儿查。

### evals

三个用例分别覆盖三种模式：iOS 主界面实现（系统组件、Dynamic Type、无自绘玻璃）、iPhone→Mac 移植审查（菜单栏、快捷键、Sidebar、Dynamic Type 不可用、窗口底部控件）、Widget 设计（可瞥视、深链、交互克制、外观模式）。断言放在仓库根 `evals/apple-hig-design/evals.json`，不进技能目录。
