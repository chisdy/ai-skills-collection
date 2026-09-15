# 会话变更集（session edit record as change-set source）

Read this file when git cannot produce a usable diff and the change set must be reconstructed from the current session's edit record（来源：会话编辑记录）. This is a fallback, never a substitute: when git can produce a diff, only `git diff` is the fact.

## Before committing to the fallback

Check whether the session's own commits identify a diff base: `git log` around the session's timeframe usually does, and `git diff <first-session-commit>^...HEAD` then restores the primary source. Only proceed here when that fails too. Do not fall back merely because running git feels like a detour.

## Reconstructing the change set

- Reconstruct from what this session actually did: every file edited by a tool call in this conversation (including edits summarized in attached history), plus the symbols touched.
- Read the current state of each edited file around every edited region — the record says *where* the session wrote, not what the code now says.
- Throughout the checklist, "diff hunk" reads as "edited region": conformance audits edited regions against the baseline, and regions the baseline does not account for are still 计划外/需求外改动.

## Declaring the limits

This source carries two limits; state both explicitly in the 变更集 line and 已核对范围:

1. It cannot prove nothing *else* changed — no repository-wide record exists.
2. There is no before-image — the old contract that off-diff callers may still assume must be recovered from callers, tests, and the plan (checklist step 4) instead of read off a diff.

Report header form:

```
变更集：[N 个文件，关键符号 a / b / c]（来源：会话编辑记录；无 before 快照，无法排除会话外改动）
```

## Anti-patterns

| Thought | Reality |
|---|---|
| "会话记录里就这几个文件，别的肯定没动" | The fallback source cannot prove that. Say so in 变更集 and 已核对范围 instead of asserting completeness the evidence does not support. |
