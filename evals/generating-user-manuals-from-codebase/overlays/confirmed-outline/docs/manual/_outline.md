---
status: confirmed
confirmed_at: 2026-09-16
source_inventory: docs/manual/_inventory.md
product_version: 0.3.0
output_format: markdown-multi
language: zh-CN
annotation_color: "#E5484D"
viewport: 1280x800
---

# 手册大纲（工作文件，不发布）

## 读者与角色

- 读者：最终用户（viewer / editor）与管理员（admin）
- 角色：viewer、editor、admin；拆分决定：共用任务页 + 权限矩阵；管理成员单独放「管理员」组

## 目录

### 定向 Get Started

| 节 | 文件 | 来源功能 | 验证 | 截图计划 | 必备节 | 备注 |
|---|---|---|---|---|---|---|
| 关于本手册 | get-started/about.md | — | — | 无 | 版本 / 读者 / 不覆盖 / 约定 | |
| 产品概览 | get-started/overview.md | dashboard-view | 实采 | 01 概览页 badge 1 顶栏角色、2 左侧菜单、3 内容区 | 一句话 / 区域图 / 状态模式 | |
| 快速开始：导入第一个素材 | get-started/quick-start.md | assets-import, assets-view | 实采 | 01 素材页「导入文件」box；02 导入对话框 badge 1 选择文件、2 素材名称、3 开始导入；03 列表新行「处理中」box | 前置 / 核心流程 / 成功信号 / 下一步 | 以 editor 角色截 |

### 使用 Guides / 管理素材

| 节 | 文件 | 来源功能 | 验证 | 截图计划 | 必备节 | 备注 |
|---|---|---|---|---|---|---|
| 导入素材 | guides/assets/import-assets.md | assets-import | 实采 | 复用快速开始 01–02；03 校验错误 toast box（留空名称触发 E1003） | 前置 / 步骤 / 结果 / 出错 | |
| 查看素材状态 | guides/assets/view-asset-status.md | assets-view | 实采 | 01 列表状态列 box | 前置 / 步骤 / 结果 | 链接到状态说明 |
| 删除素材 | guides/assets/delete-assets.md | assets-delete | 实采 | 01 行内「删除」box；02 确认框 box（红色确认按钮） | 前置 / 步骤 / 警告 / 结果 / 出错 | 警告紧贴「确认删除」步骤 |

### 使用 Guides / 管理员

| 节 | 文件 | 来源功能 | 验证 | 截图计划 | 必备节 | 备注 |
|---|---|---|---|---|---|---|
| 管理成员 | guides/admin/manage-members.md | members-view | 实采 | 01 成员列表 box，邮箱列 mask | 前置 / 步骤 / 结果 | 邀请成员按钮禁用，不写 |

### 使用 Guides / 设置

| 节 | 文件 | 来源功能 | 验证 | 截图计划 | 必备节 | 备注 |
|---|---|---|---|---|---|---|
| 修改通知设置 | guides/settings/notification-settings.md | settings-notify | 实采 | 无 | 前置 / 步骤 / 结果 | |

### 理解 Reference

| 节 | 文件 | 来源功能 | 验证 | 截图计划 | 必备节 | 备注 |
|---|---|---|---|---|---|---|
| 权限说明 | reference/permissions.md | assets-import, assets-delete, members-view | 实采 | 无 | 功能 × 角色 / 被拦时看到 | |
| 限制汇总 | reference/limits.md | assets-import | 实采 + 仅代码 | 无 | 每条注明位置 | 500 行限制只进编辑备注 |
| 状态说明 | reference/statuses.md | assets-view | 实采 | 无 | 状态 / 显示 / 含义 / 进出 | |

### 恢复 Troubleshooting

| 节 | 文件 | 来源功能 | 验证 | 截图计划 | 必备节 | 备注 |
|---|---|---|---|---|---|---|
| 常见问题排查 | troubleshooting/README.md | 全部 | 实采 | 无 | 症状 → 原因 → 恢复 | 含「看不到导入按钮」「一直处理中」「处理失败」 |
| 错误提示对照 | troubleshooting/error-messages.md | assets-import | 实采 | 无 | 原文 / 条件 / 可做 | |

### 附录

| 节 | 文件 | 备注 |
|---|---|---|
| 术语表 | appendix/glossary.md | 素材、已就绪、处理中 |

## 覆盖检查

- 清单功能总数：7；已映射到某节：6
- 验证状态：实采 6 / 仅代码 0 / 待确认 1
- 没有截图的节与原因：修改通知设置（纯表单，文字可说清）；参考与排障节不配图

## 本版不含

| 功能 ID | 原因 |
|---|---|
| members-invite | 按钮在演示环境禁用，无表单实现，无法验证 |

## 未决问题（会影响正文）

| # | 问题 | 影响哪节 | 现在打算怎么写 |
|---|---|---|---|
| 1 | 处理需要多久 | 快速开始、排障 | 不写时长；排障里写"若长时间处于处理中，请重新导入或联系管理员"需验证——暂只写重新导入 |
| 2 | 500 行限制界面无提示 | 限制汇总、排障 | 正文不写；编辑备注提请产品确认是否要在界面提示 |
