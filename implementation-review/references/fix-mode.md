# 修复模式与提前授权（fix mode and pre-authorization）

Read this file in either situation, and always **before** editing any repo file:

- the user's review request already grants fix approval upfront ("评审完发现明确的问题直接修") — read at the start, because pre-authorization changes what the review turn itself does;
- the user approves fixes after reading the report — read before entering `[模式：修复]`.

## Pre-authorization (提前授权)

The user may grant fix approval upfront, in the same message that requests the review. This moves the approval earlier; it does not weaken the discipline:

- The complete review report still comes first. Findings must be on record before any edit, or the user can no longer tell what was found from what was changed.
- It covers only 必须补齐 items that are **明确** — and 明确 is about the *source of the spec*, not the reviewer's confidence in the fix. A finding is 明确 when the correct behavior was already written down by the user:
  - a plan step marked **未实现** → implement it as the plan describes;
  - a plan step marked **偏离** → restore the code to what the plan says — *unless* the review found evidence that the plan as written is wrong or infeasible, in which case the item is really a plan question and waits for the user's ruling;
  - a requirement the user **stated directly** (in this conversation, or in the request that produced the change).
- Everything the review discovered on its own — a security hole, an off-diff caller the plan never mentioned, a quality or structure problem — is **not** 明确, however obvious the fix looks. Its spec exists only in the reviewer's head; writing it into code without a nod is the reviewer deciding requirements. These stay in the report and wait.
- It **never** covers the plan document. 计划更新建议 always waits for the user's explicit 同步计划 choice — pre-authorized or not.
- It never covers 暂不处理 items. "顺手修掉别的问题" stays scope creep even when pre-authorized fixing is on.

**Execution under pre-authorization:** produce the same complete report first, then immediately fix the 明确 items, re-run the checklist step 10 verification on them, and report which items were fixed and which still wait for a decision. In the report, tag fixed items `[已修·提前授权]` so the boundary of what was touched stays visible. Any plan document remains untouched either way; the closing question narrows to the reviewer-discovered items (plus, under 计划基准, whether to 同步计划).

## `[模式：修复]` execution, after the user chooses

- Restate the approved 必须补齐 list (plus any 改进建议 the user explicitly adopted). When the user replied with report numbers ("修复 3.1、3.3"), expand each number back into the finding it names — resolved against *this* report's numbering — one line each, so both sides see the same list before any edit and a mis-typed number cannot silently authorize the wrong fix.
- Under 计划基准, resolve the plan-document choice first per `plan-baseline.md` (A / B / C); with no plan document, there is nothing to sync and the approval is simply which items to fix.
- Implement exactly the approved items (none, for 仅更新计划), re-run the checklist step 10 verification, and report any remaining risk. Anything not on the approved list stays in 暂不处理.
- A formatting item the user approved is the one place a formatter's writing mode (`ruff format`, `prettier --write`, `gofmt -w`, `cargo fmt`) is allowed — scoped to the files in the change set, using the project's own configuration, never a loaded skill's defaults. Formatting files outside the change set is scope creep even here.

## Anti-patterns

| Thought | Reality |
|---|---|
| "用户授权了直接修，那计划也顺手同步掉" | Pre-authorization covers unambiguous code fixes only. The plan document always waits for an explicit 同步计划 choice. |
| "这个问题很明确，不用等批准了" | Without pre-authorization in the user's own message, every fix waits — 明确 controls what a granted authorization covers, it does not replace the authorization. |
| "这个 bug 修法只有一种，够明确了吧" | 明确 looks at where the spec comes from (a plan step, the user's words), not at how obvious the fix is. A reviewer-discovered finding waits, however single-solution it looks. |
