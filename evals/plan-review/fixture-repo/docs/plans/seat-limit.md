# 计划：组织席位上限

## 背景

免费版组织可以无限邀请成员，导致计费侧对不上。需要给组织加席位上限，超出上限时拒绝邀请。

## 现状

- `Organization` 模型已经有 `seat_limit` 字段，默认值 5，所以不需要新加列。
- `app/services/invitations.py` 的 `invite_member` 当前返回 bool，成功 True 失败 False。
- `invite_member` 的唯一调用方是 `app/api/invitations.py` 的 `create_invitation_endpoint`。

## 改动步骤

1. 在 `invite_member` 开头调用 `membership_repo.count_active_members(org_id)`，与 `org.seat_limit` 比较，超出则返回 False。
2. `create_invitation_endpoint` 在拿到 False 时返回 409。
3. 更新相关的前端逻辑。

## 验收

功能能跑通即可。
