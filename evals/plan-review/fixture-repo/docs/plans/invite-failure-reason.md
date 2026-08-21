# 计划：邀请失败时返回原因

## 背景

前端邀请失败时只显示「邀请失败」，用户不知道是满员还是别的原因。需要让失败原因一路传到前端。

## 现状

- `invite_member` 目前返回 dict。
- `audit.record` 记录每次邀请。
- 前端只有 `InviteDialog` 这一个入口。

## 改动步骤

1. 把 `invite_member` 的返回值从 dict 改成 bool：成功 True，失败 False。这样前端好判断。
2. 给 `audit.record` 增加一个必填参数 `reason`，失败时把原因写进审计日志。
3. `InviteDialog` 在拿到 False 时显示「邀请失败」。

## 验收

能看出失败即可。
