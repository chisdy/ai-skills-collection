# 功能清单（工作文件，不发布）

- 项目：`lumen-assets-demo`　技术栈：静态 HTML + 原生 JS（hash 路由）　产品版本 / commit：`0.3.0`
- 生成日期：`2026-09-16`　最后验证：`2026-09-16`

## 功能

| ID | 功能（用户视角） | 入口（菜单 / 路径文字） | 角色 | 状态 | 限制 | 出错提示 | 证据 | 验证 | 手册节 |
|---|---|---|---|---|---|---|---|---|---|
| `dashboard-view` | 查看概览（素材总数、处理中数量） | 菜单「概览」 | 全部 | — | — | — | src/router.js:3; src/views.js:10-22; src/i18n/zh-CN.json nav.dashboard | 实采 snapshot@2026-09-16 | 产品概览 |
| `assets-view` | 查看素材列表与状态 | 菜单「素材」 | 全部 | 上传中 / 处理中 / 已就绪 / 处理失败 | — | 空状态「还没有素材，点击右上角「导入文件」开始。」 | src/router.js:4; src/views.js:24-60; src/status.js | 实采 snapshot@2026-09-16 | 查看素材状态 |
| `assets-import` | 导入素材文件 | 「素材」页右上角「导入文件」；概览页「去导入素材」 | editor、admin | 导入后为「处理中」 | CSV / XLSX；≤ 5 MB；名称必填、≤ 60 字 | E1001 / E1002 / E1003 | src/components/UploadAssetDialog.js; src/validation.js:1-8; src/permissions.js:5-6 | 实采 snapshot@2026-09-16 | 导入素材 |
| `assets-delete` | 删除素材 | 「素材」列表每行「删除」 | admin | — | — | 确认框「删除后无法恢复，引用该素材的页面会显示为空。确定删除「{name}」吗？」 | src/views.js:33-36,63-77; src/components/ConfirmDialog.js; src/i18n/zh-CN.json assets.deleteConfirm | 实采 snapshot@2026-09-16（截确认框后取消） | 删除素材 |
| `members-view` | 查看成员列表 | 菜单「成员」（无权限时菜单隐藏） | admin | — | — | 「你没有权限查看成员列表，请联系管理员。」 | src/router.js:5; src/views.js:90-104 | 实采 snapshot@2026-09-16 | 管理成员 |
| `members-invite` | 邀请成员 | 「成员」页「邀请成员」 | admin | — | — | — | src/views.js:97（按钮 disabled，演示环境不可用） | 待确认 | 本版不含 |
| `settings-notify` | 开关「素材处理完成时通知我」 | 菜单「设置」 | 全部 | — | — | 「设置已保存」 | src/views.js:108-127 | 实采 snapshot@2026-09-16 | 修改通知设置 |

## 角色与权限（草表）

| 功能 ID | viewer | editor | admin | 被拦时看到 | 证据 |
|---|---|---|---|---|---|
| assets-import | 不可 | 可 | 可 | 「导入文件」按钮不显示 | src/permissions.js; src/views.js:29 |
| assets-delete | 不可 | 不可 | 可 | 「删除」按钮不显示 | src/permissions.js; src/views.js:33 |
| members-view | 不可 | 不可 | 可 | 菜单「成员」隐藏；直接访问显示「你没有权限查看成员列表，请联系管理员。」 | src/router.js:5,22-24; src/views.js:91 |

## 状态

| 功能 / 实体 | 状态值 | 界面显示 | 含义 | 从哪来 → 到哪去 | 证据 |
|---|---|---|---|---|---|
| 素材 | uploading | 上传中 | 文件正在上传 | → 处理中 | src/status.js |
| 素材 | processing | 处理中 | 系统正在处理文件 | → 已就绪 / 处理失败 | src/status.js |
| 素材 | ready | 已就绪 | 可被引用 | 终态 | src/status.js |
| 素材 | failed | 处理失败 | 需重新导入 | → 上传中（重新导入） | src/status.js |

## 限制

| 位置 | 限制 | 值 | 前端 / 后端 | 证据 |
|---|---|---|---|---|
| 导入文件 | 文件类型 | .csv, .xlsx | 前端 | src/validation.js:3; 界面提示 assets.fileHint |
| 导入文件 | 文件大小 | 5 MB | 前端 | src/validation.js:4 |
| 素材名称 | 长度 | ≤ 60 | 前端 maxlength | src/validation.js:5 |
| 导入文件 | 行数 | 500 行（界面无提示） | 仅代码 | src/validation.js:7-8 |

## 错误提示

| 界面原文 | 出现条件 | 用户可做 | 证据 |
|---|---|---|---|
| 文件类型不支持，请上传 CSV 或 XLSX | 选了其他类型 | 换文件 | errors.E1001 |
| 文件超过 5 MB | 超大 | 拆分或压缩后重试 | errors.E1002 |
| 素材名称不能为空 | 名称留空 | 填写名称 | errors.E1003 |
| 处理失败，请重新导入 | 处理阶段失败（含行数超 500） | 重新导入 | errors.E2001; validation.js maxRows |
| 你没有权限执行此操作 | 无权限触发导入 | 联系管理员 | errors.E3001 |

## 未见 / 待确认

| 想知道 | 找过哪里 | 为什么重要 |
|---|---|---|
| 处理需要多久 | status.js、views.js 无定时 / 队列配置 | 用户会问"处理中要等多久" |
| 500 行限制是否会提前告知用户 | 界面无任何提示 | 写进正文会误导为可预知规则；应进编辑备注 |
| 邀请成员流程 | 按钮 disabled，无表单代码 | 本版不写 |
