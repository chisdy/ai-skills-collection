---
name: plan-review
description: Reviews one not-yet-implemented plan, proposal, RFC, or TODO before any code is written. Verifies the plan's premises against the real codebase, maps the affected surface with codegraph, walks the current problem chain to the end so no sibling entry point or sync site is missed, and on stable codebases keeps the change silent toward unrelated business logic. Audits step ordering, staged delivery, per-step acceptance criteria, and approach selection, then writes must-fix findings back into the plan document. Use only when explicitly requested.
disable-model-invocation: true
metadata:
  version: "1.0.0"
  author: chisdy
---

# Plan Review

## Goal

Review one plan before any of it is built, and answer three questions with evidence:

1. If this plan is executed exactly as written, is the current problem actually solved — including every site on this problem's chain, and the business-layer synchronization it implies?
2. Can someone execute it as written without getting stuck, guessing, or breaking production halfway through?
3. On a codebase that already has related, working business: will this add or fix leave other business logic and workflows undisturbed?

Reviewing before implementation is the highest-leverage moment there is: every finding here costs nothing to act on, while the same finding after the code is written means rework. That is the whole reason this skill exists as its own thing.

The expensive error in a plan is rarely a wrong line — it is a missing one. Wrong lines get caught by the type checker on day one; missing ones surface mid-implementation, when the cost of adding them has already multiplied. So weight the review toward what the plan does not say.

This skill never edits implementation code. The only repo file it writes is the plan document itself (step 7). That constraint is not a limitation to work around — it is what keeps the review auditable, since the user can always tell what was found apart from what was changed. If implementing something feels urgent mid-review, that is the signal to finish the review and ask. Refreshing the codegraph index (`codegraph sync`, or an init the user approved) does not count as an edit — it writes a local index, not the repo's source.

These instructions are in English; the deliverable is not. Write the review in 简体中文 following the template at the end, so section headings stay stable and the user can skim for the parts they care about.

## Checklist

### 1. Get the plan onto paper, then state the boundary

- **A plan document exists** → read it in full. Also check `git status`: if uncommitted work already touches what the plan assumes is untouched, the plan's starting state is already false, and that is a finding.
- **The plan only exists in the conversation** → write it down first, then review it. This is not bureaucracy. A plan's real risk is what it forgot to list, and you cannot see an omission in something that was never enumerated; on top of that, findings with nowhere to live get lost the moment the conversation moves on. Keep the draft short — problem, steps, affected surface — put it where this repo already keeps such documents (see *Locating the plan*), and tell the user the path. Ask where it should go only if the repo has no visible convention.
- **State the issue boundary in one sentence.** If the plan solves something other than what the user described, flag the mismatch and ask instead of reviewing against a guessed intent.
- **Write down the change set**: every file, symbol, entity, endpoint, table, and config key the plan claims it will touch. This list feeds later steps and goes into the report so the user can confirm you reviewed the right thing. Listing it explicitly is also the cheapest way to notice what is missing from it.
- **Name the project context in one line**: 新项目 (little or no related business already running) or 已有稳定代码 (the common case — related models, endpoints, tasks, and UI already exist). Isolation in step 4 only has teeth in the second case; skip it there with an explicit "新项目，无既有业务面需隔离" rather than silently dropping it.

### 2. Verify the plan's premises against the actual codebase

This is the move that a diff review cannot make, and the one that catches the most catastrophic class of plan failure: a plan resting on a misremembered schema collapses at its first step, and no amount of reasoning about the plan's logic will reveal that.

For each thing the plan assumes already exists — a symbol, field, table, endpoint, config key, migration, permission — read it and confirm it exists *and has the shape the plan describes*. A field that exists but is nullable when the plan assumes NOT NULL is a premise failure, not a match.

Also confirm the assumed starting state: current behaviour, existing data shape, which migrations have already been applied. Record each premise as confirmed, missing, or mismatched, with the evidence. Confirmed premises belong in the report too — they are what makes "no issues found" mean something.

### 3. Map the affected surface with codegraph

Call sites and sync points are, by definition, not written in the plan. Mapping them is how you find the work the plan did not account for.

**First, get a usable index.** Start with `codegraph_status`. If it fails, resist reading every failure as "no index" — three causes look alike and need opposite responses:

- **Index exists, the server just can't find it.** The error mentions a working-directory or workspace-root problem and typically says the index is probably fine. Retry the same call with an explicit `projectPath` pointing at the repo root. This recovers a working index in one call, so never rebuild for this cause.
- **Index exists but is stale.** Run `codegraph sync` — it processes only changes since the last index, is cheap, and matters here because the files lagging behind are usually the ones the plan is about to touch.
- **Never initialized** (no `.codegraph/` directory). Stop and ask before building anything. A full index is a write into their repo that can run for many minutes and leave hundreds of megabytes to over a gigabyte, and `codegraph init` does not reliably add it to `.gitignore`. Give them what they need to decide: the repo's file count (`git ls-files | wc -l`) as a scale signal, the command `codegraph init --index`, and the gitignore reminder. Wait for the answer. If they decline, fall back to Grep + Read and say so in 已核对范围, so the weaker coverage is visible in the report.

**Then map the surface** for each symbol in the change set:

- `codegraph_context` gives definition + callers + callees in one call — start there. Add `codegraph_callers` where the plan changes a signature, return shape, or side effect; `codegraph_impact` for renames, enum changes, or schema changes; `codegraph_explore` to survey several related symbols at once. Follow the codegraph server's own tool-selection guidance rather than re-deriving it.
- How far to walk: one layer of callers and callees is the floor. Go deeper only where a contract moves — signature, return shape, enum, schema, API payload — since that is where breakage hides, and it keeps the review from becoming a whole-repo audit.

The surface includes frontend components, hooks, stores, API clients, routes, and UI state; backend APIs, schemas, services, repositories, models, migrations, tasks, notifications, and permission logic; plus tests, docs, and config where this plan requires them.

### 4. Isolate the current problem, then walk its chain to the end

This is the step that existing, stable codebases most need, and the one a greenfield plan can mostly skip. Two opposite failure modes look like diligence:

- **Truncation** — the plan patches only the entry point the user named, and misses sibling sites on the *same* problem. Seat-limit on the invite API but not on CSV bulk invite, and not on accept-invitation, leaves the original hole open.
- **Leakage** — the plan mutates a shared function, schema, enum, or return shape in a way that other businesses, which merely happen to share that code, must now change too. Turning `invite_member` into a boolean, or adding a required argument to `audit.record`, is how a seat-limit plan quietly becomes a cross-business rewrite.

The review holds both at once: **complete along this problem's chain, and silent toward every other business.** Looking at other callers is required — that is how you know you will not break them. Changing those other businesses is not.

**Draw the current problem chain as a sequence**, from trigger to terminal side effect, using only what belongs to *this* requirement. A typical chain is: the user-facing trigger → every write-path that can produce the same fact (API, job, webhook, admin) → the matching read/validate path → the side effects that make *this* problem true (the specific notification, audit action, billing tick, cache key). Write it down. A chain that was never named cannot be checked for holes.

**Walk that chain to the end.** Every node the plan omitted is 必须补齐 — it is still this problem, not a new one. Shared helpers used *only* as an implementation detail of this chain (a repository function called solely from the invite flow) stay on the chain.

**Then split the mapped callers.** For each shared symbol the plan would mutate (signature, return shape, enum, schema, required field, side effect):

- Callers **on this chain** must be updated with it. Missing them is truncation.
- Callers **off this chain** must keep working with the existing contract. If the plan would break them, that is 阻塞, and the usual repair is to adapt at the current-problem layer — a wrapper, a new field with a default, a new endpoint, an error object added beside the existing dict — rather than changing the shared contract. A shared-contract change that other businesses cannot avoid is no longer this problem; it needs explicit user approval before it belongs in the plan.

While walking the chain and splitting callers, sweep the sync domains that plans most often forget — credits, org membership, notifications, audit logs, usage records, task status, cache invalidation, and the matching client / server / service / repository layers. What you find here feeds both 当前问题链 and 业务同步 in the report.

On a 新项目, there is little existing business to isolate from. Still name and walk the feature's own chain — truncation is just as expensive when the product is new.

### 5. Check for missing or incorrect logic

Walk the plan against: happy path, edge cases, empty and error states, permissions, retries and idempotency, concurrency, data consistency, and API contract mismatches.

Every claim needs a concrete observation behind it — a file read, a codegraph result, a grep hit. "Probably handled" inferred from naming or memory is exactly how reviews pass broken plans.

### 6. Audit the plan as a plan

Steps 4 and 5 ask whether the plan's content is right. This step asks whether it works *as a sequence of actions* — the failure mode where every individual step is correct and the plan still breaks production halfway through. These four checks are only meaningful before implementation, which is why they belong here and nowhere else.

**Ordering and dependencies.** Walk the steps in the order given and ask what the system looks like between each pair. Adding a NOT NULL column before the backfill, deploying a client that calls an endpoint that ships next week, switching reads before the dual-write has caught up, dropping a column while old pods still select it — each step is fine and the sequence still takes the site down. Where order matters, say what must precede what and why.

**Staged delivery.** Can this land in pieces that are each independently shippable and independently revertible? A plan that only works once every step is done concentrates all its risk into one moment. If it can be split, propose the split points; if it genuinely cannot, say so — that is worth knowing explicitly rather than discovering later.

**Per-step acceptance criteria.** For each step, name what would prove it was done correctly: a specific test, a query, a log line, a manual check. A step nobody can verify is either underspecified or untestable, and both belong in 必须补齐. This is also the cheapest way to expose vague steps — "更新相关逻辑" survives a read-through but not the question "how would we know this is done?"

**Approach selection.** Consider whether an obviously simpler or safer path was skipped. Raise it only when the alternative materially reduces cost or risk, and state it as one sentence plus the trade-off, leaving the decision to the user. If the alternative is merely equivalent, or a matter of taste, staying quiet is the right call — this is the dimension most likely to turn a review into a redesign, and a review that redesigns is no longer reviewing. When the chosen path is sound, say so in one line; that is a useful result, not an empty section.

### 7. Classify, rank, and write findings back into the plan

Sort every finding into one of two buckets:

- **必须补齐 (Current Fix Required)** — needed to make *this* problem correctly solved. That includes holes on the current problem chain (truncation) and planned mutations that would break off-chain callers (leakage) — leakage is 阻塞, and the inserted step should preserve the shared contract, not expand the plan into those other businesses. Tag each so the user knows where to start: `阻塞` (the plan is wrong, or will break something as written), `重要` (correct but incomplete — an unhandled edge case, error state, sync point, or missing ordering constraint), `次要` (belongs in this plan, low risk if deferred). Order the list by severity.
- **暂不处理 (Out Of Scope)** — adjacent or newly discovered problems. Report them and wait for approval. They do not go into the plan.

Then update the plan document, because findings that live only in chat vanish when the conversation moves on, which defeats the review:

- Insert every 必须补齐 item as a concrete step in the plan.
- Preserve the plan's existing structure, ordering, and language, and insert each item at the right stage (analysis / change / verification) so the plan stays the single source of truth.
- Mark inserted items so they trace back to this review — a short tag like `补充于评审` is enough.
- If ordering findings from step 6 require resequencing, reorder the steps and note why at the point of change rather than silently rearranging.

### 8. Report using the template below, then stop

Keep the report proportional to the plan: a section with nothing to flag gets one line of conclusion, not padding — the fixed headings are for skimming, not for filling. Reporting is where this skill ends. Implementation is a separate request, made by the user, after they have read the findings.

## Anti-patterns (red flags)

| Thought | Reality |
|---|---|
| "计划里这些字段/表/接口应该都是有的" | Not evidence. Read them. A plan built on a misremembered schema fails at step one, and this is the single most common way plans collapse. |
| "计划读下来挺完整的" | Completeness is not something you read off a document; it comes from walking the change set against callers, sync points, and states. |
| "顺手把方案重新设计一下" | Out of bounds. The job is finding holes and sequencing risk, not swapping approaches. Propose an alternative only when it materially cuts cost or risk, in one sentence, and let the user decide. |
| "顺便把这个也一起改了" / "和当前问题无关，但都看到了" | Scope creep either way. Goes to 暂不处理, never into the plan. |
| "只改用户点名的那一个入口就够了" | Truncation. If another write-path, accept-path, or side effect on *this* chain can still produce the old fact, the original problem is not solved. |
| "这个函数反正要改，顺手把返回类型/参数也清一下" / "别的调用方一起改掉，保持一致" | Leakage, unless those callers are on this chain. Off-chain callers must keep the existing contract; adapt at the current-problem layer instead. |
| "步骤顺序实施的时候再说" | Ordering *is* the plan. A correct set of steps in the wrong order still breaks production between steps. |
| "验收标准等做的时候再补" | A step nobody can verify is underspecified. That is a finding, not a formality. |
| "计划没写但实现的时候自然会想到" | If it were reliably remembered it would already be in the plan. Unwritten is unplanned. |
| "先按计划开工，边做边发现问题" | That is exactly the cost this review exists to avoid — a finding made now is free, the same one made mid-implementation is rework. |
| "codegraph 慢，先跳过" | Querying is sub-millisecond — the index already did the work, and skipping it is the biggest cause of missed sync points. Building an index from scratch is the expensive part, and that decision belongs to the user (step 3). |
| "status 报错了，那就是没索引，我先 index 一下" | Most `status` failures are a workspace-root detection problem on an index that is perfectly fine. Retry with `projectPath` first; a needless full re-index can burn many minutes. |

## Locating the plan

When deciding which document to review and write findings back into:

1. A plan file the user explicitly pointed at this turn.
2. A new or modified plan / RFC document on the current branch. Find where this repo actually keeps them — check `git diff --name-only` and `git status` against the repo's own convention (`docs/**/plans/**`, `rfcs/`, `.plans/`, or whatever exists) rather than assuming a fixed path.
3. The active TodoList in this session.
4. Nothing written yet → draft it per step 1 before reviewing.

## Output format

```markdown
[计划评审]
结论：[可以开工 / 需补齐 N 项（含 M 项阻塞） / 需重新规划]
当前问题边界：[one sentence]
仓库语境：[新项目 / 已有稳定代码]
计划：[path]（或"对话内方案，已落成 [path]"）
变更集（计划声称触及）：[N 个文件/符号：a / b / c]

当前问题链：
- [触发] → [写入路径（含并行入口）] → [读取/校验] → [本问题的副作用]
- 链上每个节点标 已覆盖 / 计划漏列

隔离（已有稳定代码）：
- [共享符号] : [链外调用方] → [本次改动是否扰动其契约或流程；无则写「不扰动」]
（新项目写「无既有业务面需隔离」）

前提核对：
- [符号 / 字段 / 表 / 端点 / 配置键] : [存在且与计划一致 / 不存在 / 形状不符] — 证据：[file:line]
- [...] : [...]

已核对范围：
- [file or symbol] : [codegraph_context / codegraph_callers / Read / Grep]
- [...] : [...]
（相邻但未覆盖的面也要诚实列出，写"未核对"）

必须补齐：（按严重度排序）
- [阻塞] [finding] — 证据：[file:line 或 codegraph 结果摘要]
- [重要] [finding] — 证据：[...]

计划可执行性：
- 顺序与依赖：[必须先于什么，以及中间态的风险；无问题则写"顺序无阻塞"]
- 分阶段：[可独立上线的切分点，或说明为何无法切分]
- 验收标准：[缺少验收方式的步骤；已有的写"每步可验证"]
- 选型：[仅在存在实质更优路径时给出一句话与代价对比；否则写"当前路径合理"]

业务同步：
- [client / server / service / repository / test / doc 需要同步的点]

暂不处理：
- [new or unrelated issue, pending user confirmation]

计划已更新：
- [plan file path] → [新增/修改/重排的步骤摘要]

下一步：
- [focused action or confirmation request]
```

If nothing is wrong, write `结论：可以开工` and drop 必须补齐 / 暂不处理 — but keep 前提核对、已核对范围、当前问题链、隔离 and 计划可执行性. "No issues" without evidence is rubber-stamping, not review.
