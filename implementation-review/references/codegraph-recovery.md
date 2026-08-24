# codegraph 索引恢复

Read this file when `codegraph_status` fails. Resist reading every failure as "no index" — three causes look alike and need opposite responses:

1. **Index exists, the server just can't find it.** The error mentions a working-directory or workspace-root problem and typically says the index is probably fine. Retry the same call with an explicit `projectPath` pointing at the repo root. This recovers a working index in one call, so never rebuild for this cause.
2. **Index exists but is stale.** Run `codegraph sync` — it processes only changes since the last index, is cheap, and matters especially here: the files lagging behind the index are usually the exact ones under review. Refreshing the index does not count as a repo edit — it updates a local index, not the repo's source.
3. **Never initialized** (no `.codegraph/` directory). Stop and ask before building anything. A full index is a write into their repo that can run for many minutes and leave hundreds of megabytes to over a gigabyte, and `codegraph init` does not reliably add it to `.gitignore`. Give the user what they need to decide: the repo's file count (`git ls-files | wc -l`) as a scale signal, the command `codegraph init --index`, and the gitignore reminder. Wait for the answer. If they decline, fall back to Grep + Read and say so in 已核对范围, so the weaker coverage is visible in the report.

## Anti-patterns

| Thought | Reality |
|---|---|
| "status 报错了，那就是没索引，我先 index 一下" | Most `status` failures are a workspace-root detection problem on an index that is perfectly fine. Retry with `projectPath` first; a needless full re-index can burn many minutes. |
