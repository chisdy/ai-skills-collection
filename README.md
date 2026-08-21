# AI Skills Collection

专业的 AI 技能集合，为 Claude 和其他 AI 助手提供专业化的工作流程和领域知识。

## 技能列表

| 技能 | 目录 | 版本 | 用途 |
|---|---|---|---|
| Master Architect Workflow | `master-architect-workflow/` | — | 全栈架构师工作流，按任务复杂度自动路由简单/标准/完整三条路径 |
| Full Stack Expert | `fullstack-expert/` | — | 多技术栈全栈开发（React 19 / Vue 3 + FastAPI / Fastify） |
| Fullstack Test Automation | `fullstack-test-automation/` | — | 写测试 → 运行 → 调试 → 修复的全场景测试自动化 |
| Plan And Diff Review | `plan-and-diff-review/` | 1.0.0 | 只评审当前这一个方案或 diff，反范围蔓延，必修项写回计划文档 |

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

### Plan And Diff Review

只评审当前这一个方案或 diff：借 codegraph 映射受影响面（调用方、契约变更的下游），检查缺失逻辑与业务同步缺口，把必修项按严重度写回活跃的计划文档，并把新发现的无关问题隔离到"暂不处理"等待确认。默认只读，进入修复需用户批准具体条目。

名字里计划在前是有意的：评审尚未实施的方案时，发现的每个问题改起来都是零成本，所以纯方案输入是主场而非降级用法。

该技能默认不由模型自动触发（`disable-model-invocation: true`），需显式调用。

## 技能格式

每个技能遵循 Agent Skills 规范：

- `SKILL.md` — 主技能文件，YAML frontmatter（必填 `name` / `description`）+ Markdown 指令
- `references/` — 按需加载的参考文档
- `scripts/` — 可执行脚本（如需要）
- `assets/` — 模板和资源文件（如需要）
- `evals/` — 测试提示与断言
- `CHANGELOG.md` — 版本记录（如该技能已启用版本号）

版本号写在 frontmatter 的 `metadata.version`（规范不支持顶层 `version` 字段），值为字符串。目前只有 `plan-and-diff-review` 启用了版本号，其余三个待统一。

`workspaces/` 是 skill 评估的运行产物目录，已被 gitignore。

## 贡献指南

1. 每个新技能创建独立子目录，目录名必须与 frontmatter 的 `name` 完全一致
2. 遵循 Agent Skills 规范格式
3. `SKILL.md` 控制在 500 行内，详细内容下沉到 `references/`
4. 提供 `evals/evals.json` 便于回归验证

## 技能开发计划

- [x] Master Architect Workflow — 全栈架构师工作流
- [x] Full Stack Expert — 多技术栈全栈开发专家
- [x] Fullstack Test Automation — 全栈自动化测试
- [x] Plan And Diff Review — 方案与 diff 的聚焦式评审
- [ ] 数据库设计专家技能
- [ ] API 设计最佳实践技能
- [ ] 性能优化专家技能
- [ ] 安全审计专家技能
- [ ] DevOps 自动化技能

## 许可证

MIT License
