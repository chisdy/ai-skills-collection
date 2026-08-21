---
name: implementation-review
description: Reviews the code written for one plan after implementation — the post-code counterpart to plan-review. Establishes the change set from git diff, audits plan-to-code conformance in both directions (unimplemented steps, silent deviations, unplanned changes), maps off-diff callers and sync sites with codegraph, checks logic completeness and business-layer synchronization, runs a security review over the change's attack surface (authorization, injection, sensitive-data exposure, input validation, dangerous primitives), and reviews code quality (readability, structure, performance) with blocking findings separated from non-blocking suggestions. Writes must-fix findings back into the plan document. Use only when explicitly requested.
disable-model-invocation: true
metadata:
  version: "1.1.0"
  author: chisdy
---

# Implementation Review

## Goal

Review the diff produced by implementing one plan, and answer four questions with evidence:

1. **Conformance** — hold the plan in one hand and the diff in the other: do they match? Every plan step lands as 已实现 / 部分实现 / 未实现 / 偏离, and every diff hunk traces back to a step — or gets named as unplanned.
2. **Correctness** — is the code right beyond what the diff shows: logic and edge cases, off-diff callers that still assume the old contract, business-layer sync sites that never got the memo?
3. **Safety** — does the change open a security hole on the surface it adds or touches?
4. **Quality** — is the code worth merging as written: readable, structured to fit the system, free of complexity that a named restructuring would remove?

**The approval standard:** approve a change when it definitely improves overall code health, even if it is not perfect. Perfect code does not exist; the goal is continuous improvement. "Not how I would have written it" is a preference, not a finding — blocking on it teaches authors to ignore reviews. This is why quality findings are split into blocking and non-blocking below.

This is the post-code counterpart to plan-review. plan-review runs before a line exists, when every finding is free to act on; this skill runs after, when every finding is already rework — which is exactly why it must be caught now, before the change ships and the cost multiplies again.

The diff itself is the one thing the author has already stared at. The expensive findings live where the diff cannot show them: the caller in another file, the plan step that quietly fell out, the acceptance criterion nobody ran, the endpoint nobody thought to attack. Weight the review toward those.

These instructions are in English; the deliverable is not. Write the review in 简体中文 following the template at the end, so section headings stay stable and the user can skim for the parts they care about.

## Two modes

This skill is a review, not a rewrite. Keeping the phases separate is what makes the output auditable — a review that quietly turns into a patch leaves the user unable to tell what was found from what was changed.

- **`[模式：评审]`** — the default, and the only mode to enter unprompted. Read code, query codegraph, run read-only verification. The only repo files to edit are the plan documents in step 8; implementation code stays untouched. Refreshing the codegraph index (`codegraph sync`, or an init the user approved) does not count as an edit — it updates a local index, not the repo's source.
- **`[模式：修复]`** — requires the user to approve a specific list of 必须补齐 items. Implement exactly those, then re-verify.

Wanting to fix something mid-review — a broken caller, a type error, even a security hole — is the signal to finish the review and ask, not to start editing.

## Checklist

### 1. Establish the change set from git, then state the boundary

A review built on what the conversation happens to mention will miss whatever was changed silently, so start from the repository's own record:

- `git status` and `git diff` for uncommitted work; `git diff <base>...HEAD` when the change spans a branch. Extract the changed files, hunks, and symbol names — steps 2 and 3 need that list as input, and it goes into the 变更集 line so the user can confirm you reviewed the right thing.
- State the issue boundary in one sentence. If the diff appears to solve something other than what the user described, flag the mismatch and ask rather than reviewing against a guessed intent.
- No diff at all → this is the wrong skill: reviewing a not-yet-implemented plan is plan-review's territory. Say so instead of reviewing an imaginary implementation.

### 2. Locate the plan and audit conformance in both directions

This is the step that separates this skill from a generic code review: the code was written *for a plan*, so the plan is the review's spec.

- Locate the plan per *Locating the plan* below. If no plan document exists, still review the diff — steps 3 through 7 do not need one — but record the gap in the report and propose writing a short plan doc, because findings need somewhere durable to live and 计划已更新 will otherwise have no target.
- **Plan → code.** Mark each plan step 已实现 / 部分实现 / 未实现 / 偏离, with evidence. 偏离 means implemented differently than written; defensible or not, a silent deviation is a finding — the user decides whether the plan or the code is the truth. Do not silently rewrite either to match the other.
- **Code → plan.** Every diff hunk that no plan step accounts for is 计划外改动. Sometimes it is a necessary discovery made mid-implementation and should be written back into the plan; sometimes it is scope creep and belongs in 暂不处理; and occasionally it is where the bug or the hole hides — unplanned code received zero review at planning time, by definition.
- **Acceptance criteria are part of conformance.** A criterion the plan names but nobody ran — "非成员返回 403" with no test behind it — is 未实现 even when the happy-path code exists.

### 3. Map the affected surface with codegraph

Call sites and sync points are by definition not in the diff. Mapping them is what separates a real review from re-reading what the author already read.

**First, get a usable index.** Start with `codegraph_status`. If it fails, resist reading every failure as "no index" — three causes look alike and need opposite responses:

- **Index exists, the server just can't find it.** The error mentions a working-directory or workspace-root problem and typically says the index is probably fine. Retry the same call with an explicit `projectPath` pointing at the repo root. This recovers a working index in one call, so never rebuild for this cause.
- **Index exists but is stale.** Run `codegraph sync` — it processes only changes since the last index, is cheap, and matters especially here: the files lagging behind the index are usually the exact ones under review.
- **Never initialized** (no `.codegraph/` directory). Stop and ask before building anything. A full index is a write into their repo that can run for many minutes and leave hundreds of megabytes to over a gigabyte, and `codegraph init` does not reliably add it to `.gitignore`. Give them what they need to decide: the repo's file count (`git ls-files | wc -l`) as a scale signal, the command `codegraph init --index`, and the gitignore reminder. Wait for the answer. If they decline, fall back to Grep + Read and say so in 已核对范围, so the weaker coverage is visible in the report.

**Then map the surface** for each changed symbol:

- `codegraph_context` gives definition + callers + callees in one call — start there. Add `codegraph_callers` when a signature, return shape, or side effect changed; `codegraph_impact` for renames, enum or schema changes; `codegraph_explore` to survey several related symbols at once. Follow the codegraph server's own tool-selection guidance rather than re-deriving it.
- How far to walk: one layer of callers and callees is the floor for every change. Go deeper only where a contract moved — signature, return shape, enum, schema, API payload — since that is where breakage hides, and it keeps the review from expanding into a whole-repo audit.

The surface includes frontend components, hooks, stores, API clients, routes, and UI state; backend APIs, schemas, services, repositories, models, migrations, tasks, notifications, and permission logic; plus tests, docs, and config where this change requires them.

### 4. Check for missing or incorrect logic

Walk the implementation against: happy path, edge cases, empty and error states, permissions, retries and idempotency, concurrency, data consistency, and API contract mismatches.

Every claim needs a concrete observation behind it — a file read, a codegraph result, a grep hit, or a verification run. "Probably handled" inferred from naming or memory is exactly how reviews pass broken code.

### 5. Check business synchronization

Credits, org membership, notifications, audit logs, usage records, task status, cache invalidation, and matching client / server / service / repository changes. Use `codegraph_callers` / `codegraph_impact` on the changed entity (model field, enum, API shape) to find every downstream site that must move with it. What the plan forgot here, the implementation usually forgot too — this is where the two reviews overlap on purpose.

### 6. Run the security review over the change's attack surface

New code is where holes enter a codebase, and the moment it lands is the cheapest moment to catch them. The attack surface of this change is whatever the diff adds or alters that outside input can reach: new or changed endpoints and their parameters, new file / network / subprocess operations, new rendering or logging of user data, new authorization decisions.

Sweep these domains against that surface:

- **权限** — every new or changed entry point must verify the caller's right *to the specific resource*, not merely that some caller is logged in. A resource id taken from the request and used without an ownership or membership check is an IDOR. An authorization requirement stated in the plan's acceptance criteria and skipped in code is simultaneously a conformance failure and a security finding.
- **注入** — SQL, shell commands, file paths, or HTML assembled by string interpolation from user input: f-strings into `execute`, `subprocess` with `shell=True`, path joins with user-supplied filenames, unescaped rendering.
- **敏感数据** — response fields beyond what the plan specifies; tokens, credentials, or PII flowing into logs, audit records, or error messages; secrets hardcoded in the diff.
- **输入校验** — boundary validation at system entry points; unbounded sizes (file uploads, list lengths, pagination); mass assignment where a request dict is written wholesale into a model.
- **危险原语** — `eval` / `exec` / unpickling untrusted data, requests to user-supplied URLs (SSRF), weak randomness for tokens, disabled TLS verification.

Two scope rules keep this from becoming a whole-repo security audit:

- A pre-existing vulnerability the diff does not touch goes to 暂不处理 — report it, do not fix it. But if the diff copies or extends the vulnerable pattern, the new instance is in scope: the change is actively spreading the hole.
- The client is never a trust boundary. "The value comes from a dropdown" or "the internal service always sends valid ids" are statements about the happy path, not about what an attacker can send.

Severity maps onto the standard tags: reachable and exploitable by an ordinary user → `阻塞`; requires unusual preconditions or an already-privileged position → `重要`; hardening and defense-in-depth → `次要`. Mark every security finding with an additional `[安全]` tag so it stands out in 必须补齐.

### 7. Review code quality: readability, structure, performance

A change can be conformant, correct, and secure, and still not be worth merging as written — or, more often, be worth merging with suggestions attached. Hold the approval standard from the Goal while sweeping:

- **Readability** — names carry meaning in context (no bare `temp` / `data` / `result`); control flow is straightforward; no clever tricks a simpler form would replace; comments explain non-obvious intent only. Code this diff orphaned — a helper nothing calls anymore, a replaced component, a dangling constant — gets listed explicitly; whether to delete it now is the user's call, not a silent edit.
- **Structure** — the change fits the system it lands in. Watch for: a new conditional bolted onto an unrelated flow (a missing helper, state, or policy — design smell, not a nit); feature-specific logic entering a shared or general-purpose module; a bespoke near-duplicate of an existing canonical helper; an abstraction that has not earned its complexity (don't generalize before the third use); a refactor that relocates complexity instead of reducing it — count the concepts a reader must hold, and if the count is unchanged, it is not cleaner. A diff that mixes refactoring with behavior change is two changes; suggest the split.
- **Performance** — N+1 query patterns, unbounded loops or unconstrained fetches, missing pagination on new list endpoints, synchronous work that should be async. Quantify where possible: "adds one query per member on a list that can hold thousands" lands; "could be slow" does not.
- **Dependencies** — a new or upgraded dependency inside the diff is its own finding: does the existing stack already cover it, is it maintained, does the lockfile diff match what was claimed?

When flagging a structural problem, propose the named move — extract the helper, replace the conditional chain with a dispatcher, relocate the logic to its owning module, delete the pass-through wrapper — not just the complaint. A review that only says "this is complex" leaves the author guessing.

Route quality findings by consequence, not by axis: one that threatens the correctness, safety, or maintainability of *this* change (feature logic contaminating a shared module, an N+1 on a hot path, dead code shadowing live code) goes to 必须补齐 with a normal severity tag. Everything else — style, naming, simplifications, "consider" items — goes to 改进建议, explicitly non-blocking, and the user may ignore it freely. Mixing the two is how reviews train authors to skim past everything; and if there is one structural problem and ten nits, the structural problem *is* the review — a few high-conviction findings beat a long list.

### 8. Classify, rank, and write findings back into the plan

Sort every finding into one of three buckets:

- **必须补齐 (Current Fix Required)** — needed to make this change correct and safe to ship: conformance gaps (未实现 / 偏离 steps), broken off-diff callers, missing business sync, in-scope security findings, and quality findings with real consequence (step 7). Tag each `阻塞` / `重要` / `次要` (plus `[安全]` where it applies) and order the list by severity.
- **改进建议 (Suggestions)** — non-blocking quality items from step 7. The user may adopt or ignore them; they never gate the 结论 and never go into the plan unless the user asks.
- **暂不处理 (Out Of Scope)** — adjacent or newly discovered problems, including untouched pre-existing vulnerabilities. Report them and wait for approval. They do not go into the plan. "先合了以后再清理" belongs here too, as a written item the user signs off — deferred cleanup that lives nowhere never happens.

Then update the plan document, because findings that live only in chat vanish when the conversation moves on:

- Insert every 必须补齐 item as a concrete step, preserving the plan's existing structure, ordering, and language, at the right stage (analysis / change / verification).
- Mark inserted items so they trace back to this review — a short tag like `补充于评审` is enough.
- 计划外改动 judged necessary gets written into the plan too, so the document catches up with reality; 计划外改动 judged as scope creep goes to 暂不处理 instead.
- If no plan document exists, propose creating one before continuing; do not let findings live only in chat.

### 9. Verify with the narrowest check that produces evidence

Read-only checks belong in 评审模式 — they are what turn assertions into evidence. The code exists, so verify it directly:

- type-check / lint on touched files (always)
- **the plan's own acceptance criteria for steps marked 已实现** — the plan already names its checks, which makes them the cheapest verification available, and skipping them is exactly how an unmet criterion slips through as "done"
- the most relevant single test file, not the full suite
- DB changes → migration dry-run or schema diff
- API contract changes → the affected endpoint's contract or integration test
- frontend → component test, plus a manual browser check only if interaction logic moved

If the project supplies domain conventions (a tech-stack or coding-standards skill or rule), consult it for business-sync specifics — DB constraints, container exec, test locations, naming — instead of assuming defaults.

### 10. Report using the template below, then stop

A failing check is a finding, not a detour: record it under 必须补齐 with the actual error output as evidence and let severity reflect it. Keep the report proportional to the change — a section with nothing to flag gets one line, not padding. 评审模式 ends here.

**`[模式：修复]` only, after approval:** restate the approved 必须补齐 list (plus any 改进建议 the user explicitly adopted), implement exactly those items, re-run the step 9 verification, and report any remaining risk. Anything not on the approved list stays in 暂不处理.

## Anti-patterns (red flags)

| Thought | Reality |
|---|---|
| "顺手把这个也修了" / "写都写了" | Scope creep either way. Goes to 暂不处理, never into the fix or the plan. |
| "对话里说改了哪些文件，照着看就行" | Only `git diff` is the fact. Silent changes are exactly what a review exists to catch. |
| "看名字应该处理了 error case" | Not evidence. Read the code or run the test. |
| "只看 diff 就够了" | The diff cannot show call sites, sync points, or the plan step that fell out. At minimum walk one layer of callers/callees and every plan step. |
| "测试应该会覆盖" | Open the test file and verify. Acceptance criteria without a check behind them are 未实现. |
| "type-check 挂了，我先修一下" | That is 修复模式 without approval. Record the error as a finding and ask. |
| "代码和计划不一样，把计划改成和代码一致就行" | That launders a silent deviation into retroactive truth. Flag the deviation; the user decides which side is right. |
| "这段代码计划里没写，但看着有用，就不提了" | Unplanned code received zero planning review — it is where bugs and holes hide. Name it as 计划外改动 and judge it. |
| "内部接口/内网服务，不用做权限校验" | An assumption about deployment is not a trust boundary. Check the caller's right to the resource. |
| "参数来自前端下拉框，值是固定的" | The client is never a trust boundary. Review what an attacker can send, not what the UI sends. |
| "这个漏洞是老代码带的，不关这次 diff" | Untouched → report in 暂不处理, don't fix. But if the diff copies or extends the pattern, the new instance belongs to this change. |
| "测试都过了，代码就没问题" | Tests are necessary, not sufficient — they catch neither architecture problems, nor security holes, nor unreadable code. |
| "能跑就行，可读性以后再说" | Working code that is unreadable or misplaced compounds debt. Quality is an axis of this review; route it per step 7. |
| "不是我喜欢的写法，让作者改掉" | Preference is not a finding. If the change improves code health and follows conventions, it passes; taste goes to 改进建议. |
| "重构完看起来干净多了" | Relocating complexity is not reducing it. Count the concepts a reader must hold — unchanged count means unchanged structure. |
| "先合了，这些小问题以后再清" | Deferred cleanup that lives nowhere never happens. Either it enters 必须补齐 now, or it is a written 暂不处理 item the user signs off. |
| "codegraph 慢，先跳过" | Querying is sub-millisecond — the index already did the work, and skipping it is the biggest cause of missed sync points. Building an index from scratch is the expensive part, and that decision belongs to the user (step 3). |
| "status 报错了，那就是没索引，我先 index 一下" | Most `status` failures are a workspace-root detection problem on an index that is perfectly fine. Retry with `projectPath` first; a needless full re-index can burn many minutes. |

## Locating the plan

When deciding which document to check conformance against and write findings back into:

1. A plan file the user explicitly pointed at this turn.
2. A new or modified plan / RFC document on the current branch. Find where this repo actually keeps them — check `git diff --name-only` and `git status` against the repo's own convention (`docs/**/plans/**`, `rfcs/`, `.plans/`, or whatever exists) rather than assuming a fixed path.
3. The active TodoList in this session.
4. Nothing written → review the diff anyway, record the gap, and propose creating a plan doc so findings have somewhere durable to live.

## Output format

```markdown
[模式：评审]
结论：[可以合并 / 需补齐 N 项（含 M 项阻塞、K 项安全） / 需返工]
当前问题边界：[one sentence]
变更集：[N 个文件，关键符号 a / b / c]（来源：git diff）
计划：[path]（或"无计划文档，建议先补一份"）

计划符合度：
- [步骤 N：一句话概括] : [已实现 / 部分实现 / 未实现 / 偏离（怎么偏的）] — 证据：[file:line 或测试结果]
- 计划外改动：[hunk 概述 → 判定：应写回计划 / 属暂不处理]（无则写"无"）

已核对范围：
- [file or symbol] : [codegraph_context / codegraph_callers / Read / Grep / 运行测试]
- [...] : [...]
（相邻但未覆盖的面也要诚实列出，写"未核对"）

必须补齐：（按严重度排序，安全项加 [安全] 标记）
- [阻塞][安全] [finding] — 证据：[file:line 或 codegraph 结果摘要]
- [重要] [finding] — 证据：[...]

逻辑风险：
- [risk tied to current change]

业务同步：
- [client / server / service / repository / test / doc sync required]

安全评审：
- [权限 / 注入 / 敏感数据 / 输入校验 / 危险原语] → [发现（对应必须补齐第 N 条）或"未发现"]

改进建议：（不阻塞合并，可自行取舍；结构性建议附具名解法）
- [suggestion] — [具名解法：提取 helper / 换 dispatcher / 移回所属模块 / …]

暂不处理：
- [new or unrelated issue, incl. untouched pre-existing vulnerabilities and deferred cleanup, pending user confirmation]

已执行验证：
- [command 或验收核对动作] → [结果]

计划已更新：
- [plan file path] → [新增/修改的步骤摘要]（若无计划文件则写明"无现有计划，建议先建立"）

下一步：
- [focused action or confirmation request]
```

If nothing is wrong, write `结论：可以合并` and drop 必须补齐 / 改进建议 / 暂不处理 / 计划已更新 — but keep 计划符合度、已核对范围、安全评审 and 已执行验证. "No issues" without evidence is rubber-stamping, not review. 改进建议 alone never changes the 结论: a change with only suggestions attached is still 可以合并.
