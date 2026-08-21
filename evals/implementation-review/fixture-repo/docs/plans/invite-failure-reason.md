# 计划：重复邀请返回失败原因

## 背景

同一邮箱可以被反复邀请出多条 pending 记录，前端失败时也只显示「邀请失败」。需要拦住重复邀请，并把原因传到前端。

## 现状

- `invite_member` 返回 dict，调用方依赖其中的 `invitation_id` 字段（`app/api/invitations.py` 与 `app/tasks/bulk_invite.py` 两处）。
- `InviteDialog` 只在 `status !== "pending"` 时显示固定文案「邀请失败」。

## 改动步骤

1. `app/repositories/membership.py` 新增 `has_pending_invitation(org_id, email) -> bool`。
   - 验收：单测覆盖「有 pending」「无 pending」两种情况。
2. `invite_member` 开头检查，命中则不创建邀请、不发通知，返回 `{"status": "failed", "reason": "duplicate_invitation"}`（保持 dict 契约，不改成 bool）。
   - 验收：单测断言重复邀请返回 failed 且不产生新 invitation。
3. `app/tasks/bulk_invite.py` 对 `status != "pending"` 的行跳过并继续，不再无条件取 `invitation_id`。
   - 验收：单测断言 CSV 中含重复邮箱时不抛异常、返回已创建的 id 列表。
4. `create_invitation_endpoint` 对 `status == "failed"` 返回 409。
   - 验收：接口测试断言 409。
5. `web/src/api/invitations.ts` 的 `InvitationResult` 加可选 `reason`；`InviteDialog` 把 `duplicate_invitation` 映射为「该邮箱已有待接受的邀请」。
   - 验收：组件测试覆盖重复邀请提示文案。

## 回滚

纯新增逻辑，回滚代码即可。
