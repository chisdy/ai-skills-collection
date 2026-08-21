# 计划：组织成员列表接口

## 背景

前端 `web/src/api/invitations.ts` 里已经有 `listMembers(orgId)`，但后端没有对应端点，页面上成员列表现在是空的。补齐这个只读接口。

## 现状

- `app/repositories/membership.py` 有 `count_active_members(org_id)`，但没有列表查询函数。
- `app/api/invitations.py` 里已有 `create_invitation_endpoint` / `revoke_invitation_endpoint` 两个端点，新端点按同样的函数签名风格写。
- `web/src/api/invitations.ts` 的 `listMembers` 已经在请求 `GET /api/orgs/{orgId}/members`，路径以它为准。
- 只读接口，不涉及 `billing.sync_seat_usage`、审计日志或通知。

## 改动步骤

1. `app/repositories/membership.py` 新增 `list_active_members(org_id) -> list[Membership]`，按 `joined_at` 升序返回 `status == "active"` 的记录。
   - 验收：新增单测覆盖「有活跃成员」「全部非活跃返回空列表」「按 joined_at 排序」三种情况。
2. `app/api/invitations.py` 新增 `list_members_endpoint(org_id, current_user_id)`，返回 `(list[dict], 200)`，字段为 `user_id / role / joined_at`。
   - 验收：单测断言非本组织成员访问时返回 403，正常访问返回 200 且字段齐全。
3. 前端 `InviteDialog` 所在页面渲染列表。
   - 验收：组件测试断言接口返回两条记录时渲染出两行，返回空数组时渲染空态文案。

第 1、2 步可以独立上线（前端在没有数据时已有空态），第 3 步单独发布。

## 回滚

新增端点与新增函数，无数据写入，直接回滚代码即可。
