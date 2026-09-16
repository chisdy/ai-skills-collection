# 三份文档的写作规则

模板在 `assets/templates/`，数据在 `features/features.json`（先读 `features-summary.md` 摘要）。文档是给产品 / 设计 / 开发看的需求层产物，不是采集结果的转录。

## 0. 先找已安装的文档技能，没有才用模板兜底

本技能擅长的是"采证与推断"，不是"把需求写得好看"。环境里如果已经装了专门写 PRD / 规格 / 用户故事的技能，让它来写，本技能只负责喂证据和验收。

### 0.1 查找顺序（先命中先用）

1. 上下文里的 `<available_skills>` 列表（名称 + 描述）
2. AGENTS.md / CLAUDE.md 的技能表
3. `openskills list`（该 CLI 存在时）
4. 环境暴露的子代理（`story-generator`、`ui-sketcher`、`dev-planner` 一类）

只在已列出的范围内匹配，不扫文件系统、不安装任何技能（推荐安装最多在交付说明里写一句）。

### 0.2 匹配表

| 文档 | 命中词（名称或描述含其一） | 常见例子 | 角色 |
|---|---|---|---|
| PRD.md | PRD、需求文档、product requirements、spec / specification、brainstorming、writing-plans、design doc | `superpowers` 的 `brainstorming`（把想法变成设计文档）与 `writing-plans`；`doc-coauthoring`；名为 `prd` / `product-spec` 的技能 | 主写 |
| PRD.md §5 用户故事 | user story、用户故事、acceptance criteria、验收标准 | `story-generator` 子代理；`ui-sketcher` | 补充（只写 §5，合并回 PRD） |
| frontend-ia.md | 信息架构、information architecture、sitemap、user flow、用户流程、UI blueprint | `ui-sketcher`（区块与用户旅程）；`doc-coauthoring` | 主写 |
| admin-ia.md | 同 frontend-ia，另加 admin / 后台 / dashboard 设计 | 一般没有专门技能，多为模板兜底 | 主写 |

预算：每份文档最多一个主写技能 + 一个补充技能。多个候选时优先：项目本地 > 全局；描述与"写需求 / 规格文档"直接相关 > 泛用文档协作；已在上下文加载的 > 需要新读的。落选的候选名写进交付说明。

排除：只做开发计划 / 任务拆分的（`dev-planner`、`writing-plans` 用于实现计划时）、会生成代码的、会安装东西的，不作为 PRD 主写；代码评审 / 测试类不相关。

### 0.3 怎么加载与委派

- 加载：Read 候选的 `SKILL.md`（`<available_skills>` 给的路径），或 `openskills read <name>`；子代理用 Task 启动。读完再判断它的输入输出形态是否适合，不合适就回到模板。
- 交给它的上下文：问卷答案（用途 / 站点类型 / 账号后台）、`features-summary.md` 全文、需要时 `features.json` 的对应段（`features[]` / `entities[]` / `flows[]` / `admin`）、本文件 §2–4 对应文档的节表（作为它的输出结构约束）。
- 交互式技能（`brainstorming` 会逐个问问题）：把上面的上下文当作"已知答案"先给它，让它只问 `features.json` 回答不了的问题（如商业目标、目标用户画像），不重复问站点有什么功能——那是证据里已有的。
- 子代理产出（如 `story-generator` 的故事列表）：验证每条能对应一个功能 ID，再合并进模板格式的 §5；对应不上的丢弃或标推断。

### 0.4 委派时不变的三件事

1. **输入只有证据**：文档技能不得自己"想象"站点功能；功能清单、实体、流程以 `features.json` 为准，它可以改写措辞、补结构、写目标与价值，不能新增 `features.json` 里没有且不标推断的功能。
2. **输出的文件名、位置、必备节不变**：`docs/PRD.md` / `frontend-ia.md` / `admin-ia.md`；§2–4 的节表是验收清单，文档技能漏的节按模板补齐；PRD 功能 ID 仍要在两份 IA 里可对应。
3. **依据列与合规声明不变**：每张表有"依据"列（实采 / 推断 / 实采 + 推断），admin IA 开头的推断声明与 PRD 末尾的合规声明必须在。文档技能的风格再好，把推断写成事实就是不合格。

写完由本技能过一遍 §5 的误判清单和 SKILL.md 第 4 步的自检，再交付。交付说明里写明：用了哪个技能写哪份文档、哪些节由模板补齐、或"未找到文档技能，全部按模板"。

## 1. 通用规则

- **每张表必有"依据"列**，值只能是 `实采` / `推断` / `实采 + 推断`（部分字段实采、部分推断）。文档开头一句解释这两个词。
- **实采要能回溯**：功能点写"来源页面 / 元素"（`login.html` form[action=/api/login]），实体属性写来源（API `/api/products.json` 响应字段、结算表单字段），流程步骤写页面。`features.json` 里每条都有 `sources[]`，照抄第一条即可，多来源时挑最有代表性的（首页 > 列表 > 详情 > 其他）。
- **推断要克制**：只补"常规产品逻辑必然存在"的东西（支付成功页、404、空态、表单错误提示、后台用户管理）。原站没有证据的增值功能（积分、推荐算法、分销）不写进功能清单，最多在"待确认"提一句。
- **不写视觉**：颜色、字号、间距、动画归 `website-clone-visual`。"区块"在 IA 里只描述内容与交互，不描述样式。
- **不写技术方案**：不选框架、不设计表结构（erDiagram 是概念模型不是 DDL）、不写接口定义（API 清单可作为附录列出观察到的接口路径与参数，标实采）。
- **不写页面代码**：本技能的产出只有文档。
- **Mermaid 图**：站点地图 / 流程用 `flowchart`，实体用 `erDiagram`，状态用 `stateDiagram-v2`。推断节点用虚线（`-.->`）或名字后加 ` ?`。节点文字含括号、斜杠时用引号包住。
- **中文**，与仓库其他技能一致；实体名与字段名保留英文。
- 站点名不知道时用 `document.title` 的公共部分或域名。

## 2. PRD.md

| 节 | 数据来源 | 要点 |
|---|---|---|
| 1 概述 | `siteType`、首页 `h1` / `description`、`pages` 统计 | 一句话定位是推断，说清楚；"未覆盖"必写 |
| 2 角色 | `roles[]` | 管理员永远在，标推断并指向 admin-ia |
| 3 旅程 | `flows[]` | 3–6 条；每条一张 flowchart + 步骤表；`basis: 推断` 的步骤加 `?` |
| 4 功能清单 | `features[]` 按 `module` 分组 | ID 沿用 F001…；描述用一句话说清"用户能做什么"，不复述 DOM；空模块不列 |
| 5 用户故事 | Must / Should 功能点 | 每条 ≥ 2 条验收 + 边界；§0 找到的用户故事技能 / 子代理可扩写，仍合并到本节格式 |
| 6 页面清单 | `pages[]` + 推断页 | URL 写成模式（`/product?id=`），登录要求一列 |
| 7 实体 | `entities[]` | erDiagram + 表；`?` 标推断属性；删掉 `Item` 一类占位实体（见 entity-inference §5） |
| 8 非功能 | `jsonLd` / `openGraph` / `i18n` / `thirdParty[captcha]` / `legal` 页 | 原站有证据的标实采，行业基线标推断 |
| 9 假设 | `assumptions[]` + 写作中新增的 | 每条写影响范围与谁确认 |
| 10 合规 | 问卷答案 | 用途、写请求拦截声明、版权说明 |

## 3. frontend-ia.md

| 节 | 数据来源 | 要点 |
|---|---|---|
| 1 站点地图 | `pages[]` + `navigation.main` + 推断页 | 实采页实线，推断页虚线 |
| 2 导航 | 首页 `navigation.main / footerGroups`、`auth.links`、`i18n.langSwitch` | 登录前 / 后两列——登录后形态多为推断 |
| 3 路由表 | `pages[].url` + `probes[].urlAfter` 里的参数 + 表单 `action` | 参数来自只读探测观察到的 URL 变化（实采） |
| 4 每页 IA | 每页 `page.json`：`lists` / `forms` / `controls` / `buttons` / `interactions` / `tables` / `headings` | 区块按页面 DOM 顺序；数据来源列填 `api[]` 里该页触发的接口；**状态表必写**（空 / 加载 / 错误 / 登录态），几乎全是推断 |
| 5 全局组件 | `controls.modals`、`interactions.chatWidget`、Toast（推断） | — |
| 6 主流程图 | `flows[]` | 与 PRD §3 同源，这里画得更细（分支、错误） |
| 7 权限矩阵 | `roles[].can` | 访客点写按钮时的"→ 登录"多为推断 |

## 4. admin-ia.md

| 节 | 数据来源 | 要点 |
|---|---|---|
| 开头声明 | `admin.basis` | 全推断 / 部分实采 |
| 1 角色与矩阵 | `admin.roles` | 全推断 |
| 2 模块树 | `admin.modules[]`；有后台实采时 `navigation.side` | — |
| 3 模块详情 | 每个 `admin.modules[]`：`list.columns / filters / batch`、`form.fields`、`actions`、`states` | 每模块最后一行"依据"；stateDiagram 按 `states`；用户管理不显示密码 |
| 4 与前台映射 | `features[]` ↔ `admin.modules[]` | 一张表 |
| 5 待确认 | 后台是否存在、审核流程、订单状态定义 | — |

规则见 `admin-inference.md`。

## 5. 常见误判

- **把采集字段当功能**：`interactions.cart: true` 只是"页面有购物车入口"，功能点要写成"购物车：查看 / 修改数量 / 移除 / 金额汇总"（后半句在结算页实采到才写，否则标推断）。
- **把 fixture / 静态 JSON 当真实 API**：`.json` 静态文件说明是静态站或 mock，PRD 里写"数据来源为静态 JSON，真实实现需接口"标推断。
- **登录页不是登录墙**：`pageType: auth` 是登录页；`loginWall` / `redirectedToLogin` 才表示某页需要登录。
- **列表页的多个 `lists`**：可能包含筛选组（radio 列表）、卡片网格、页脚链接——按 `fields` 与 `itemHasPrice/Image` 判断哪个是内容列表。
- **前端筛选写成服务端接口**：探测 `requests: 0` 且 `urlChanged: true` 是前端过滤；路由表参数仍可列（URL 同步了），但数据来源写"前端过滤"。
- **多语言 / 多货币只看符号**：`currencies` 只有 `¥` 不算多货币；`langSwitch` 有两项以上才算多语言。
- **roleHints 误报**：文案里的"专业（pro）"、"合作伙伴（partner）"会被当角色线索——核对上下文再决定要不要写成角色。
- **推断写成事实**：模板里凡是模型补的步骤、状态、模块，依据列必须是"推断"；宁可多标推断。
