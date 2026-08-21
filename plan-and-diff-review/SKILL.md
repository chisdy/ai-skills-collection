---
name: plan-and-diff-review
description: Reviews only the current plan or diff for missing logic, logic errors, business-layer sync gaps, and scope creep; uses codegraph to map the affected surface, and writes Current-Fix-Required findings back into the active plan/RFC/TODO before further changes. Use only when explicitly requested.
disable-model-invocation: true
metadata:
  version: "1.0.0"
  author: chisdy
---

# Plan And Diff Review

## Goal

Review the current plan or diff without expanding scope. Confirm whether it fully solves the current issue, including required business-layer synchronization. Do not change unrelated code or fix newly discovered problems without explicit user approval.

The name states the two accepted inputs, and they rank in that order. Reviewing a plan before any code exists is the higher-leverage case, since every finding is still free to act on — so a plan with no diff behind it is the primary use of this skill, not a degraded one. Throughout, *fix* refers to whichever of the two is under review: the proposed solution to the current issue, written or not.

These instructions are in English; the deliverable is not. Write the review in 简体中文 following the template at the end, so section headings stay stable and the user can skim for the parts they care about.

## Two modes

This skill is a review, not a rewrite. Keeping the phases separate is what makes the output auditable — a review that quietly turns into a patch leaves the user unable to tell what was found from what was changed.

- **`[模式：评审]`** — the default, and the only mode to enter unprompted. Read code, query codegraph, run read-only verification. The only files to edit are the plan documents in step 6; implementation code stays untouched. Refreshing the codegraph index per step 2 does not count as an edit — it updates a local index, not the repo's source.
- **`[模式：修复]`** — requires the user to approve a specific list of 必须补齐 items. Implement exactly those, then re-verify.

Wanting to fix something mid-review is the signal to finish the review and ask, not to start editing.

## Checklist

1. **Establish the change set from git, then state the issue boundary.** A review built on what the conversation happens to mention will miss whatever was changed silently, so start from the repository's own record:
   - `git status` and `git diff` for uncommitted work; `git diff <base>...HEAD` when the fix spans a branch. Extract the changed files, hunks, and symbol names — step 2 needs that symbol list as its input, and it goes into the 变更集 line of the report so the user can confirm you reviewed the right thing.
   - If there is no diff, the change set is the plan itself. Read the plan document and treat what it says it will touch — files, symbols, entities, endpoints — as the change set, and name those explicitly in 变更集. A plan's real risk is usually what it forgot to list, and you can only spot that once the list is written down.
   - State the issue boundary in one sentence. If the diff appears to solve something other than what the user described, flag the mismatch and ask rather than reviewing against a guessed intent.

2. **Map the affected surface before opening individual files.** This is what separates a real review from re-reading the diff — call sites and sync points are by definition not in the diff.

   **First, get a usable index.** Start with `codegraph_status`. If it fails, resist the urge to read every failure as "no index" — three different causes look alike and need opposite responses, so diagnose first:
   - **Index exists, the server just can't find it.** The error mentions a working-directory or workspace-root problem, and typically says the index is probably fine. Retry the same call with an explicit `projectPath` pointing at the repo root. This recovers a fully working index in one call, so never rebuild for this cause — a full re-index here is pure waste.
   - **Index exists but is stale.** Run `codegraph sync`, which processes only changes since the last index. It is cheap, adds no new side effects, and matters especially here: the files lagging behind the index are usually the exact ones under review.
   - **Never initialized** (no `.codegraph/` directory). Stop and ask the user before building anything. A full index is a write into their repo that can run for many minutes and leave a directory of hundreds of megabytes to over a gigabyte, and `codegraph init` does not reliably add it to `.gitignore`. Give them what they need to decide — the repo's file count (`git ls-files | wc -l`) as a scale signal, the command `codegraph init --index`, and a reminder to gitignore `.codegraph/`. Wait for the answer. If they decline, fall back to Grep + Read and say so in 已核对范围 so the weaker coverage is visible in the report.

   **Then map the surface.**
   - `codegraph_context` on each changed symbol (definition + callers + callees in one call). Add `codegraph_callers` when a signature, return shape, or side effect changed; `codegraph_impact` for renames, enum or schema changes; `codegraph_explore` to survey several related symbols at once. The codegraph server's own instructions cover tool selection in more detail — follow them rather than re-deriving.
   - Reviewing a plan instead of a diff → run the same mapping against the symbols the plan says it will touch. This is the highest-leverage use of the index: a call site found now costs nothing to account for, whereas the same one found after implementation means rework.
   - How far to walk: one layer of callers and callees is the floor for every change. Go deeper only where a contract moved — signature, return shape, enum, schema, API payload — since that is where breakage actually hides, and it keeps the review from expanding into a whole-repo audit.

   The surface includes:
   - frontend component, hook, store, API client, route, or UI state
   - backend API, schema, service, repository, model, migration, task, notification, or permission logic
   - tests, docs, or config only when required by this fix

3. **Check for missing or incorrect logic:** happy path, edge cases, empty/error states, permissions, retries/idempotency, concurrency, data consistency, and API contract mismatches. Every claim needs a concrete observation behind it — a file read, a codegraph result, a grep hit, or a verification run. "Probably handled" inferred from naming or memory is how reviews pass broken code.

4. **Check business synchronization:** credits, org membership, notifications, audit logs, usage records, task status, cache invalidation, and matching client/server/service/repository changes. Use `codegraph_callers` / `codegraph_impact` on the changed entity (model field, enum, API shape) to find every downstream site that must move with it.

5. **Classify and rank every finding.**
   - **Current Fix Required** — needed to make this issue correct. Tag each one so the user knows where to start: `阻塞` (the fix is wrong, or breaks callers without it), `重要` (correct but incomplete — an edge case, error state, or sync point is unhandled), `次要` (belongs in this fix, low risk if deferred). Order 必须补齐 by severity.
   - **Out Of Scope** — adjacent or newly discovered problem; report only and wait for approval.

6. **Sync Current Fix Required findings back into the active plan.** Findings that live only in chat get lost the moment the conversation moves on, which defeats the review.
   - If a plan, proposal, TODO, or RFC exists for this fix, edit it in place so every **Current Fix Required** finding becomes a concrete step before any further implementation.
   - Preserve the plan's existing structure, ordering, and language; insert new items at the correct stage (analysis / change / verification) so the plan stays the single source of truth.
   - Mark each inserted item so it traces back to this review (e.g. a short tag like `补充于评审`).
   - **Out Of Scope** findings stay out of the plan — keep them in 暂不处理 until the user approves.
   - If no written plan exists, propose creating or updating one before continuing.

7. **Verify with the narrowest check that produces evidence.** Read-only checks belong in 评审模式 too — they are what turn assertions into evidence.

   Code already written:
   - type-check / lint on touched files (always)
   - the most relevant single test file, not the full suite
   - DB changes → migration dry-run or schema diff
   - API contract changes → the affected endpoint's contract or integration test
   - frontend → component test, plus a manual browser check only if interaction logic moved

   Plan not yet implemented — nothing can be type-checked, so verify the plan's premises instead, which is where plans actually fail:
   - Read and confirm that every symbol, field, table, endpoint, or config key the plan assumes already exists really does. A plan resting on a misremembered schema collapses at its first step.
   - Confirm the plan's assumed starting state matches reality: current behaviour, existing data shape, migrations already applied.
   - For each proposed step, state what check would later prove it correct. A step nobody can verify is either underspecified or untestable, and both belong in 必须补齐.

   Either way: if the project supplies domain conventions (a tech-stack or coding-standards skill or rule), consult it for business-sync specifics — DB constraints, container exec, test locations, naming — instead of assuming defaults.

8. **Report using the template below, then stop.** A failing check is a finding, not a detour: record it under 必须补齐 with the actual error output as evidence and let severity reflect it. 评审模式 ends here.

9. **`[模式：修复]` only, after approval:** restate the approved 必须补齐 list, implement exactly those items, re-run the step 7 verification, and report any remaining risk. Anything not on the approved list stays in 暂不处理.

## Anti-patterns (red flags)

| Thought | Reality |
|---|---|
| "顺手把这个也修了" / "和当前 fix 无关，但写都写了" | Scope creep either way. Goes to 暂不处理, never into the fix or the plan. |
| "对话里说改了哪些文件，照着看就行" | Only `git diff` is the fact. Silent changes are exactly what a review exists to catch. |
| "看名字应该处理了 error case" | Not evidence. Read the code or run the test. |
| "只看 diff 就够了" | The diff cannot show call sites. At minimum walk one layer of callers/callees. |
| "测试应该会覆盖" | Open the test file and verify. |
| "type-check 挂了，我先修一下" | That is 修复模式 without approval. Record the error as a finding and ask. |
| "计划写错了，我顺手改对" | If diff and plan conflict, flag the conflict and let the user decide which is truth. Do not silently rewrite the plan to match the code. |
| "codegraph 慢，先跳过" | Querying is sub-millisecond — the index already did the work, and skipping it is the single biggest cause of missed sync points. Building an index from scratch is the expensive part, and that is a separate decision belonging to the user (step 2). |
| "status 报错了，那就是没索引，我先 index 一下" | Most `status` failures are a workspace-root detection problem on an index that is perfectly fine. Retry with `projectPath` first; a needless full re-index can burn many minutes. |

## Plan source priority

When deciding which plan to write findings back into:

1. A plan file the user explicitly pointed at this turn.
2. A new or modified plan / RFC document on the current branch. Find where this repo actually keeps them — check `git diff --name-only` against the repo's own convention (`docs/**/plans/**`, `rfcs/`, `.plans/`, or whatever exists) rather than assuming a fixed path.
3. The active TodoList in this session.
4. No plan exists → propose creating one before continuing; do not let findings live only in chat.

## Output format

```markdown
[模式：评审]
结论：[可以合并 / 需补齐 N 项（含 M 项阻塞） / 需返工]
当前问题边界：[one sentence]
变更集：[N 个文件，关键符号 a / b / c]（来源：git diff）

已核对范围：
- [file or symbol] : [codegraph_context / codegraph_callers / Read / Grep / 运行测试]
- [...] : [...]
（相邻但未覆盖的面也要诚实列出，写"未核对"）

必须补齐：（按严重度排序）
- [阻塞] [finding tied to current fix] — 证据：[file:line 或 codegraph 结果摘要]
- [重要] [finding] — 证据：[...]

逻辑风险：
- [risk tied to current fix]

业务同步：
- [client/server/service/repository/test/doc sync required]

暂不处理：
- [new or unrelated issue, pending user confirmation]

已执行验证：
- [command 或前提核对动作] → [结果]

计划已更新：
- [plan file path] → [新增/修改的步骤摘要]（若无计划文件则写明"无现有计划，建议先建立"）

下一步：
- [focused action or confirmation request]
```

If nothing is wrong, write `结论：可以合并` and drop the 必须补齐 / 暂不处理 / 计划已更新 sections — but keep 已核对范围 and 已执行验证. "No issues" without evidence is rubber-stamping, not review.
