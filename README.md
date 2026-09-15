# AI Skills Collection

专业的 AI 技能集合，为 Claude 和其他 AI 助手提供专业化的工作流程和领域知识。

## 技能列表

| 技能 | 目录 | 版本 | 用途 |
|---|---|---|---|
| Master Architect Workflow | `master-architect-workflow/` | — | 全栈架构师工作流，按任务复杂度自动路由简单/标准/完整三条路径 |
| Full Stack Expert | `fullstack-expert/` | — | 多技术栈全栈开发（React 19 / Vue 3 + FastAPI / Fastify） |
| Fullstack Test Automation | `fullstack-test-automation/` | — | 写测试 → 运行 → 调试 → 修复的全场景测试自动化 |
| Plan Review | `plan-review/` | 1.0.0 | 写码前评审一份计划：前提核对、问题链隔离、可执行性审计，必修项写回计划文档 |
| Implementation Review | `implementation-review/` | 2.1.0 | 写码后评审按计划（或直接需求）实现的 diff：计划符合度、链外调用方、业务同步、安全评审、代码质量；自动识别语言栈并招募已安装的语言专项评审 / 格式技能 |
| Plan And Diff Review | `plan-and-diff-review/` | 1.0.0 | （已拆分为上面两个技能，保留作兼容）方案或 diff 的聚焦式评审 |
| Apple HIG Design | `apple-hig-design/` | 1.0.0 | 按 Apple Human Interface Guidelines 设计、实现与审查 iOS / iPadOS / macOS / watchOS / tvOS / visionOS 界面，含 Liquid Glass、Dynamic Type、Widgets |
| Apple Icon Design | `apple-icon-design/` | 1.0.0 | Apple 平台三类图标（App Icon / 界面图标 / 状态栏与菜单栏图标）的设计规范、Xcode 与 Icon Composer 接入，附四个检测脚本（.icon / .appiconset 校验、六种外观渲染与小尺寸预览、SF Symbols 用法审计、模板图检查） |

安装（把目录名替换成上表中的任一个）：

```bash
openskills install https://github.com/chisdy/ai-skills-collection/tree/main/plan-and-diff-review
```

### Master Architect Workflow

严格工程化流程的架构师工作流。收到任务先做复杂度评估并告知用户选择了哪条路径，避免小任务走冗长流程、大任务漏关键环节。内置意图澄清与方案对比机制。

### Full Stack Expert

前端支持 React 19 或 Vue 3.5+，后端支持 FastAPI（Python）或 Fastify（Node.js），统一 Vite 8 + Tailwind CSS V4 + pnpm。覆盖脚手架、前后端类型同步、状态管理选型、UI 与图标库选型。详细模式见 `references/`。

### Fullstack Test Automation

覆盖 Vitest + React Testing Library / Vue Test Utils、pytest + httpx、supertest 与 Playwright，从补测试、TDD 新功能、调试失败用例到提升覆盖率。

### Plan Review 与 Implementation Review

一对生命周期配对的评审技能，都默认不由模型自动触发（`disable-model-invocation: true`），需显式调用；都借 codegraph 映射受影响面，把必修项按严重度（阻塞/重要/次要）写回计划文档，把无关问题隔离到"暂不处理"等待确认。

- **Plan Review** 在写码前用：此刻发现的每个问题改起来都是零成本。独有能力：前提核对（计划假定存在的字段/表/端点逐个读出来确认）、当前问题链的截断/泄漏隔离、计划可执行性审计（步骤顺序、分阶段上线、每步验收、选型）。
- **Implementation Review** 在写码后用：计划是评审的 spec。独有能力：双向计划符合度（每步标 已实现/部分实现/未实现/偏离，无对应步骤的 hunk 标为计划外改动）、对变更攻击面的安全评审（权限/注入/敏感数据/输入校验/危险原语）、代码质量评审（可读性/结构/性能，阻塞项与不阻塞的改进建议分流）、对已写代码的直接验证（优先跑计划自带的验收标准）。

两者的前身 `plan-and-diff-review` 保留作兼容，新用法请直接用拆分后的两个。

### Apple HIG Design

把 Apple HIG 当参考手册而不是教材：先判断平台（显示、人机工程、输入、交互时长四个维度），再查对应的模式与组件，用系统组件承载功能层（控件与导航），把无障碍当设计输入而不是上线前补丁。`SKILL.md` 只放三原则（Hierarchy / Harmony / Consistency）、五步工作流、最常被问的数值速查（44pt 触控目标、4.5:1 对比度、平台最小字号等）与 Liquid Glass 一页纸；HIG 各章节下沉到 `references/`（foundations、liquid-glass、platforms、components-patterns、review-checklist）。支持三种模式：设计/实现界面（先给结构决策再给代码）、HIG 审查（按阻塞/重要/建议分级出报告）、答疑。会在用户写 SwiftUI / UIKit / AppKit 界面时自动触发。

### Apple Icon Design

`apple-hig-design` 中 App Icon / SF Symbols 一节的展开，接管所有图标资源。先把需求归入三类——App Icon（Liquid Glass 分层、Icon Composer `.icon`、六种外观、App Store 1024 图、交替图标、tvOS / visionOS image stack）、界面图标（SF Symbols 选型与代码、自定义 glyph 与自定义 SF Symbol 模板、Tab Bar / Toolbar / 快捷操作尺寸）、状态栏与菜单栏图标（macOS 菜单栏 extra 模板图、iOS 状态栏样式、角标 / Widget / 复杂功能）——再套对应规范。`scripts/` 里四个仅依赖标准库（Pillow 可选）的脚本把可机器判定的规则变成命令：`check_app_icon.py` 校验 `.icon` / `.appiconset` / 1024 PNG 并可用 Xcode 的 `ictool` 渲染全部外观；`preview_icon_sizes.py` 生成 squircle 蒙版 × 29–180 px × 浅深复杂壁纸 × tinted 模拟的对照图；`check_symbols.py` 读系统 `CoreGlyphs.bundle` 核对符号名、旧别名、逐平台最低版本、受限符号与 `.resizable()` 等误用；`check_template_images.py` 检查菜单栏 / 快捷操作 / Tab Bar 模板图的尺寸、单色与 template 意图。支持设计、接入、审查、答疑四种模式。

## 技能格式

每个技能遵循 Agent Skills 规范：

- `SKILL.md` — 主技能文件，YAML frontmatter（必填 `name` / `description`）+ Markdown 指令
- `references/` — 按需加载的参考文档
- `scripts/` — 可执行脚本（如需要）
- `assets/` — 模板和资源文件（如需要）
- `CHANGELOG.md` — 版本记录（如该技能已启用版本号）

评测不放在技能目录里：`openskills install` 会复制整个技能目录，用户用不到 fixture 和断言。作者侧回归放在仓库根目录 `evals/<skill-name>/`（`evals.json`，以及需要时的 `fixture-repo/`、`overlays/`）。官方 `.skill` 打包同样排除 `evals/`。

版本号写在 frontmatter 的 `metadata.version`（规范不支持顶层 `version` 字段），值为字符串。目前 `plan-and-diff-review` / `plan-review` / `implementation-review` / `apple-hig-design` / `apple-icon-design` 已启用版本号，其余三个待统一。

`workspaces/` 是 skill 评估的运行产物目录，已被 gitignore。

## 贡献指南

1. 每个新技能创建独立子目录，目录名必须与 frontmatter 的 `name` 完全一致
2. 遵循 Agent Skills 规范格式
3. `SKILL.md` 控制在 500 行内，详细内容下沉到 `references/`
4. 在仓库根目录 `evals/<skill-name>/` 提供评测用例，不要写进技能目录

## 技能开发计划

- [x] Master Architect Workflow — 全栈架构师工作流
- [x] Full Stack Expert — 多技术栈全栈开发专家
- [x] Fullstack Test Automation — 全栈自动化测试
- [x] Plan And Diff Review — 方案与 diff 的聚焦式评审（已拆分）
- [x] Plan Review — 写码前的计划评审
- [x] Implementation Review — 写码后的实现评审（含安全评审）
- [x] Apple HIG Design — Apple 平台界面设计、实现与审查
- [x] Apple Icon Design — Apple 平台图标规范、Icon Composer 接入与检测脚本
- [ ] 数据库设计专家技能
- [ ] API 设计最佳实践技能
- [ ] 性能优化专家技能
- [ ] 安全审计专家技能
- [ ] DevOps 自动化技能

## 许可证

MIT License
