# 计划：组织席位上限

## 背景

免费版组织可以无限邀请成员，导致计费侧对不上。需要给组织加席位上限，超出上限时拒绝邀请。

## 现状

- `Organization` 模型已有 `max_members` 字段，默认值 5，不需要新加列。
- `app/services/invitations.py` 的 `invite_member` 返回 dict，调用方依赖其中的 `invitation_id` 字段。
- `invite_member` 的调用方是 `app/api/invitations.py` 的 `create_invitation_endpoint`。

## 改动步骤

1. 新增 `app/repositories/organizations.py`，提供 `get_organization(org_id) -> Organization`。
   - 验收：单测断言能取到组织且 `max_members` 有默认值。
2. `invite_member` 开头校验：`count_active_members(org_id) + count_pending_invitations(org_id) >= org.max_members` 时，不创建邀请、不发通知，返回 `{"status": "rejected", "reason": "seat_limit_reached"}`（保持 dict 契约）。pending 邀请必须计入，否则可以用未接受的邀请无限绕过上限。
   - 验收：单测覆盖「活跃满员拒绝」「活跃 + pending 满员拒绝」「未满可邀请」三种情况。
3. `create_invitation_endpoint` 对 `status == "rejected"` 返回 409。
   - 验收：接口测试断言 409 与响应体里的 reason。
4. `InviteDialog` 收到 rejected 时提示「席位已满，请升级套餐或移除成员」。
   - 验收：组件测试覆盖满员提示。
5. `tests/test_invitations.py` 新增上述用例。

## 回滚

纯新增校验逻辑，回滚代码即可。
