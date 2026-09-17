# 手册结构：内容模型、大纲、确认关卡、输出格式

阶段 3 用（生成 `_outline.md`、给用户确认），阶段 5 用（结构检查与格式输出）。

## 1. 四架书内容模型

顶层按读者意图分四架书 + 附录，两级导航，页面标题动词开头（"导出订单"而不是"订单导出功能"）。一个页面只属于一架书：概念、步骤、排障不混在同一页——一页里既讲概念又给步骤又列错误，就拆成三页互相链接。

| 书架 | 读者在问 | 放什么 | 页面模板 |
|---|---|---|---|
| **定向 Get Started** | 这是什么、从哪开始 | 关于本手册；产品概览；快速开始；核心概念与术语 | 概览页 / 快速开始页 |
| **使用 Guides** | 我要做 X，怎么做 | 按任务分组的操作指南；设置与账户；管理员指南（单独一组） | 任务页（`feature-guide.md`） |
| **理解 Reference** | 这个选项是什么意思、有什么限制 | 设置项参考；权限矩阵；限制汇总；状态说明；快捷键 | 参考表页 |
| **恢复 Troubleshooting** | 出问题了怎么办 | 按症状索引的排障；错误提示对照表；FAQ；何时联系支持 | 症状页 / 对照表页 |
| **附录** | — | 术语表；版本 / 变更说明；编辑备注（不发布） | — |

### 1.1 每类页面的必备节

大纲里给每节标 `必有` / `视功能而定`。**没有事实支撑的节直接省略，不留空、不写"暂无"。**

**关于本手册**（必有，短）：覆盖的产品版本与日期；读者与角色；不覆盖什么、去哪找；符号约定（警告 / 提示 / 角色标记）。

**产品概览**（必有）：一段话说产品帮读者做什么；主界面区域图（一张，编号标出 ≤ 4 个区域）；主要状态或模式（若有）。

**快速开始**（必有）：前置条件（账号 / 权限 / 安装）；首次登录或配置；**一条完整走通核心价值的流程**（3–8 步）；"怎么知道成功了"；下一步去哪。

**核心概念与术语**（视功能而定）：只写读者不理解就无法操作的概念（"工作区"、"审批流"）；每条 1–3 句；与术语表互链。

**任务页**（使用书架的每一篇，结构见 `guide-writing.md` §4）：前置条件 → 编号步骤 → 结果 → 变体 / 后续 → 出现问题时。角色路径不同时：差异小用权限表一句话说明，差异大拆成分角色小节。

**设置与账户**（视功能而定）：个人资料、密码 / 安全、通知偏好、语言 / 主题；每个设置项进 Reference 的设置项参考，这里只写"怎么改"。

**管理员指南**（有管理员角色时必有，单独一组）：团队 / 成员 / 邀请；角色与权限分配；系统配置；集成；审计 / 日志。读者是管理员，仍然不暴露实现。

**设置项参考**（视功能而定）：表格——设置项 / 作用 / 可选值 / 默认值 / 生效范围 / 谁能改。

**权限矩阵**（有多角色时必有）：功能 × 角色 → 可 / 不可；被拦时看到什么；来自 `_inventory.md` 的角色表与 `ui-verification.md` §3 的分角色实采。

**限制汇总**（必有，哪怕只有两条）：文件类型 / 大小 / 数量 / 长度 / 频率 / 保留期，每条注明适用位置；来自校验规则。

**状态说明**（有状态枚举时必有）：状态 / 界面显示 / 含义 / 怎么进入 / 怎么离开。

**排障**（必有）：按症状组织——"看不到 X 按钮"、"上传后一直显示处理中"；每条：症状 → 可能原因（只写已验证的）→ 恢复动作 → 仍不行时联系谁。

**错误提示对照表**（有错误映射时必有）：界面原文 / 什么情况出现 / 用户能做什么。

**FAQ**（视功能而定）：只放已验证答案；未知项不进 FAQ。

**术语表**（有核心概念页时必有）：术语 / 定义 / 出现在哪。

**版本 / 变更说明**（更新已有手册时必有）：本次手册变更对应的产品变更；哪些页改了。

## 2. 分组决策

| 情况 | 怎么分 |
|---|---|
| 单角色、功能 ≤ 15 | 使用书架直接按任务列，不再分组 |
| 单角色、功能 > 15 | 按用户目标分组（"管理订单"、"处理退款"），每组 3–8 篇；不按产品菜单原样照搬 |
| 多角色、路径基本相同 | 共用任务页 + 权限矩阵；差异处一句话"仅管理员可见" |
| 多角色、路径差异大 | 使用书架按角色分两组（"用户指南" / "管理员指南"），共用的放前面 |
| 多产品 / 多端 | 每端一本，共用定向与附录；不要在一页里"Web 端这样、App 端那样"交替 |
| 更新已有手册 | 不重排已有目录；新功能插到对应组，改动的页只改受影响节；在变更说明里列出 |

## 3. `_outline.md` 写法

模板在 `assets/templates/manual-outline.md`。头部：

```yaml
status: draft            # draft | confirmed；用户确认后改 confirmed
confirmed_at:            # 确认日期，用户或 agent 填
source_inventory: docs/manual/_inventory.md
product_version:         # 覆盖的产品版本 / commit
output_format: markdown-multi   # markdown-single | markdown-multi | vitepress | docusaurus | mkdocs
language: zh-CN
annotation_color: "#E5484D"
```

正文每节一行（或一小块）：

```markdown
## 使用 / 管理订单

| 节 | 文件 | 来源功能 | 验证 | 截图计划 | 必备节 | 备注 |
|---|---|---|---|---|---|---|
| 导出订单 | guides/orders/export-orders.md | orders-export | 实采 | 01 列表页导出按钮 box；02 导出对话框 badge 1-3；03 成功提示 box | 前置/步骤/结果/出错 | |
| 批量删除订单 | guides/orders/delete-orders.md | orders-delete | 仅代码 | 无（非测试环境未验证）；确认框文案用引用块 | 前置/步骤/警告/结果/出错 | 待用户提供测试环境 |
```

规则：

- 语言：`_inventory.md` / `_outline.md` / `_editor-notes.md` 是给用户与 agent 看的工作文件，固定中文（与本技能一致）；发布正文与总目录跟随头部 `language`。
- 每一个 `_inventory.md` 的功能 ID 至少出现在一节的"来源功能"里；不写的功能在大纲末尾"本版不含"列出理由。
- "截图计划"写到帧级：序号、时刻、标注类型与目标；没有截图的节写明原因。
- "备注"列留给用户；用户在文件里写的备注阶段 4 必须读。
- 末尾两节：`## 未决问题`（会影响正文的缺失事实）、`## 本版不含`。

## 4. 确认关卡：怎么给用户看

写完 `_outline.md` 后，聊天里只给一段摘要，不贴整个大纲：

```
大纲已写到 docs/manual/_outline.md（status: draft）。
- 4 架书 / 6 组 / 23 节；覆盖功能 21 / 23（2 个列在"本版不含"：原因）
- 验证状态：实采 17、仅代码 4、待确认 2
- 没有截图的节：批量删除订单、重置密码（非测试环境）
- 角色拆分：用户指南 + 管理员指南两组，共用权限矩阵
- 未决问题 3 条（见文件末尾），其中"导出文件保留期"会影响正文
确认后我按大纲开始写；可以直接改文件，或告诉我调整点。
```

然后**结束本轮**。下一轮进入阶段 4 时重新读文件；`status` 仍是 `draft` 且用户没有口头确认，先问一句再继续。用户在问卷里说了不用确认：仍写文件、仍给摘要，但不停。

## 5. 输出格式适配

问卷第 3 题决定。默认 `markdown-multi`。

| 格式 | 目录 | 额外产出 |
|---|---|---|
| `markdown-single` | `docs/USER-MANUAL.md` 一个文件 + `docs/manual/assets/` | 文内目录（锚点链接） |
| `markdown-multi`（默认） | `docs/manual/README.md`（总目录，模板 `manual-toc.md`）+ `get-started/` `guides/<group>/` `reference/` `troubleshooting/` `appendix/` | 每个目录一个 `README.md` 做组索引 |
| `vitepress` | 同上放在 `docs/`；配置写到 `docs/.vitepress/config.ts` 的 `themeConfig.sidebar` | 生成 sidebar 数组片段，不覆盖用户已有 config，给出合并位置 |
| `docusaurus` | `docs/` + `sidebars.js` 的 `manualSidebar` | 每个 md 加 `sidebar_position` frontmatter |
| `mkdocs` | `docs/` + `mkdocs.yml` 的 `nav:` | 生成 `nav:` 片段 |

VitePress sidebar 片段示例（阶段 5 按大纲生成）：

```ts
{ text: '快速开始', items: [
  { text: '关于本手册', link: '/get-started/about' },
  { text: '产品概览', link: '/get-started/overview' },
  { text: '快速开始', link: '/get-started/quick-start' },
]},
{ text: '管理订单', items: [
  { text: '导出订单', link: '/guides/orders/export-orders' },
]},
```

Docusaurus：`sidebars.js` 里新增一个 sidebar（不覆盖用户已有的），每个 md 加 `sidebar_position`：

```js
// sidebars.js
module.exports = {
  manualSidebar: [
    { type: 'category', label: '快速开始', items: ['get-started/about', 'get-started/overview', 'get-started/quick-start'] },
    { type: 'category', label: '管理订单', items: ['guides/orders/export-orders'] },
    { type: 'category', label: '参考', items: ['reference/permissions', 'reference/limits'] },
    { type: 'category', label: '故障排查', items: ['troubleshooting/index', 'troubleshooting/error-messages'] },
  ],
};
```

```markdown
---
sidebar_position: 1
title: 导出订单
---
```

MkDocs：`mkdocs.yml` 的 `nav:`（追加到已有 nav 下，不重排用户已有条目）：

```yaml
nav:
  - 快速开始:
      - 关于本手册: get-started/about.md
      - 产品概览: get-started/overview.md
      - 快速开始: get-started/quick-start.md
  - 管理订单:
      - 导出订单: guides/orders/export-orders.md
  - 参考:
      - 权限说明: reference/permissions.md
      - 限制汇总: reference/limits.md
  - 故障排查:
      - 常见问题排查: troubleshooting/index.md
      - 错误提示对照: troubleshooting/error-messages.md
```

三种片段都按 `_outline.md` 的目录表生成：一级分组 = 表的 `###` 标题，条目 = 每行的"节"与"文件"列。

文件命名：英文小写短横线，动词开头与标题一致（`export-orders.md`）；图片相对路径引用 `../../assets/<feature-id>/...`（多文件）或 `assets/...`（单文件）。

## 6. 交叉链接与术语

- 任务页的"前置条件"链接到权限矩阵 / 设置页；"出现问题时"链接到排障对应症状；概念首次出现链接到术语表。
- 术语全书唯一：`_outline.md` 头部之后可加一张"术语表（草）"——产品名词以 i18n 文案为准，不自创同义词（界面叫"工作区"就不写"空间"）。
- 更新已有手册：先读现有目录与术语，沿用；只改受影响节，保留人工修订的段落；重截受影响的截图并覆盖同名文件；变更写进"版本 / 变更说明"。
