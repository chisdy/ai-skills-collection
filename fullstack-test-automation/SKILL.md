---
name: fullstack-test-automation
description: 全栈自动化测试专家，覆盖前端（React/Vue）和后端（FastAPI/Fastify）的完整测试工作流。当用户提到以下任何场景时必须使用此技能：(1) 为现有代码补写测试用例，(2) TDD 驱动新功能开发，(3) 调试失败的测试，(4) 自动跑测试并修复 bug，(5) 搭建测试基础设施（Vitest/pytest/Playwright），(6) 提升测试覆盖率，(7) 集成测试或 E2E 测试。即使用户只说"帮我写测试"、"测试跑不过"、"加单测"，也应立即激活此技能。
---

# Fullstack Test Automation

全场景测试自动化：写测试 → 运行 → 调试 → 修复，直到全绿。

## 技术栈覆盖

| 层 | 框架 | 测试工具 |
|---|---|---|
| React 前端 | React 19 | Vitest + React Testing Library + MSW |
| Vue 前端 | Vue 3.5+ | Vitest + Vue Test Utils + MSW |
| FastAPI 后端 | Python | pytest + pytest-asyncio + httpx |
| Fastify 后端 | Node.js | Vitest + supertest |
| E2E | 全栈 | Playwright |

---

## Step 0：识别模式

根据用户描述，判断当前处于哪种模式：

| 模式 | 触发信号 | 入口 |
|---|---|---|
| **Coverage** | "帮我写测试"、"补单测"、"提升覆盖率" | → Step 1 |
| **TDD** | "先写测试"、"测试驱动"、"TDD" | → Step 1（测试先于实现） |
| **Debug** | "测试跑不过"、"fix failing tests" | → Step 3（直接进调试循环） |
| **Full Flow** | "写完测试跑通"、"找 bug" | → Step 1 → Step 3 |

---

## Step 1：分析项目

### 1.1 检测技术栈

```bash
# 检查前端
cat package.json | grep -E '"react"|"vue"|"vitest"|"@testing-library"'

# 检查后端
ls *.toml *.cfg requirements*.txt 2>/dev/null | head -5
cat pyproject.toml 2>/dev/null | grep -E 'pytest|fastapi|httpx'
```

根据检测结果，读取对应参考文件：
- 前端测试模式 → [references/frontend-testing.md](references/frontend-testing.md)
- 后端测试模式 → [references/backend-testing.md](references/backend-testing.md)
- 调试策略 → [references/debug-loop.md](references/debug-loop.md)

### 1.2 理解代码结构

扫描需要测试的目标：

```bash
# 前端：找组件、Hook、工具函数
find src -name "*.tsx" -o -name "*.ts" | grep -v test | grep -v ".d.ts"

# 后端：找路由、Service、工具函数
find . -name "*.py" | grep -v test | grep -v __pycache__
```

### 1.3 检查现有测试基础设施

```bash
# 前端
cat vitest.config.ts 2>/dev/null || cat vite.config.ts 2>/dev/null | grep test

# 后端
cat pytest.ini 2>/dev/null || cat pyproject.toml 2>/dev/null | grep -A 10 '\[tool.pytest'
```

如果测试基础设施不存在，先完成 **Step 2** 再继续。

---

## Step 2：搭建测试基础设施（如需）

### 前端（React/Vue）

```bash
pnpm add -D vitest @vitest/coverage-v8 jsdom @testing-library/jest-dom
# React
pnpm add -D @testing-library/react @testing-library/user-event msw
# Vue
pnpm add -D @vue/test-utils @testing-library/vue msw
```

在 `vite.config.ts` 中添加：

```typescript
/// <reference types="vitest" />
export default defineConfig({
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'lcov'],
    },
  },
})
```

创建 `src/test/setup.ts`：

```typescript
import '@testing-library/jest-dom'
import { server } from './mocks/server'

beforeAll(() => server.listen({ onUnhandledRequest: 'warn' }))
afterEach(() => server.resetHandlers())
afterAll(() => server.close())
```

### 后端（FastAPI）

```bash
uv add --dev pytest pytest-asyncio httpx pytest-cov
```

在 `pyproject.toml` 中添加：

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

创建 `tests/conftest.py`（见 [references/backend-testing.md](references/backend-testing.md) 的 conftest 模板）。

---

## Step 3：制定测试计划

在写代码之前，列出测试清单并告知用户：

```
将为以下模块编写测试：

前端：
- [ ] UserCard 组件 - 渲染、交互、边界状态
- [ ] useAuth Hook - 登录/登出/token 刷新
- [ ] api/users.ts - 请求成功/失败/loading 状态

后端：
- [ ] POST /api/users - 创建用户（成功、重复邮箱、参数校验）
- [ ] UserService.create - 业务逻辑单元测试
- [ ] GET /api/users/{id} - 404 处理

E2E：
- [ ] 用户注册完整流程
```

**TDD 模式**：先写测试（此时测试应该失败），再实现功能，再跑通。

---

## Step 4：编写测试

按照参考文件中的模式编写测试。核心原则：

### 测试命名规范

```
describe('组件/函数名', () => {
  it('应该 [做什么] 当 [条件]', () => { ... })
  it('应该 [抛出/返回] 当 [边界条件]', () => { ... })
})
```

### 测试分层策略

```
单元测试（Unit）：
  - 纯函数、工具函数 → 直接测输入输出
  - 组件 → 测渲染结果和用户交互
  - Service 层 → mock 依赖，测业务逻辑

集成测试（Integration）：
  - API 路由 → 真实 HTTP 请求，mock 数据库
  - 前端 API 层 → MSW mock 后端，测完整请求链路

E2E 测试：
  - 关键用户流程 → 真实浏览器，真实后端（测试数据库）
```

详细模式见：
- [references/frontend-testing.md](references/frontend-testing.md)
- [references/backend-testing.md](references/backend-testing.md)

---

## Step 5：调试循环（核心）

写完测试后，进入自动调试循环。**最多执行 6 轮**，超出则停止并报告。

```
轮次 N：
  1. 运行测试，捕获完整输出
  2. 解析失败信息
  3. 判断根因（见下方决策树）
  4. 修复
  5. 重新运行
  6. 如果全绿 → 完成；否则继续下一轮
```

### 根因判断决策树

```
测试失败
├── 错误类型：Cannot find module / Import error
│   → 检查路径、安装依赖、tsconfig paths
│
├── 错误类型：TypeError / undefined is not a function
│   ├── 在测试代码中 → 修复 mock 或测试逻辑
│   └── 在业务代码中 → 这是代码 bug，直接修复
│
├── 错误类型：AssertionError（期望值 ≠ 实际值）
│   ├── 期望值明显错误 → 修正测试断言
│   └── 实际值是 bug → 修复业务代码
│
├── 错误类型：Timeout / async 问题
│   → 检查 await、async setup、waitFor 用法
│
└── 错误类型：数据库/网络连接错误
    → 检查 fixture、mock 配置、测试隔离
```

详细调试策略见 [references/debug-loop.md](references/debug-loop.md)。

### 修复原则

- **优先修复代码 bug**：如果测试逻辑正确但业务代码有问题，直接修复业务代码
- **修复测试时说明原因**：如果是测试写错了，解释为什么
- **不要为了让测试通过而写无意义的 mock**：mock 应该反映真实行为

---

## Step 6：完成报告

所有测试通过后，输出简洁报告：

```
✅ 测试全部通过

覆盖情况：
- 新增测试文件：3 个
- 测试用例：24 个（单元 18 + 集成 6）
- 覆盖率：87%（statements）

发现并修复的 bug：
- UserService.create：未处理重复邮箱时的数据库唯一约束错误
- useAuth：token 过期后未清除本地存储

运行命令：
  前端：pnpm test
  后端：pytest -v
  覆盖率：pnpm test --coverage / pytest --cov
```

---

## 快速参考

| 场景 | 命令 |
|---|---|
| 前端单次运行 | `pnpm vitest run` |
| 前端覆盖率 | `pnpm vitest run --coverage` |
| 后端运行 | `pytest -v` |
| 后端覆盖率 | `pytest --cov=. --cov-report=term-missing` |
| E2E 运行 | `npx playwright test` |
| E2E 调试模式 | `npx playwright test --debug` |
