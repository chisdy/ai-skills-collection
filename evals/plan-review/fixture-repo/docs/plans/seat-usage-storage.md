# 计划：席位用量落库

## 背景

`app/services/billing.py` 目前把席位用量存在进程内的 `_SEAT_USAGE` 字典里，重启即丢失，多实例之间也不一致。要迁到新表 `seat_usage_snapshots`。

## 现状

- `billing.sync_seat_usage(org_id)` 在成员数变化后被调用，写入 `_SEAT_USAGE`。
- `billing.current_seat_usage(org_id)` 从 `_SEAT_USAGE` 读取。
- 读取方在计费结算和前端组织设置页。

## 改动步骤

1. 把 `current_seat_usage` 改为从 `seat_usage_snapshots` 表读取。
2. 新建 `seat_usage_snapshots` 表，并从现有组织成员数回填一份历史数据。
3. 让 `sync_seat_usage` 同时写内存和新表（双写），观察一段时间。
4. 前端组织设置页接入新的用量接口。
5. 后端上线新的用量接口。
6. 确认无误后删除 `_SEAT_USAGE` 相关代码。

## 验收

上线后看下数据对不对。
