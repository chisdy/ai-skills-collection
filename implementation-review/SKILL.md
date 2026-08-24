---
name: implementation-review
description: Post-implementation code review against the change's own baseline — a plan document when one exists, or the user's stated requirement when none does. Audits baseline-to-code conformance in both directions, maps off-diff callers and business sync sites with codegraph, runs a security review over the changed attack surface, and reviews code quality with blocking findings separated from non-blocking suggestions. Establishes the change set from git diff, falling back to the session's edit record when git has nothing usable. Review-only by default — code and plan documents are modified only after explicit user approval. Use only when explicitly requested.
disable-model-invocation: true
metadata:
  version: "2.0.0"
  author: chisdy
---

# Implementation Review

## Goal

Review the change set produced by implementing one request — established from git diff, or from the session's edit record when git has nothing usable (see step 1) — and answer four questions with evidence:

1. **Conformance** — hold the review baseline in one hand and the change in the other: do they match? The baseline is the plan document when one exists, or the user's stated requirement when none does (see *Establishing the baseline*). Every baseline item lands as 已实现 / 部分实现 / 未实现 / 偏离, and every diff hunk traces back to an item — or gets named as unplanned.
2. **Correctness** — is the code right beyond what the diff shows: logic and edge cases, off-diff callers that still assume the old contract, business-layer sync sites that never got the memo?
3. **Safety** — does the change open a security hole on the surface it adds or touches?
4. **Quality** — is the code worth merging as written: readable, structured to fit the system, free of complexity that a named restructuring would remove?

**The approval standard:** approve a change when it definitely improves overall code health, even if it is not perfect. Perfect code does not exist; the goal is continuous improvement. "Not how I would have written it" is a preference, not a finding — blocking on it teaches authors to ignore reviews. This is why quality findings are split into blocking and non-blocking below.

This is the post-code counterpart to plan-review. plan-review runs before a line exists, when every finding is free to act on; this skill runs after, when every finding is already rework — which is exactly why it must be caught now, before the change ships and the cost multiplies again. A plan document is *not* a prerequisite: many changes are implemented straight from a one-sentence request, and those deserve the same review — only the conformance spec changes, not the depth.

The diff itself is the one thing the author has already stared at. The expensive findings live where the diff cannot show them: the caller in another file, the plan step that quietly fell out, the acceptance criterion nobody ran, the endpoint nobody thought to attack. Weight the review toward those.

These instructions are in English; the deliverable is not. Write the review in 简体中文 following the template at the end, so section headings stay stable and the user can skim for the parts they care about.

## Reference files — load on demand

Branch-specific machinery lives in `references/` (relative to this skill's directory). Read a file **only when its trigger fires**, then follow it. The one-line hard rules in this document bound *what* is allowed either way; the reference files carry the *how*.

| File | Read when |
|---|---|
| `references/plan-baseline.md` | The baseline is a plan document (计划基准) — read during step 2, before auditing conformance. |
| `references/fix-mode.md` | The user pre-authorized fixes in the review request, or approves fixes after the report — always read **before** editing any repo file. |
| `references/session-changeset.md` | Git cannot produce a usable diff, so the change set must come from the session's edit record — read during step 1. |
| `references/codegraph-recovery.md` | `codegraph_status` fails — read before rebuilding or re-indexing anything. |

## Two modes

This skill is a review, not a rewrite. Keeping the phases separate is what makes the output auditable — a review that quietly turns into a patch leaves the user unable to tell what was found from what was changed.

- **`[模式：评审]`** — the default, and the only mode to enter unprompted. Read code, query codegraph, run read-only verification. Edit **no** repo files at all — implementation code *and* plan documents both stay untouched. Findings that need to land in a plan document go into the report as a proposal, never into the file. (Refreshing the codegraph index does not count as an edit — it updates a local index, not the repo's source.)
- **`[模式：修复]`** — requires the user to approve a specific list of 必须补齐 items; read `references/fix-mode.md` before any edit. Under 计划基准 the approval additionally chooses how to handle the plan document (三选项, see `references/plan-baseline.md`); with no plan document there is nothing to sync — the approval is simply which items to fix, and offering plan choices anyway is noise.

Wanting to fix something mid-review — a broken caller, a type error, even a security hole — is the signal to finish the review and ask, not to start editing.

**Pre-authorization.** The user may grant fix approval upfront, in the same message that requests the review ("评审完发现明确的问题直接修"). Three boundaries hold no matter what — the full rules are in `references/fix-mode.md`, read it before acting: the complete report still comes first; the authorization covers only items whose spec the user already wrote down (plan steps, stated requirements) — never reviewer-discovered findings, however obvious the fix looks; and it never covers plan documents or 暂不处理 items.

## Checklist

### 1. Establish the change set — git first, session edits as fallback

A review built on what the conversation happens to *mention* will miss whatever was changed silently, so prefer the repository's own record; but a review that refuses to run because git has nothing is equally useless when the code was demonstrably edited in this session.

**Primary — git diff (来源：git diff):**

- `git status` and `git diff` for uncommitted work; `git diff <base>...HEAD` when the change spans a branch. Extract the changed files, hunks, and symbol names — steps 2 and 3 need that list as input, and it goes into the 变更集 line so the user can confirm you reviewed the right thing.
- If the working tree mixes this task's edits with unrelated pre-existing modifications, use the session's edit record to scope which changed files belong to this review, and name the excluded files in 变更集 so the narrowing is visible — scoping is the one job the session record does even when git is available.

**Fallback — session edit record (来源：会话编辑记录):** when git cannot produce a usable diff — not a git repo, edits already committed with no identifiable base, git unavailable — read `references/session-changeset.md` and reconstruct the change set from the session's edit record. It covers recovering a base from the session's own commits before falling back, the reconstruction method, and the limits that must be declared in the report.

**Either way:**

- State the issue boundary in one sentence. If the change set appears to solve something other than what the user described, flag the mismatch and ask rather than reviewing against a guessed intent.
- No git diff *and* no session edits → this is the wrong skill: reviewing a not-yet-implemented plan is plan-review's territory. Say so instead of reviewing an imaginary implementation.

### 2. Establish the baseline and audit conformance in both directions

This is the step that separates this skill from a generic code review: the code was written *for something*, and that something is the review's spec. Determine which baseline applies per *Establishing the baseline* below. **计划基准 → read `references/plan-baseline.md` now** (acceptance-criteria auditing, the 计划更新建议 proposal, and the plan-specific closing live there). **需求基准 → all plan machinery stays off**: no 计划更新建议 section, no plan choices in the closing question, and do *not* propose writing a plan document — the user chose to work without one, and the report itself is the durable record for a change this size.

The audit runs the same two directions under either baseline:

- **Baseline → code.** Mark each plan step or requirement point 已实现 / 部分实现 / 未实现 / 偏离, with evidence. 偏离 means implemented differently than written; defensible or not, a silent deviation is a finding — the user decides whether the baseline or the code is the truth. Do not silently rewrite either side to match the other.
- **Code → baseline.** Every diff hunk (or edited region) that no baseline item accounts for is 计划外/需求外改动. Sometimes it is a necessary discovery made mid-implementation; sometimes it is scope creep and belongs in 暂不处理; and occasionally it is where the bug or the hole hides — unplanned code received zero review at planning time, by definition.
- Under 需求基准, restate the requirement as a short list of concrete requirement points (the 评审基准 line in the report), so the user can correct a misread before it distorts the whole review.

### 3. Map the affected surface with codegraph

Call sites and sync points are by definition not in the diff. Mapping them is what separates a real review from re-reading what the author already read.

**First, get a usable index.** Start with `codegraph_status`. If it fails, read `references/codegraph-recovery.md` before doing anything else — most failures are recoverable in one call, and a full `codegraph init` is a multi-minute write into the user's repo that is **never** run without asking.

**Then map the surface** for each changed symbol:

- `codegraph_context` gives definition + callers + callees in one call — start there. Add `codegraph_callers` when a signature, return shape, or side effect changed; `codegraph_impact` for renames, enum or schema changes; `codegraph_explore` to survey several related symbols at once. Follow the codegraph server's own tool-selection guidance rather than re-deriving it.
- How far to walk: one layer of callers and callees is the floor for every change. Go deeper only where a contract moved — signature, return shape, enum, schema, API payload — since that is where breakage hides, and it keeps the review from expanding into a whole-repo audit.

The surface includes frontend components, hooks, stores, API clients, routes, and UI state; backend APIs, schemas, services, repositories, models, migrations, tasks, notifications, and permission logic; plus tests, docs, and config where this change requires them.

### 4. Check for missing or incorrect logic

Walk the implementation against: happy path, edge cases, empty and error states, permissions, retries and idempotency, concurrency, data consistency, and API contract mismatches.

Every claim needs a concrete observation behind it — a file read, a codegraph result, a grep hit, or a verification run. "Probably handled" inferred from naming or memory is exactly how reviews pass broken code.

Findings from this step do not get their own report section — a logic gap with real consequence goes into 必须补齐, a genuine but out-of-scope risk into 暂不处理. A separate "逻辑风险" list that restates 必须补齐 items or pads with "无" is exactly the redundancy the report format below removes.

### 5. Check business synchronization

Credits, org membership, notifications, audit logs, usage records, task status, cache invalidation, and matching client / server / service / repository changes. Use `codegraph_callers` / `codegraph_impact` on the changed entity (model field, enum, API shape) to find every downstream site that must move with it. What the plan (or the requirement) forgot here, the implementation usually forgot too — this is where the two reviews overlap on purpose.

Same routing as step 4: a missing sync site is a 必须补齐 item with the site as evidence, not an entry in a standalone section.

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

### 8. Classify and rank the findings

Sort every finding into one of three buckets:

- **必须补齐 (Current Fix Required)** — needed to make this change correct and safe to ship: conformance gaps (未实现 / 偏离 steps), broken off-diff callers, missing business sync, in-scope security findings, and quality findings with real consequence (step 7). Tag each `阻塞` / `重要` / `次要` (plus `[安全]` where it applies) and order the list by severity.
- **改进建议 (Suggestions)** — non-blocking quality items from step 7. The user may adopt or ignore them; they never gate the 结论 and never go into the plan unless the user asks.
- **暂不处理 (Out Of Scope)** — adjacent or newly discovered problems, including untouched pre-existing vulnerabilities. Report them and wait for approval. They do not go into the plan. "先合了以后再清理" belongs here too, as a written item the user signs off — deferred cleanup that lives nowhere never happens.

Under 计划基准, additionally draft the 计划更新建议 proposal per `references/plan-baseline.md` — as a proposal in the report, never as an edit to the plan document.

### 9. Verify with the narrowest check that produces evidence

Read-only checks belong in 评审模式 — they are what turn assertions into evidence. The code exists, so verify it directly:

- type-check / lint on touched files (always)
- **the baseline's own acceptance criteria for items marked 已实现** — under 计划基准 the plan names its checks (see `references/plan-baseline.md`); skipping them is exactly how an unmet criterion slips through as "done"
- the most relevant single test file, not the full suite
- DB changes → migration dry-run or schema diff
- API contract changes → the affected endpoint's contract or integration test
- frontend → component test, plus a manual browser check only if interaction logic moved

If the project supplies domain conventions (a tech-stack or coding-standards skill or rule), consult it for business-sync specifics — DB constraints, container exec, test locations, naming — instead of assuming defaults.

### 10. Report using the template below, then stop

A failing check is a finding, not a detour: record it under 必须补齐 with the actual error output as evidence and let severity reflect it. Keep the report proportional to the change: an *optional* section with nothing to report is **dropped entirely**, not filled with "无" — the template below marks which sections are core and which are optional. A small diff against a one-line requirement should produce a report the user can read in under a minute.

End the report with the closing question that matches the baseline:

- **需求基准:** simply ask whether to fix the 必须补齐 items (all, or by number), and whether any 暂不处理 item should be pulled into scope. No plan options — there is no plan.
- **计划基准:** the 三选项 closing from `references/plan-baseline.md` replaces the 需求基准 form; never emit both.

评审模式 ends here — no file has been written. With pre-authorization, or after the user approves fixes, follow `references/fix-mode.md`.

## Anti-patterns (red flags)

| Thought | Reality |
|---|---|
| "顺手把这个也修了" / "写都写了" | Scope creep either way. Goes to 暂不处理, never into the fix or the plan. |
| "没有计划文档，先让用户补一份计划" | The user chose to work from a direct requirement; the requirement is the baseline. Review against it — demanding a plan first is process for its own sake. |
| "报告末尾照例给出同步计划三选项" | Those options only exist under 计划基准. With no plan document, ask the one real question — 修不修 — and stop. |
| "每个 section 都要写点什么才完整" | Padding is not completeness. Optional sections with nothing to report are dropped; a "逻辑风险：无" line tells the user nothing. |
| "对话里说改了哪些文件，照着看就行" | When git can produce a diff, only `git diff` is the fact — silent changes are exactly what a review exists to catch. The session edit record is the fallback for when git has nothing, not a substitute when it does. |
| "没有 git diff，那就没法评审" | The session's edit record is a legitimate change-set source (step 1 fallback, `references/session-changeset.md`). Reconstruct the change set from it, state its limits, and run the same review. |
| "看名字应该处理了 error case" | Not evidence. Read the code or run the test. |
| "只看 diff 就够了" | The diff cannot show call sites, sync points, or the plan step that fell out. At minimum walk one layer of callers/callees and every baseline item. |
| "测试应该会覆盖" | Open the test file and verify. Acceptance criteria without a check behind them are 未实现. |
| "type-check 挂了，我先修一下" | That is 修复模式 without approval. Record the error as a finding and ask. |
| "这个问题很明确，不用等批准了" | Without pre-authorization in the user's own message, every fix waits — see `references/fix-mode.md` for what a granted authorization actually covers. |
| "这段代码基准里没写，但看着有用，就不提了" | Unplanned code received zero planning review — it is where bugs and holes hide. Name it as 计划外/需求外改动 and judge it. |
| "内部接口/内网服务，不用做权限校验" | An assumption about deployment is not a trust boundary. Check the caller's right to the resource. |
| "参数来自前端下拉框，值是固定的" | The client is never a trust boundary. Review what an attacker can send, not what the UI sends. |
| "这个漏洞是老代码带的，不关这次 diff" | Untouched → report in 暂不处理, don't fix. But if the diff copies or extends the pattern, the new instance belongs to this change. |
| "测试都过了，代码就没问题" | Tests are necessary, not sufficient — they catch neither architecture problems, nor security holes, nor unreadable code. |
| "能跑就行，可读性以后再说" | Working code that is unreadable or misplaced compounds debt. Quality is an axis of this review; route it per step 7. |
| "不是我喜欢的写法，让作者改掉" | Preference is not a finding. If the change improves code health and follows conventions, it passes; taste goes to 改进建议. |
| "重构完看起来干净多了" | Relocating complexity is not reducing it. Count the concepts a reader must hold — unchanged count means unchanged structure. |
| "先合了，这些小问题以后再清" | Deferred cleanup that lives nowhere never happens. Either it enters 必须补齐 now, or it is a written 暂不处理 item the user signs off. |
| "codegraph 慢，先跳过" | Querying is sub-millisecond — the index already did the work, and skipping it is the biggest cause of missed sync points. Building an index from scratch is the expensive part, and that decision belongs to the user (see `references/codegraph-recovery.md`). |

Branch-specific anti-patterns live with their machinery: plan-document rows in `references/plan-baseline.md`, pre-authorization rows in `references/fix-mode.md`, session-fallback rows in `references/session-changeset.md`, index-recovery rows in `references/codegraph-recovery.md`.

## Establishing the baseline

When deciding what to check conformance against, walk down this list and take the first hit:

1. A plan file the user explicitly pointed at this turn → **计划基准**.
2. A new or modified plan / RFC document on the current branch → **计划基准**. Find where this repo actually keeps them — check `git diff --name-only` and `git status` against the repo's own convention (`docs/**/plans/**`, `rfcs/`, `.plans/`, or whatever exists) rather than assuming a fixed path.
3. The active TodoList in this session, when it captures the agreed scope → use it as the conformance spec (check 符合度 against its items), but since there is no document to sync, all plan-document machinery stays off and the closing question takes the 需求基准 form.
4. None of the above → **需求基准**: the user's stated requirement is the spec. Restate it, review against it, and do not propose creating a plan document.

## Output format

Core sections appear in every report: the unnumbered header block (结论 / 问题边界 / 变更集 / 评审基准), plus 符合度、已核对范围、安全评审、已执行验证 — these carry the evidence, and "no issues" without evidence is rubber-stamping. Every other section is **optional: drop it entirely when it has nothing to report** — do not write "无" as a placeholder.

**Numbering is the report's addressing scheme.** Sections are numbered `1.` `2.` `3.` …; items inside actionable sections are numbered `N.1` `N.2` … so the user can reply with bare numbers — "修复 3.1 和 3.3，5.2 也采纳" — instead of re-describing findings. Two rules make the numbers reliable:

- After dropping empty optional sections, **renumber so the displayed sequence is continuous** (1, 2, 3…), never leave gaps from a fixed scheme.
- Evidence sections (已核对范围 / 已执行验证) keep plain `-` bullets — nobody acts on those line-by-line, and numbering them buries the numbers that matter.

```markdown
[模式：评审]

结论：[可以合并 / 需补齐 N 项（含 M 项阻塞、K 项安全） / 需返工]
问题边界：[one sentence]
变更集：[N 个文件，关键符号 a / b / c]（来源：git diff ／ 会话编辑记录；会话来源时附一句局限说明）
评审基准：[计划文档 path ／ 需求基准：一句话复述用户需求]

---

### 1. 符合度（计划基准逐计划步骤核对；需求基准逐需求点核对）

- 1.1 [步骤或需求点：一句话概括] — [已实现 / 部分实现 / 未实现 / 偏离（怎么偏的）]。证据：[file:line 或测试结果]
- 1.2 [...]
- 计划外/需求外改动：[hunk 概述 → 判定：写回计划（列入 计划更新建议）/ 必要铺垫 / 属暂不处理]（无则省略本行）

### 2. 已核对范围

- [file or symbol]：[codegraph_context / codegraph_callers / Read / Grep / 运行测试]
- （相邻但未覆盖的面也要诚实列出，写"未核对"）

### 3. 必须补齐（可选节；按严重度排序，含逻辑缺陷与业务同步缺失，安全项加 [安全]，提前授权下已修复的加 [已修·提前授权]）

- 3.1 [阻塞][安全] [finding]。证据：[file:line 或 codegraph 结果摘要]
- 3.2 [重要] [finding]。证据：[...]

### 4. 安全评审

[无发现时压成一行："已检查权限 / 注入 / 敏感数据 / 输入校验 / 危险原语，未发现问题"；有发现时按域指向必须补齐对应编号，如"权限 → 见 3.1"]

### 5. 改进建议（可选节；不阻塞合并，可自行取舍；结构性建议附具名解法）

- 5.1 [suggestion] — [具名解法：提取 helper / 换 dispatcher / 移回所属模块 / …]

### 6. 暂不处理（可选节）

- 6.1 [new or unrelated issue, incl. untouched pre-existing vulnerabilities and deferred cleanup, pending user confirmation]

### 7. 已执行验证

- [command 或验收核对动作] → [结果]

---

### 下一步

（需求基准时）请确认修复范围，可直接回复编号：

- 回复"全部修复"，或指定编号（如"修复 3.1、3.3"）
- 改进建议如需采纳、暂不处理项如需纳入本次修复，也用编号一并说明（如"5.1 采纳，6.2 一起修"）
```

Under 计划基准, two additions from `references/plan-baseline.md` apply: an optional 计划更新建议 section (inserted before 下一步, renumbered with the rest), and the A/B/C 三选项 closing that **replaces** the 需求基准 下一步 block — never emit both. The section numbers above show the fullest case; a real report renumbers after dropping empty sections. When the user replies with numbers, resolve them against *this* report's numbering and restate each resolved item in one line before fixing, so a mis-typed number cannot silently authorize the wrong fix. 改进建议 alone never changes the 结论: a change with only suggestions attached is still 可以合并.
