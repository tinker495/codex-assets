---
name: probe-deep-search
description: Probe-first, CLI-only deep codebase investigation using local `probe` commands directly. Use when Codex needs to understand an unfamiliar repository, trace cross-file behavior, locate implementations before editing, audit architecture, investigate bugs, or perform deep search where `probe search`, `probe symbols`, `probe query`, `probe extract`, and `probe lsp` should be prioritized over plain-text tools such as `rg` or `grep`.
---

# Probe Deep Search

Use the Probe CLI as the primary read surface for code and doc investigation. In this skill, Codex remains the only agent and reasoner: use Probe only as a direct CLI retrieval tool, not as a second agent.

Keep the workflow evidence-driven: broaden with `probe search`, narrow with structural passes, then extract only the exact code bodies needed. Do not drift into ad-hoc `rg`-only exploration when `probe` can still answer the question.

## CLI-only Contract

- Prefer `probe <subcommand> ...` directly. If the binary is unavailable, fall back to `npx -y @probelabs/probe@latest <subcommand> ...`.
- Do not use `probe agent`, `npx -y @probelabs/probe@latest agent`, `probe-chat`, MCP server mode, Node SDK integration, or LLM Script from this skill.
- Do not use `probe extract --prompt ...` or `--instructions ...` here. Let Codex interpret Probe output itself.
- Start every investigation with at least one `probe` subcommand.
- Prefer the locally installed `probe ... --help` output over README snippets when they disagree. The installed binary is the source of truth for actual flags and defaults.
- Fall back to `rg`, `grep`, or direct file reads only when Probe is unavailable, broken, or structurally incapable of answering the question.
- State when you are falling back and why.

## Core Rules

- Prefer `probe search` for discovery, `probe symbols` for file topology, `probe query` for AST structure, `probe extract` for exact bodies, and `probe lsp` for cross-file semantic navigation.
- Use Boolean terms and search hints such as `ext:`, `file:`, `dir:`, `type:`, and `lang:` to reduce noise early.
- Limit context deliberately with `--max-results`, `--max-bytes`, or `--max-tokens`.
- Shape output deliberately with `--format`, `--files-only`, `--dry-run`, `--no-merge`, and `--merge-threshold`.
- Use `--exact` or `--strict-elastic-syntax` when query semantics matter more than fuzzy tokenization.
- Use `--session` when repeated search passes should avoid re-emitting the same code blocks.
- Treat `--allow-tests` as opt-in. Default to production paths unless the investigation is explicitly about tests.
- After a broad search hit, run a structural or semantic follow-up before concluding. Typical pairs are `search -> symbols`, `search -> extract`, `search -> query`, or `search -> lsp`.

## Delegation Contract

- When another skill needs probe-first repository discovery, symbol tracing, AST-pattern hunting, or exact code-body extraction, delegate that investigation layer to `probe-deep-search`.
- Parent skills keep domain ownership. `probe-deep-search` owns the `probe search -> probe symbols/query/extract/lsp` loop; the caller still owns review severity, remediation decisions, rewrite policy, or documentation synthesis.
- Prefer a short explicit handoff such as: "Use `probe-deep-search` for the discovery/structural pass, then continue here with domain-specific judgment."

## Command Surface

### Primary commands

- `probe search <PATTERN> [PATH] [OPTIONS]`: semantic discovery, ranked retrieval, token-bounded context, and quick file filtering.
- `probe symbols <FILES> [OPTIONS]`: file table-of-contents for functions, classes, constants, methods, and nesting.
- `probe extract <FILES> [OPTIONS]`: exact code-body pull by file, line, range, symbol, stdin, clipboard, or diff input.
- `probe query <PATTERN> [PATH] [OPTIONS]`: AST-pattern search for structurally repeated shapes.
- `probe lsp ...`: definitions, references, implementations, hover, call hierarchy, workspace symbols, and optional workspace indexing.

### Secondary commands

- `probe config ...`: inspect or validate effective Probe configuration when behavior looks surprising.
- `probe benchmark ...`: benchmark Probe itself with `--bench`, `--format`, `--compare`, `--baseline`, or `--fast` when diagnosing Probe performance. This is not part of normal repository investigation.

## Search Grammar and Result Control

- Use Boolean syntax such as `AND`, `OR`, `NOT`, parentheses, `+required`, `-excluded`, quoted phrases, and wildcards.
- Narrow with search hints such as `ext:rs`, `file:src/**/*.py`, `dir:tests`, `type:rust`, or `lang:typescript`.
- Use `--ignore`, `--no-gitignore`, and `--exclude-filenames` when the filesystem boundary needs explicit control.
- Use `--language` when file-extension inference is too broad.
- Control breadth with `--max-results`, `--max-bytes`, and `--max-tokens`.
- Control ranking with `--reranker`. Local help currently exposes `bm25`, `hybrid`, `hybrid2`, `tfidf`, and optional `ms-marco-*` rerankers.
- Smart token search is normally handled by `--frequency`; switch to `--exact` when you need literal matching rather than tokenization and stemming.
- Use `--question` only when BERT reranking is intentionally enabled and ranking quality is the problem.
- Use `--timeout` on large trees when you need a predictable upper bound.
- Use `--files-only` when you need candidate files first, then follow with `symbols` or `extract`.
- Use `--dry-run` when you want file paths plus coordinates without the full block bodies.
- Use machine-readable formats such as `json`, `xml`, `outline`, or `outline-xml` when the next step is programmatic.
- Use `--lsp` on `probe search` only when enriched symbol information is worth the extra cost.

## Extraction and Structural Tools

- Use `probe symbols <file>` before reading a long file. Prefer mapping first, then extracting the exact body.
- Use `probe extract <file>:<line>`, `<file>#<symbol>`, or `<file>:<start>-<end>` for exact code bodies.
- Use multiple extraction targets in one command when you already know the small set of relevant locations.
- Use `probe extract --context <n>` to keep a few surrounding lines when local scaffolding matters.
- Use `probe extract --keep-input` when feeding compiler output, stack traces, or grep results and you must preserve the original unstructured input.
- Use `probe extract --diff` when the input is a git diff rather than plain file references.
- Use `probe extract --from-clipboard` or `--input-file` only when the investigation input already exists in those forms.
- Use `probe extract --to-clipboard` or `--dry-run` only for deliberate operator workflows, not as the default Codex path.
- Use `probe extract --allow-tests` only when stdin, clipboard, or diff input should include test targets.
- Use `probe extract --lsp` and `--include-stdlib` only when call hierarchy or reference enrichment is actually required.
- `probe extract` also exposes LLM-facing `--prompt` and `--instructions` flags in some builds, but this skill intentionally does not use them.
- Use `probe query` when the target is structural rather than lexical: repeated handlers, constructors, async functions, route definitions, React components, or language-specific idioms.
- Use `probe query --language`, `--ignore`, `--allow-tests`, `--no-gitignore`, `--max-results`, and `--format` to keep AST queries scoped and reviewable.

## LSP and Indexing

- Prefer plain `search/symbols/extract/query` first. Escalate to `probe lsp` only when cross-file semantics matter.
- Use `probe lsp status`, `ping`, `languages`, `version`, `start`, `init`, and `doctor` to validate daemon health before deeper semantic calls.
- Use `probe lsp call definition`, `references`, `implementations`, `type-definition`, `hover`, `document-symbols`, `workspace-symbols`, `call-hierarchy`, and `fqn` for cross-file navigation.
- Use `probe lsp index`, `index-status`, `index-stop`, `index-config`, and `index-export` only when LSP-backed investigation needs workspace indexing.
- Use `probe lsp logs`, `crash-logs`, `connections`, `wal-sync`, `cache`, `restart`, or `shutdown` only for daemon debugging or recovery.
- Use `probe lsp enrich-symbol` or `edge-audit` only when you intentionally need persisted semantic enrichment or workspace graph auditing.
- Do not pay indexing or daemon-management overhead when a direct `search -> symbols/query -> extract` loop already answers the question.

## Investigation Workflow

### 1. Frame the search

- Translate the user request into 2-4 concrete search intents: domain terms, symbol names, error strings, execution paths, or file constraints.
- Start broad only once. After the first hit set, narrow aggressively.
- When a repo is large, include path hints early.

### 2. Run a broad `probe search`

- Use `probe search "<terms>" <path>` first.
- Add Boolean operators when the prompt includes multiple concepts.
- Add `--max-results`, `--max-bytes`, or `--max-tokens` to keep results reviewable.
- For code-only targeting, add file hints such as `ext:py`, `lang:typescript`, or `file:src/**/*.py`.

### 3. Switch to structure

- Use `probe symbols <file>` to map a file before reading large chunks.
- Use `probe query` for AST-pattern hunting such as async functions, React components, constructors, handlers, or framework-specific shapes.
- Use `probe extract <file>:<line>`, `<file>#<symbol>`, or ranges to pull only the exact body you need.

### 4. Escalate to semantics when needed

- If ownership or control flow remains unclear, use `probe lsp call definition`, `references`, `implementations`, or `call-hierarchy`.
- If semantic calls look stale or incomplete, inspect `probe lsp status` and index only if necessary.
- Keep LSP usage targeted. Do not turn every read into a daemon-management task.

### 5. Build the answer from evidence

- Cross-check claims against extracted code, not only ranked snippets.
- Cite the concrete symbol, file, or line-bearing extraction that supports the conclusion.
- If the user asked for deep analysis, repeat the search-structure-extract loop for adjacent callers, callees, validators, serializers, or parallel implementations.

### 6. Fallback cleanly

- If `probe` errors, note whether the problem is path noise, unsupported files, daemon state, or indexing.
- Retry with a narrower path or query once before switching tools.
- If you fall back, use the lightest alternative and preserve the same investigation goal.

## Task Recipes

### Unknown codebase or architecture

- Start with `probe search` on domain terms from the request.
- Use `probe symbols` on the top 2-3 files to map entry points.
- Use `probe extract` on likely orchestrators, interfaces, or handlers.
- Use `probe query` if the architecture depends on repeated patterns such as controllers, routes, jobs, or hooks.
- Use `probe lsp call definition` or `references` if ownership still looks ambiguous after extraction.

### Bug investigation or regression tracing

- Search for the error string, feature term, or failing symbol.
- Extract the nearest implementation body.
- Search again using related state names, exceptions, or helper calls found in the extracted code.
- Trace outward to callers and validators before proposing a fix.
- Use `probe lsp call references` or `call-hierarchy` when the bug depends on cross-file flow rather than local logic.

### Pre-edit code comprehension

- Before changing code, use `probe search` to find all likely implementations.
- Use `probe query` for structural variants of the same pattern.
- Use `probe extract` to inspect the exact body to edit and one neighboring usage site.
- Use `probe lsp call definition` or `implementations` if the edit touches interfaces, traits, or polymorphic call sites.

### Pattern inventory or refactor prep

- Use `probe query` first when the pattern is syntactic.
- Use `probe search` first when the pattern is semantic or named inconsistently.
- Combine the results into a small inventory before editing.

### Cross-file semantic tracing

- Start with `probe search` or `probe symbols` to find the candidate anchor.
- Use `probe lsp call definition`, `references`, `implementations`, `type-definition`, or `call-hierarchy` from that anchor.
- Extract the returned locations to inspect exact bodies rather than reasoning from symbol lists alone.
- Index the workspace only if semantic calls are missing, stale, or too shallow.

### Probe troubleshooting

- Use `probe config show` or `probe config validate` when behavior differs from expectation.
- Use `probe lsp doctor`, `status`, `logs`, and `crash-logs` when semantic navigation is broken.
- Use `probe benchmark` only when diagnosing Probe itself, not the target repository.

## References

- Read [CLI recipes](./references/cli-recipes.md) when you need ready-to-run `probe` command patterns.
- Read [LSP and indexing recipes](./references/lsp-and-indexing-recipes.md) when `definition`, `references`, `call-hierarchy`, or workspace indexing are needed.
- Read [Investigation playbook](./references/investigation-playbook.md) when the request is broad and you need a repeatable deep-search sequence.

## Output Expectations

- Summarize the search path you took: broad query, structural follow-ups, semantic follow-ups, and the extracted evidence.
- Keep raw command output out of the final user-facing summary unless it is specifically requested.
- When a result is still tentative, say what additional `probe` pass would confirm it.
- If LSP or indexing state materially affected confidence, say so explicitly.
