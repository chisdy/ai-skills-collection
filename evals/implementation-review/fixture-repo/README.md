# seatly（评估用示例仓库）

一个精简的组织 / 成员 / 邀请后端，外加一点前端，用于 skill 评估。

- `app/models/` — 数据模型（`organizations` 的列见 `migrations/0003_add_org_plan_tier.py` 顶部注释）
- `app/services/` — 业务逻辑，成员数变化后需要调用 `billing.sync_seat_usage`
- `app/repositories/` — 数据访问
- `app/api/` — HTTP 端点
- `app/tasks/` — 后台任务
- `web/src/` — 前端
- `docs/plans/` — 计划文档
