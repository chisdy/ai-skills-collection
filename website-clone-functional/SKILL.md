---
name: website-clone-functional
description: 给一个网站 URL，分析它的功能架构并产出三份文档——产品需求文档（PRD：角色、用户旅程、功能清单与优先级、用户故事、数据实体）、前端功能信息架构（站点地图、导航、路由表、每页区块与状态、主流程图）、admin 功能信息架构（管理角色与权限矩阵、模块树、每模块的列表 / 表单 / 操作 / 状态流转）。用 Playwright 脚本或 Cursor / Codex 内联浏览器逐页采集导航、表单、按钮、列表、筛选 / 排序 / 分页、登录态、第三方服务与 XHR / fetch 请求，默认拦截所有写请求，每条结论标注实采或推断。只要用户问"这个网站有哪些功能"、"帮我写这个站的 PRD / 需求文档 / 信息架构"、"照着这个产品做一个，先梳理功能"、"这个网站的后台该有什么模块"、"分析竞品的功能结构"、"反推这个站的数据模型 / 用户角色 / 业务流程"，都应使用此技能——即使用户没有说"复刻"两个字。
metadata:
  version: "1.0.0"
  author: chisdy
---

# Website Clone — Functional

回答三个问题：这个网站有什么功能、给谁用、后台需要管什么。方法是先采证再下结论：每个功能点都指向一个页面上的元素或一条网络请求；页面上看不到的按规则推断并明确标出。产出是三份 Markdown 文档，到需求与信息架构为止。

本技能只管功能架构，**不**复刻样式与动画、**不**写页面代码、**不**设计数据库与接口、**不**推进后端。需要像素级视觉复刻请用 `website-clone-visual`；既要功能又要视觉的完整复刻请用主控 `website-clone`。本技能可以单独安装、单独触发、单独跑完。

## 合规边界（开始前确认）

只服务于：学习 / 练习、重建自己拥有的站点、已获授权的复刻、竞品分析与产品研究。开始前用一句话确认用途。硬性规则：

- **采集不得在目标站产生任何写操作**。脚本路径默认拦截所有非 GET / HEAD / OPTIONS 请求（并自检拦截器生效）；两条路径都不提交表单、不点击注册 / 下单 / 评论 / 收藏 / 关注 / 删除等写按钮，表单字段只从 DOM 静态读取。允许的交互只有只读的：Tab、排序、筛选、分页、加载更多、展开折叠。
- `--allow-writes` 只在用户**明确声明**目标是自有站点或测试环境时开启，开启后脚本会打印警告并记录在 `summary.json`。
- 登录墙后的内容只在用户持有账号并授权时采集，由用户自己在内联浏览器里登录（或提供 `--storage-state`）；不绕过验证码、付费墙、反爬。
- `robots.txt` / 服务条款禁止自动化访问且用户不是所有者 → 告知风险由用户决定；可改为内联浏览器逐页人工浏览 + 采集。
- 文档里分析的是功能与信息架构；原站文案、图片、品牌不在复用范围，PRD 末尾有合规声明节。

## 最小问卷（缺什么问什么；主控传来的答案不重复问）

1. **URL 与范围**：首页 URL；只看公开页面还是也要登录后的（个人中心、订单）？大概多少页（默认 BFS 20 页 / 深 3）？
2. **是否有账号 / 后台**：能登录吗（用户自己登录）？有后台 URL 吗（有则 admin IA 改为实采）？
3. **站点类型**：电商 / 内容 / SaaS / 社区，或让脚本判断？
4. **用途与交付**：学习 / 自有重建 / 授权复刻 / 竞品分析；三份文档都要还是只要其一？
5. **是否自有 / 测试站点**（决定能否 `--allow-writes`，默认否）。

## 四步流程

```
1 采集 crawl  →  2 分析 analyze  →  3 写三份文档  →  4 自检交付
```

### 1. 采集

产出固定结构的 `features/` 目录（`references/capture-guide.md` §1 有逐文件说明），无论用哪条路径：

```
features/
  site-map.json  network.json  summary.json
  <page-id>/page.json  links.json  probes.json
  features.json  features-summary.md          ← 第 2 步产出
```

页面内提取逻辑全部在 `scripts/collect/`：`features.js`（导航 / 表单 / 按钮读写分类 / 列表字段 / 表格 / 筛选排序搜索分页 Tab / 登录态与角色线索 / 多语言货币 / 互动点 / 第三方 / JSON-LD / 实体线索）、`links.js`（同域链接）、`network.js`（内联路径的请求补充）、`_read.js`（MCP 分片读取）。两条路径注入同一批文件。

| 环境 | 走哪条 |
|---|---|
| 能跑 Python + Playwright | **路径 A** 脚本（默认）：自带 BFS、网络记录、写请求拦截、只读探测 |
| 需登录 / 反爬 / 装不上 Playwright / 想边看边采 | **路径 B** 内联浏览器（`cursor-ide-browser` 或 Playwright MCP）：用户登录后模型逐页注入采集 |
| 两者都有 | A 采公开页 + B 采登录后页（`save_page.py --login-wall`），落同一个 `features/` |
| 都没有 | `curl` 拿 HTML 人工读 + 用户截图，明确告知只能做粗粒度分析 |

**路径 A**

```bash
python3 -m venv /tmp/wc-venv && /tmp/wc-venv/bin/pip install -r scripts/requirements.txt && /tmp/wc-venv/bin/playwright install chromium
/tmp/wc-venv/bin/python scripts/crawl_features.py <url> -o features/ [--max-pages 20] [--storage-state state.json] [--admin-url <后台 URL>]
```

也接受外部 `site-map.json`（主控 `discover_site.py` 的产物或手写清单）。脚本每页：加载 → 滚动 → 注入 `features.js` / `links.js` → 只读探测（Tab / 排序 / 筛选 / 分页 / 加载更多，记录触发的接口与 URL 变化）→ 落盘；全程 `page.route` 拦截写请求并在开头自检。看到 `[WARN] discover 只发现了 1 页` 时不要继续，先换发现方式（加大 `--wait`、内联浏览器展开菜单后手写 `site-map.json`）。

**路径 B**：按 `references/capture-guide.md` §3 的操作序列（cursor-ide-browser 与 Playwright MCP 两张表）。每页 `Runtime.evaluate` / `browser_evaluate` 注入三个脚本 → `python3 scripts/save_page.py features/ --page <文件> --links <文件> --network <文件>`。没有 `page.route` 保护，**靠不点写按钮保证零写操作**——点任何东西前先 `browser_snapshot` 确认它是 Tab / 排序 / 分页而不是提交 / 加购 / 收藏。

### 2. 分析

```bash
python3 scripts/analyze_features.py features/ [--site-type ecommerce|content|saas|community]
```

仅标准库。产出 `features.json`（功能点 / 实体 / 角色 / 流程 / API / admin 反推 / 假设，每条带 `sources` 与 `basis: 实采 | 推断`）与 `features-summary.md`。规则在 `references/feature-taxonomy.md`（功能归类与优先级）、`entity-inference.md`（实体 / 关系 / 角色 / 流程）、`admin-inference.md`（后台反推）、`network-to-api.md`（网络记录怎么读）。

**先读 `features-summary.md`**，需要细节再按 `pageId` 查 `page.json`、按 path 查 `network.json`；`page.json` 单个 20–80 KB，不要全部读进上下文。分析结果要过一遍 `entity-inference.md` §5 的误判清单（占位实体、动词路径、表单字段映射错实体）再写文档。

### 3. 写三份文档

**先找已安装的文档技能，有就用它写，没有才用本技能的模板兜底**（规则与匹配表在 `references/doc-writing.md` §0）。按顺序查：上下文 `<available_skills>` → AGENTS.md 技能表 → `openskills list` → 环境暴露的子代理。名称或描述命中 PRD / 需求文档 / product requirements / spec / brainstorming / writing-plans / 信息架构 / user story / 文档协作（例如 `superpowers` 的 `brainstorming` / `writing-plans`、`doc-coauthoring`、`story-generator`、`ui-sketcher`）的即为候选，每份文档最多加载一个主写技能 + 一个补充技能，不安装新技能。

委派给文档技能时不变的三件事：**输入**是 `features.json`（证据集，不让文档技能自己去猜功能）；**输出**文件名与位置不变（`PRD.md` / `frontend-ia.md` / `admin-ia.md`）且必须覆盖模板的必备节（`doc-writing.md` §2–4 的节表就是验收清单，缺节按模板补）；**每张表的"依据"列与合规声明**不可省——这是本技能的纪律，不随文档技能的风格变。文档技能若要求交互式头脑风暴（如 `brainstorming`），把问卷答案与 `features-summary.md` 作为已知上下文喂给它，不重复向用户提问。

兜底路径：模板在 `assets/templates/`，规则在 `references/doc-writing.md`。顺序：`PRD.md` → `frontend-ia.md` → `admin-ia.md`（后两份引用 PRD 的功能 ID）。

- 每张表都有"依据"列（实采 / 推断 / 实采 + 推断）；实采写得出来源页面 / 元素 / 接口；推断只补常规产品逻辑必然有的东西
- PRD：概述与未覆盖范围 → 角色 → 3–6 条用户旅程（Mermaid）→ 功能清单按 12 个模块分组、MoSCoW → Must / Should 的用户故事与验收 → 页面清单 → 实体 erDiagram → 非功能 → 假设 → 合规声明
- 前端 IA：站点地图（推断页虚线）→ 导航登录前 / 后 → 路由表（参数来自只读探测观察到的 URL）→ 每页区块 + **状态表**（默认 / 空 / 加载 / 错误 / 登录态）→ 全局组件 → 主流程图 → 前台权限矩阵
- admin IA：开头声明全推断 / 部分实采 → 角色与权限矩阵 → 模块树 → 每模块列表 / 表单 / 操作 / 状态机（stateDiagram）→ 与前台映射 → 待确认。有后台实采时用 `navigation.side` 与 `tables[].headers`

产出位置：用户项目里 `docs/`（主控委派时为 `clone-package/docs/`）。

### 4. 自检交付

- [ ] `summary.json.network.allowWrites == false`（或用户确认过自有站点），`blocked ≥ 1`（自检生效）
- [ ] 写文档前查过已安装的文档技能；用了哪个（或"未找到，用模板兜底"）写进交付说明
- [ ] 三份文档每张表有依据列；没有一条推断写成事实（无论由哪个技能写）
- [ ] PRD 功能 ID 在两份 IA 里能对上；PRD §1 写了未覆盖范围（登录墙后页数）
- [ ] 没有页面代码、没有接口定义、没有表结构（那些不是本技能的产出）
- [ ] 交付语：文档到需求层为止；要继续做请另起任务用 `website-clone-visual`（视觉）或 `fullstack-expert` / `master-architect-workflow`（开发）

## 速查

| 想知道 | 看哪 |
|---|---|
| 站点有哪些功能、优先级 | `features-summary.md` 功能点表 → `features.json.features[]` |
| 某功能在哪页哪个元素 | `features[].sources[]` → `<page-id>/page.json` 的 `forms` / `buttons` / `controls` |
| 实体与属性来源 | `features.json.entities[].attributes[*].sources` |
| 接口与响应结构 | `features.json.api[]` → `network.json.entries[]`（`responseShape` / `responseSample`） |
| 筛选 / 排序是前端还是接口 | `<page-id>/probes.json`：`requests: 0 + urlChanged` = 前端 |
| 哪些页要登录 | `site-map.json.pages[].loginWall`、`page.json.redirectedToLogin` |
| 第三方服务（支付 / 统计 / 客服） | `page.json.thirdParty[]` |
| 后台该有什么 | `features.json.admin` → `references/admin-inference.md` |
| 有没有产生写操作 | `summary.json.network`、`network.json.blocked` 条目 |

## 常见误判

- **登录页 ≠ 登录墙**：`pageType: auth` 是登录页本身；`loginWall` / `redirectedToLogin` 才是"这页需要登录"。
- **`interactions.cart: true` 不等于完整购物车功能**：只表示有入口；数量修改 / 移除 / 汇总要在结算页实采到才标实采。
- **读接口用 POST 被拦**：列表为空 + 大量 blocked 同域 POST → GraphQL 或 POST 列表接口；告知用户，自有站点才 `--allow-writes`，否则内联浏览器路径。
- **API 路径的动词当实体**：`/api/search`、`/api/config` 不是实体，删掉。
- **`Item` 占位实体**：列表无价格 / 评分 / 日期时的默认名；按列表标题改名或删除（静态卖点区块不是实体）。
- **页面类型全 content**：URL 无语义，按 `h1` / `lists` / `forms` 手改 `site-map.json` 的 `type` 再重新分析。
- **roleHints 误报**："专业版（pro）"、"合作伙伴（partner）"文案会被当角色线索，核对上下文。
- **`.json` 静态文件当真实 API**：说明是静态站 / mock，PRD 里注明"真实实现需接口"标推断。
- **只读探测超时**：控件被遮挡；不影响静态采集，`--no-probe` 或内联浏览器手动探。
- **只发现 1 页**：SPA 导航交互后才渲染；不要就这一页写文档。

## 参考索引

- `references/capture-guide.md`：`features/` 逐文件说明；脚本参数；内联浏览器两张工具映射表与操作序列；完整性自检
- `references/feature-taxonomy.md`：12 个功能模块的归类与 MoSCoW 默认规则；`features.js` 识别规则速查
- `references/entity-inference.md`：实体 / 关系 / 角色 / 流程的来源与可信度；误判修正
- `references/admin-inference.md`：实体 → CRUD、行为 → 管理与报表、固定模块；默认状态机；有后台实采时怎么写
- `references/network-to-api.md`：`network.json` 字段、拦截机制、从请求读出 API 与分页 / 筛选参数
- `references/doc-writing.md`：先找文档技能（匹配表、加载方式、委派时的不变量）；三份文档逐节的数据来源与写法；常见误判
- `assets/templates/`：`PRD.md`、`frontend-ia.md`、`admin-ia.md`
- `scripts/`：`crawl_features.py`、`analyze_features.py`、`save_page.py`（内联路径落盘）、`collect/features.js` / `links.js` / `network.js` / `_read.js`、`requirements.txt`
