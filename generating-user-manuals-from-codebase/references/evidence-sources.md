# 证据源查找表：各类事实在代码里的位置

阶段 1 用。先识别技术栈（§0），再按 §1–§7 逐类提取，填 `_inventory.md`。每类都有一列「能证明什么 / 不能证明什么」——这是防止把代码推断写成事实的边界。用 Grep 时优先 `rg`，关键词按栈选。表中 grep 列是可直接执行的 `rg` 命令：多个候选用多个 `-e`（等价于"或"，刻意不用 `|`，因为它既会被 Markdown 表格吞掉、又与 BRE 的 `\|` 混淆），正则按 rg / Rust 语法，自行在末尾追加搜索路径。

## 0. 识别技术栈

| 看什么 | 结论 |
|---|---|
| `package.json` 的 `dependencies` | `react` / `react-router` / `next` → React 系；`vue` / `vue-router` / `nuxt` → Vue 系；`@angular/core` → Angular；`svelte` / `@sveltejs/kit` → Svelte；`electron` → 桌面；`commander` / `yargs` / `oclif` → CLI |
| `pubspec.yaml` | Flutter（`go_router` / `auto_route` 为路由） |
| `*.xcodeproj` / `Package.swift` / `build.gradle` | 原生移动端（SwiftUI / UIKit / Compose） |
| `go.mod` + `cobra` / `urfave/cli`；`pyproject.toml` + `click` / `typer` / `argparse` | CLI |
| 后端：`fastapi` / `django` / `express` / `fastify` / `spring-boot` / `gin` | 决定 §4 / §6 后端校验与错误表的位置 |
| 已有 `docs/`、`README.md`、`CHANGELOG.md`、`*.stories.*` | 第二级来源，先读一遍 |

多包仓库（`apps/`、`packages/`、`pnpm-workspace.yaml`）先确定用户要写的是哪个应用。

## 1. 功能与入口

**能证明**：功能存在、URL / 菜单路径、层级关系、是否需要登录（守卫）。
**不能证明**：菜单上显示的文字（去 §2）、功能是否对所有角色可见（去 §3）、是否已上线（查 feature flag，§7）。

| 栈 | 位置 | grep |
|---|---|---|
| React Router | `routes.tsx` / `router.tsx` / `createBrowserRouter` / `<Route path=` | `rg -e createBrowserRouter -e '<Route\b' -e 'path:'` |
| Next.js | `app/**/page.tsx`（目录即路由）、`pages/**/*.tsx`；`layout.tsx` 里的导航 | `fd page.tsx app/`；`href=` |
| Vue Router | `router/index.ts` 的 `routes` 数组；`meta` 字段常带标题 key 与权限 | `rg -e 'path:' -e 'component:\s*\(\)\s*=>\s*import'` |
| Nuxt | `pages/**/*.vue`（目录即路由）、`definePageMeta` | `definePageMeta` |
| Angular | `*-routing.module.ts` / `app.routes.ts` 的 `Routes` | `rg -e 'path:' -e canActivate` |
| SvelteKit | `src/routes/**/+page.svelte` | `fd +page.svelte` |
| Flutter | `GoRouter(routes:` / `@RoutePage` / `Navigator.pushNamed` | `rg -e 'GoRoute\(' -e 'pushNamed\('` |
| 原生移动 | `TabView` / `NavigationStack` / `UITabBarController` / `NavHost` | `rg -e NavigationLink -e 'composable\('` |
| Electron | `Menu.buildFromTemplate` / `MenuItem` | `Menu.buildFromTemplate` |
| CLI | `program.command(` / `@click.command` / `cobra.Command{` / `add_parser(` | 同左 |
| 菜单 / 导航配置 | `menu.ts` / `nav.ts` / `sidebar.ts` / `navigation.json`，或布局组件里的 `<NavLink>` / `<el-menu-item>` / `<a-menu-item>` | 文件名含 `menu` / `nav` / `sidebar`：`fd -i -e ts -e js -e json 'menu|nav|sidebar'` |

功能 ID 建议用 `<模块>-<动作>`（`orders-export`、`users-invite`），全书统一。

## 2. 界面文案（唯一合法的"按钮叫什么"来源）

**能证明**：按钮、标题、占位符、提示、确认框、空状态的实际文字。
**不能证明**：这段文案当前是否真的渲染（可能是废弃 key）；多个候选 key 时哪一个在这个位置——要么顺着 `t('key')` 反查到组件，要么阶段 2 实采。

| 形式 | 位置 | 怎么用 |
|---|---|---|
| i18n JSON / YAML | `locales/`、`i18n/`、`lang/`、`messages/`、`public/locales/`、`src/i18n/` 下的 `zh-CN.json` / `en.json` / `*.yaml` | 以输出语言对应的文件为准；先建立 key → 文本表，再在组件里 grep key |
| `react-i18next` / `vue-i18n` / `next-intl` / `@ngx-translate` | 组件里 `t('module.key')`、`$t('...')`、`useTranslations('ns')`、`{{ 'key' \| translate }}` | 用 key 反查文件，确认在哪个组件哪个位置 |
| ICU / gettext | `*.po` / `*.pot`、`messages.properties`、`*.arb`（Flutter）、`Localizable.strings` / `.xcstrings`（iOS）、`strings.xml`（Android） | 同上 |
| 无 i18n | 模板 / JSX 里的字面文本：`<Button>导出</Button>`、`label="邮箱"`、`placeholder=` | 直接 grep 中文 / 英文字面；注意同一字面可能出现在多处 |
| 确认框 / toast | `Modal.confirm({ title:`、`confirm(`、`message.success(`、`toast(`、`ElMessageBox.confirm` | 这些是"警告紧贴动作"要引用的原文 |
| 空状态 / 加载 | `<Empty description=`、`emptyText`、`loadingText` | 阶段 4 的"结果"与"出现问题时"会用到 |

同一功能在 i18n 里有多个候选文案（如 `upload.button` 与 `upload.title`）时，标记 `待实采` 而不是挑一个。

## 3. 权限与角色

**能证明**：某入口 / 动作要求某角色或权限点；角色名的集合；管理员有哪些独占菜单。
**不能证明**：没写守卫的入口就是所有人可见（可能在后端或网关拦）；某角色**不能**做某事（除非有显式拒绝分支）。写正文时只写"已验证的边界"——谁可以、被拦的人看到什么。

| 位置 | grep |
|---|---|
| 路由 `meta.roles` / `meta.permission` / `requiresAuth` / `canActivate` / 路由级 `<ProtectedRoute>` | `rg -e 'roles:' -e permission -e requiresAuth -e ProtectedRoute -e RequireAuth` |
| 组件级：`hasPermission(` / `can(` / `usePermission` / `v-permission` / `v-if="isAdmin"` / `<Can I=` | 同左 |
| 角色枚举与权限点常量 | `rg -e 'enum Role' -e 'ROLES\s*=' -e 'PERMISSIONS\s*=' -e 'const permissions'` |
| 后端：`@PreAuthorize` / `@permission_required` / `Depends(require_role` / `@Roles(` / casbin 策略 / `policy.csv` | 同左 |
| 菜单配置里的 `roles` / `hidden` 字段 | 结合 §1 |

产出一张权限矩阵草表（功能 × 角色 → 可 / 不可 / 未知），`未知` 在阶段 2 实采或进编辑备注。

## 4. 限制（文件类型、大小、数量、长度、格式、频率）

**能证明**：前端校验规则里写死的值；后端校验里的值；两者不一致时以更严的为"实际会被拦"的值，并在编辑备注记录不一致。
**不能证明**：没写校验就没限制（可能在网关 / 对象存储 / 数据库列长度上）。没找到的写"未见限制说明"进编辑备注，不写"无限制"。

| 位置 | grep |
|---|---|
| zod / yup / valibot / joi | `rg -e 'z\.string\(\)' -e 'z\.number\(\)' -e 'z\.object\(' -e 'yup\.' -e 'Joi\.'` |
| vee-validate / vuelidate / async-validator（antd / Element 的 `rules`） | `rg -e 'rules\s*[:=]' -e 'required:\s*true' -e 'max:\s*\d' -e 'pattern:'` |
| HTML 属性 | `rg -i -e 'accept=' -e maxlength -e 'min=' -e 'max=' -e 'step=' -e required` |
| 上传组件 props | `rg -e maxSize -e maxCount -e 'limit=' -e beforeUpload -e 'accept=' -e fileSize` |
| 常量文件 | `rg -e 'MAX_\w+\s*=' -e 'LIMIT\s*=' -e 'ALLOWED_\w+\s*='` |
| 后端：Pydantic `Field(max_length=` / `constr(` / `conint(`；class-validator `@MaxLength(` / `@IsEmail(`；Django `max_length=`；Spring `@Size(` / `@Max(`；Go `binding:"max=` | 同左 |
| 分页与频率：`pageSize` 默认值、`rateLimit` / `throttle` | `rg -e pageSize -e per_page -e rateLimit -e throttle` |

记录时保留原始单位（`10485760` 字节写成 10 MB 并注明换算来源）。

## 5. 状态与流转

**能证明**：有哪些状态值；每个值在界面上显示成什么文字 / 颜色（若有展示映射）；允许的转移（若有状态机）。
**不能证明**：状态转移由谁触发、要多久（除非代码里有定时器 / 队列配置且可读到）。"处理中一般几分钟"这种话没有证据就不写。

| 位置 | grep |
|---|---|
| 枚举 | `rg -e 'enum \w*Status' -e 'enum \w*State' -e 'as const'` 后面的状态对象 |
| 展示映射 | `rg -e statusMap -e STATUS_LABEL -e statusText -e statusColor -e '<Tag color=' -e '<Badge status='` |
| 状态机 | `xstate` / `createMachine` / `transitions` / 后端 `django-fsm` / `transitions` 库 |
| 后端状态字段 | 模型里的 `status = Column(Enum(` / `choices=` |

产出：状态表（值 → 界面文字 → 含义 → 从哪来到哪去），进 Reference 书架的"状态说明"。

## 6. 错误与恢复

**能证明**：用户会看到的错误提示原文；错误码与提示的对应；有没有重试按钮 / 重新上传入口。
**不能证明**：错误的根因解释（正文只写现象与已验证的恢复动作）；"联系管理员"是否真有效（无证据就写"联系支持"）。

| 位置 | grep |
|---|---|
| 错误码映射 | `rg -e errorMessages -e 'ERROR_\w+' -e errorCode -e 'code:\s*\d+'` 附近的文案对象 |
| 全局错误处理 | axios / fetch 拦截器里的 `message.error(` / `toast.error(`、`ErrorBoundary`、Vue `errorHandler` |
| 表单错误提示 | §4 校验规则的 `message:` 字段 |
| 后端错误表 | `class \w+Exception` / `HTTPException(status_code=` / `errors.New(` / `@ExceptionHandler`；统一错误码文件 |
| 重试 / 恢复入口 | `rg -e retry -e 重试 -e 重新上传 -e onRetry` |

产出：错误对照表（界面原文 → 什么情况出现 → 用户能做什么），进 Troubleshooting 书架。

## 7. 其他

| 事实 | 位置 | 注意 |
|---|---|---|
| Feature flag | `featureFlags` / `flags.ts` / `unleash` / `launchdarkly` / `posthog.isFeatureEnabled` / 环境变量 `VITE_ENABLE_*` | 查默认值；默认关闭的功能不写进正文，或写"若已启用" |
| 默认值 | 表单 `initialValues` / `defaultValue` / store 初始 state / 后端模型 `default=` | 只写代码里能读到的默认值 |
| 快捷键 | `useHotkeys` / `Mousetrap` / `@keydown` / `accelerator:`（Electron） | 进 Reference 书架 |
| 通知 / 邮件 | `sendMail` / `notify(` / 模板文件 `templates/email/` | 只有找到发送代码才能写"系统会发送邮件" |
| 保留期 / 定时任务 | `cron` / `celery beat` / `setInterval` / `retention` | 只有找到调度代码与参数才能写具体时长 |
| 已有产品文档 | `README.md`、`docs/`、`CHANGELOG.md`、Storybook 的 `*.stories.*`、注释里的 `@description` | 第二级来源；与代码冲突时以代码为准并记冲突 |

## 8. 填表规则

- 一行一个用户可感知的功能（"导出订单"），不是一行一个组件。
- `证据` 列写 `路径:行号`，多个来源用 `;` 分隔；阶段 2 实采后追加截图路径与日期。
- `验证状态` 初值一律 `仅代码`；只有 `browser_snapshot` 或截图看到过才改 `实采`；有冲突或找不到写 `待确认`。
- 找不到的事实**不留空**，写 `未见`，并在编辑备注里说明这条为什么重要。
- 表填完后过一遍 SKILL.md 的「常见误判」。
