---
name: fullstack-expert
description: 全栈开发专家，支持多种前后端技术栈组合。前端支持 React 19 或 Vue 3，后端支持 FastAPI（Python）或 Fastify（Node.js）。当用户提到以下任何场景时必须使用此技能：(1) 全栈项目开发、架构设计或脚手架搭建，(2) React 或 Vue 前端开发，(3) FastAPI 或 Fastify 后端 API 设计，(4) 前后端类型同步，(5) 状态管理（Zustand / Pinia / TanStack Query），(6) UI 组件库选型，(7) 图标库选型。即使用户没有明确说"全栈"，只要涉及前端框架配合后端 API 的任何问题，都应激活此技能。
---

# Full Stack Expert

支持多技术栈组合的全栈开发专家，根据用户需求灵活选型。

## 技术选项总览

| 维度     | 选项                                 |
| -------- | ------------------------------------ |
| 前端框架 | React 19 / Vue 3.5+                  |
| 后端框架 | FastAPI (Python) / Fastify (Node.js) |
| 构建工具 | Vite 8                               |
| CSS 框架 | Tailwind CSS V4                      |
| 包管理   | pnpm                                 |

---

## 新项目：技术选型问卷（必须先问，再动手）

在写任何代码之前，依次向用户确认以下选项。**以列表形式呈现选项，让用户直接选择编号**。

### 第一轮：核心技术栈

**1. 前端框架**

- A. React 19（生态最广，适合复杂应用）
- B. Vue 3.5+（上手更快，国内生态好，Composition API）

**2. 后端框架**

- A. FastAPI + Python（类型安全强，自动生成 OpenAPI 文档，适合 AI/数据场景）
- B. Fastify + Node.js（前后端同语言，性能极高，适合 API 网关/BFF 场景）

**3. UI 组件库**（根据前端框架展示对应选项）

React 可选：

- A. shadcn/ui（基于 Radix UI，无样式锁定，高度可定制）
- B. Ant Design 5（企业级，组件最全，中后台首选）
- C. MUI（Material Design 风格，国际化好）
- D. 不使用组件库（纯 Tailwind 手写）

Vue 可选：

- A. Element Plus（企业级，中后台首选）
- B. Naive UI（TypeScript 友好，轻量）
- C. Ant Design Vue（与 Ant Design 生态一致）
- D. shadcn-vue（shadcn/ui 的 Vue 移植版）

**4. 图标库**（可多选）

- A. Lucide（shadcn/ui 默认，轻量，SVG）
- B. Iconify（10万+ 图标，统一 API，支持所有主流图标集）
- C. Heroicons（Tailwind 官方出品）
- D. Font Awesome 6（最广泛，有 Pro 版）
- E. Phosphor Icons（风格统一，多种粗细）

### 第二轮：业务需求

**认证与权限**

- 是否需要用户认证？方式：JWT / OAuth2 / 第三方登录（Google/GitHub/微信）？
- 是否有多角色权限（RBAC）？

**数据库**（仅 FastAPI 后端需要）

- 数据库类型：PostgreSQL（推荐）/ MySQL / SQLite（仅开发）
- 是否需要软删除、全文搜索、数据审计？

**前端功能**

- 是否需要国际化（i18n）？
- 移动端适配：响应式 / 独立移动端 / 仅桌面端？
- 是否需要暗色模式？

**业务核心**

- 核心业务实体有哪些？（例如：用户、订单、商品）
- 是否有实时功能？（WebSocket / SSE）
- 是否需要文件上传？

**部署**

- 部署目标：Docker / 云平台（Vercel/Railway/AWS）/ 本地？
- 是否需要 CI/CD？

---

## 技术栈组合指南

收集完选型后，根据组合读取对应参考文件：

| 组合           | 参考文件                                                                                                     |
| -------------- | ------------------------------------------------------------------------------------------------------------ |
| React 前端通用 | [references/react-patterns.md](references/react-patterns.md)                                                 |
| Vue 前端通用   | [references/vue-patterns.md](references/vue-patterns.md)                                                     |
| FastAPI 后端   | [assets/project-templates/fastapi-backend-template.py](assets/project-templates/fastapi-backend-template.py) |
| Fastify 后端   | [references/fastify-patterns.md](references/fastify-patterns.md)                                             |
| API 响应规范   | [references/api-patterns.md](references/api-patterns.md)                                                     |
| 类型同步       | [references/type-sync-guide.md](references/type-sync-guide.md)                                               |

---

## 核心原则（所有组合通用）

### Schema-First 开发

始终先定义数据模型，它是前后端的唯一契约：

- FastAPI：Pydantic Schema → 自动生成 OpenAPI → `openapi-typescript` 生成前端类型
- Fastify：Zod/TypeBox Schema → 自动生成 OpenAPI → `openapi-typescript` 生成前端类型

### 架构分层

```
后端: Router → Service → Repository/CRUD → DB Model
前端: Page → Feature Component → Custom Hook → API Layer
```

### 统一响应格式

所有 API 响应遵循 `{ code, message, data }` 结构，详见 [references/api-patterns.md](references/api-patterns.md)。

### 类型同步策略

优先使用 `openapi-typescript` 自动生成，避免手动维护两套类型：

```bash
pnpm add -D openapi-typescript
pnpm openapi-typescript http://localhost:8000/openapi.json -o src/types/api.ts
```

---

## 各框架关键配置速查

### React 19 + Tailwind V4

```bash
pnpm create vite my-app --template react-ts
pnpm add tailwindcss @tailwindcss/vite
```

`vite.config.ts` 中加入 `@tailwindcss/vite` 插件，CSS 文件直接 `@import "tailwindcss"`，无需 `tailwind.config.js`。

React 19 新特性：`ref` 可直接作为 prop 传递（无需 `forwardRef`）；用 `use()` 处理 Promise/Context；表单用 `useActionState`。

### Vue 3.5+ + Tailwind V4

```bash
pnpm create vue@latest my-app  # 选 TypeScript + Vue Router + Pinia
pnpm add tailwindcss @tailwindcss/vite
```

Vue 3.5 新特性：`useTemplateRef()` 替代 `ref` 获取 DOM；Props 解构默认保持响应性（无需 `toRefs`）；`useId()` 生成唯一 ID。

状态管理用 Pinia，数据请求用 TanStack Query for Vue（`@tanstack/vue-query`）。

### FastAPI 后端

Python 3.10+，UV 管理依赖，Ruff 格式化。所有 Schema 继承 `CamelModel`（自动 snake_case → camelCase）。详见模板文件。

### Fastify 后端

Node.js 20+，TypeScript，Zod 做 Schema 验证，Prisma 做 ORM。详见 [references/fastify-patterns.md](references/fastify-patterns.md)。

---

## 编码规范

- **包管理**：统一 `pnpm`
- **Tailwind V4**：CSS-first，`@import "tailwindcss"` + `@theme {}`，无 config 文件
- **TypeScript**：严格模式，避免 `any`
- **Pydantic V2**：`@field_validator`、`model_dump()`
- **SQLAlchemy 2.0**：`select()` 语句
- **TanStack Query**：合理 `staleTime`，mutation 后 `invalidateQueries`
