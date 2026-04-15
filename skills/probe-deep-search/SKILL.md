---
name: probe-deep-search
description: Probe-first deep codebase investigation, symbol tracing, AST-pattern search, and focused code extraction using the `probe` CLI and `@probelabs/probe` SDK. Use when Codex needs to understand an unfamiliar repository, trace cross-file behavior, locate implementations before editing, audit architecture, investigate bugs, or perform deep search where `probe search`, `probe symbols`, `probe query`, and `probe extract` should be prioritized over plain-text tools such as `rg` or `grep`.
---

# Probe Deep Search

Use `probe` as the primary search surface for read-heavy code investigation. Start with `probe` before plain-text search unless `probe` is unavailable, clearly broken, or structurally incapable of answering the question.

Keep the workflow evidence-driven: broaden with `probe search`, narrow with structural passes, then extract only the exact code bodies needed. Do not drift into ad-hoc `rg`-only exploration when `probe` can still answer the question.

## Core Rules

- Start every investigation with at least one `probe` command.
- Prefer `probe search` for discovery, `probe symbols` for topology, `probe query` for AST structure, and `probe extract` for exact bodies.
- Use Boolean terms and search hints such as `ext:`, `file:`, and `dir:` to reduce noise before falling back to text search.
- Limit context deliberately with `--max-results` or `--max-tokens` when exploring large trees.
- After a broad search hit, run a structural follow-up before concluding. Typical pairs are `search -> symbols`, `search -> extract`, or `search -> query`.
- Fall back to `rg`, `grep`, or direct file reads only when `probe` fails, the index is unavailable, or the target is outside code that `probe` can interpret well.
- State when you are falling back and why.

## Investigation Workflow

### 1. Frame the search

- Translate the user request into 2-4 concrete search intents: domain terms, symbol names, error strings, execution paths, or file constraints.
- Start broad only once. After the first hit set, narrow aggressively.
- When a repo is large, include path hints early.

### 2. Run a broad `probe search`

- Use `probe search "<terms>" <path>` first.
- Add Boolean operators when the prompt includes multiple concepts.
- Add `--max-results` or `--max-tokens` to keep results reviewable.
- For code-only targeting, add file hints such as `ext:py`, `ext:ts`, or `file:src/**/*.py`.

### 3. Switch to structure

- Use `probe symbols <file>` to map a file before reading large chunks.
- Use `probe query` for AST-pattern hunting such as async functions, React components, constructors, handlers, or framework-specific shapes.
- Use `probe extract <file>:<line>`, `<file>#<symbol>`, or ranges to pull only the exact body you need.

### 4. Build the answer from evidence

- Cross-check claims against extracted code, not only ranked snippets.
- Cite the concrete symbol, file, or line-bearing extraction that supports the conclusion.
- If the user asked for deep analysis, repeat the search-structure-extract loop for adjacent callers, callees, or parallel implementations.

### 5. Fallback cleanly

- If `probe` errors, note whether the problem is indexing, unsupported files, or path noise.
- Retry with a narrower path or query once before switching tools.
- If you fall back, use the lightest alternative and preserve the same search logic.

## Task Recipes

### Unknown codebase or architecture

- Start with `probe search` on domain terms from the request.
- Use `probe symbols` on the top 2-3 files to map entry points.
- Use `probe extract` on likely orchestrators, interfaces, or handlers.
- Use `probe query` if the architecture depends on repeated patterns such as controllers, routes, jobs, or hooks.

### Bug investigation or regression tracing

- Search for the error string, feature term, or failing symbol.
- Extract the nearest implementation body.
- Search again using related state names, exceptions, or helper calls found in the extracted code.
- Trace outward to callers and validators before proposing a fix.

### Pre-edit code comprehension

- Before changing code, use `probe search` to find all likely implementations.
- Use `probe query` for structural variants of the same pattern.
- Use `probe extract` to inspect the exact body to edit and one neighboring usage site.

### Pattern inventory or refactor prep

- Use `probe query` first when the pattern is syntactic.
- Use `probe search` first when the pattern is semantic or named inconsistently.
- Combine the results into a small inventory before editing.

## References

- Read [CLI recipes](./references/cli-recipes.md) when you need ready-to-run `probe` command patterns.
- Read [Node SDK recipes](./references/node-sdk-recipes.md) when the task is inside a JavaScript or TypeScript codebase that should call `@probelabs/probe` directly.
- Read [Investigation playbook](./references/investigation-playbook.md) when the request is broad and you need a repeatable deep-search sequence.

## Output Expectations

- Summarize the search path you took: broad query, structural follow-ups, and the extracted evidence.
- Keep raw command output out of the final user-facing summary unless it is specifically requested.
- When a result is still tentative, say what additional `probe` pass would confirm it.
