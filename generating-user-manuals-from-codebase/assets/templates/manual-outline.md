---
status: draft
confirmed_at:
source_inventory: docs/manual/_inventory.md
product_version:
output_format: markdown-multi
language: zh-CN
annotation_color: "#E5484D"
viewport: 1280x800
---

# 手册大纲（工作文件，不发布）

确认方式：在聊天里说"确认"或提修改；或直接改本文件并把头部 `status` 改成 `confirmed`。"备注"列留给你写，阶段 4 会读。

## 读者与角色

- 读者：`<最终用户 / 管理员>`
- 角色：`<角色列表>`；拆分决定：`<共用 + 权限矩阵 / 分组>`

## 目录

### 定向 Get Started

| 节 | 文件 | 来源功能 | 验证 | 截图计划 | 必备节 | 备注 |
|---|---|---|---|---|---|---|
| 关于本手册 | get-started/about.md | — | — | 无 | 版本 / 读者 / 不覆盖 / 约定 | |
| 产品概览 | get-started/overview.md | `<全局>` | | 01 主界面 badge 1–4 区域 | 一句话 / 区域图 / 状态模式 | |
| 快速开始 | get-started/quick-start.md | `<核心流程功能 ID>` | | 01 入口 box；02 关键表单 badge；03 成功态 box | 前置 / 首次配置 / 核心流程 / 成功信号 / 下一步 | |
| 核心概念 | get-started/concepts.md | | | 无 | 每条 1–3 句 | |

### 使用 Guides / `<分组名>`

| 节 | 文件 | 来源功能 | 验证 | 截图计划 | 必备节 | 备注 |
|---|---|---|---|---|---|---|
| `<动词开头标题>` | guides/`<group>`/`<slug>`.md | `<ID>` | 实采 / 仅代码 | 01 …；02 …；03 … | 前置 / 步骤 / 结果 / 出错 | |

### 使用 Guides / 管理员

| 节 | 文件 | 来源功能 | 验证 | 截图计划 | 必备节 | 备注 |
|---|---|---|---|---|---|---|

### 理解 Reference

| 节 | 文件 | 来源功能 | 验证 | 截图计划 | 必备节 | 备注 |
|---|---|---|---|---|---|---|
| 权限矩阵 | reference/permissions.md | `<全部有角色差异的 ID>` | | 无 | 功能 × 角色 / 被拦时看到 | |
| 限制汇总 | reference/limits.md | | | 无 | 每条注明位置 | |
| 状态说明 | reference/statuses.md | | | 可选：状态标签样例 box | 状态 / 显示 / 含义 / 进出 | |
| 设置项参考 | reference/settings.md | | | 无 | 项 / 作用 / 取值 / 默认 / 范围 / 谁能改 | |

### 恢复 Troubleshooting

| 节 | 文件 | 来源功能 | 验证 | 截图计划 | 必备节 | 备注 |
|---|---|---|---|---|---|---|
| 常见问题排查 | troubleshooting/README.md | | | 无 | 症状 → 原因 → 恢复 → 联系谁 | |
| 错误提示对照 | troubleshooting/error-messages.md | | | 无 | 原文 / 条件 / 可做 | |
| FAQ | troubleshooting/faq.md | | | 无 | 只放已验证 | |

### 附录

| 节 | 文件 | 备注 |
|---|---|---|
| 术语表 | appendix/glossary.md | |
| 变更说明 | appendix/changelog.md | 更新已有手册时 |

## 覆盖检查

- 清单功能总数：`<M>`；已映射到某节：`<N>`
- 验证状态：实采 `<a>` / 仅代码 `<b>` / 待确认 `<c>`
- 没有截图的节与原因：

## 本版不含

| 功能 ID | 原因 |
|---|---|

## 未决问题（会影响正文）

| # | 问题 | 影响哪节 | 现在打算怎么写 |
|---|---|---|---|
