# 计划基准（plan-document baseline machinery）

Read this file when the review baseline is a plan document（计划基准）. Everything in this file is switched off under 需求基准 — with no plan document there is no 计划符合度 against a document, no 计划更新建议 section, and no plan choices in the closing question.

## Conformance specifics beyond the shared audit

- **Acceptance criteria are part of conformance.** A criterion the plan names but nobody ran — "非成员返回 403" with no test behind it — is 未实现 even when the happy-path code exists. The plan already names its checks, which also makes them the cheapest verification available in checklist step 10; skipping them is exactly how an unmet criterion slips through as "done".

## Drafting the 计划更新建议 (plan update proposal)

Draft the plan update as a *proposal* in the report's 计划更新建议 section; do **not** edit the plan document in 评审模式. The plan was already executed once; rewriting it mid-review destroys the record of what the implementation was actually built against, and the user may prefer to fix the code without touching the plan at all. That call is theirs. The proposal must still be concrete enough to apply verbatim once approved:

- List every 必须补齐 item as the exact step it would become, matching the plan's existing structure, ordering, and language, placed at the right stage (analysis / change / verification).
- Include the traceability tag the inserted steps would carry — a short tag like `补充于评审` is enough.
- 计划外改动 judged necessary goes into the proposal too, so the document can catch up with reality if the user says yes; 计划外改动 judged as scope creep goes to 暂不处理 instead.

## Report additions

Optional template section — only when there is content to write back; renumber with the rest of the report:

```markdown
### N. 计划更新建议（仅提案，评审阶段不改动计划文件）

- N.1 [plan file path] → [拟新增/修改的具体步骤，含 `补充于评审` 标记]
```

Closing question（下一步）— this form **replaces** the 需求基准 form; never emit both:

```markdown
### 下一步

请选择处理方式，可直接回复选项字母：

- **A** — 先同步计划再修复（先把"计划更新建议"写入计划文档，再修代码）
- **B** — 仅修复代码（计划保持原样）
- **C** — 仅更新计划（暂不改代码）
```

With pre-authorization (see `fix-mode.md`), 明确 items are already fixed when the report lands, so the closing question narrows to: whether to 同步计划, and how to handle the reviewer-discovered items.

## Plan handling in 修复模式

When the user chooses, execution follows `fix-mode.md`, with the plan-document part resolved first:

- **A（先同步计划再修复）** or **C（仅更新计划）** → apply the 计划更新建议 to the plan document verbatim first; under C, touch no code.
- **B（仅修复代码）** → leave the plan document exactly as written.

## Anti-patterns

| Thought | Reality |
|---|---|
| "代码和计划不一样，把计划改成和代码一致就行" | That launders a silent deviation into retroactive truth. Flag the deviation; the user decides which side is right. |
| "评审完顺手把必修项写进计划文档" | Plan documents are repo files too, and this plan was already executed once. 评审模式 writes nothing; the proposal waits in 计划更新建议 until the user picks 同步计划 or 仅修复代码. |
