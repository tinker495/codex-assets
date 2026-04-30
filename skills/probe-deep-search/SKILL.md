---
name: probe-deep-search
description: Probe-first, CLI-only deep codebase investigation using local `probe` commands directly. Use when Codex or a delegated subagent needs to understand an unfamiliar repository, trace cross-file behavior, locate implementations before editing, audit architecture, investigate bugs, or perform deep search where `probe search`, `probe symbols`, `probe query`, `probe extract`, and `probe lsp` should be prioritized over plain-text tools such as `rg` or `grep`.
---

# Probe Deep Search

Use the Probe CLI as the primary read surface for code and doc investigation. Codex remains the reasoner: Probe supplies retrieval, structure, and navigation evidence only.

Keep the workflow evidence-driven: broaden with `probe search`, narrow with `symbols` or `query`, then extract only the exact code bodies needed. Do not drift into `rg`-only exploration while Probe can still answer the question.

## Non-Negotiables

- Prefer `probe <subcommand> ...` directly. If the binary is unavailable, fall back to `npx -y @probelabs/probe@latest <subcommand> ...`.
- Do not use `probe agent`, `npx -y @probelabs/probe@latest agent`, `probe-chat`, MCP server mode, Node SDK integration, or LLM Script from this skill.
- Do not use `probe extract --prompt ...` or `--instructions ...` here. Let Codex interpret Probe output itself.
- Start each investigation with at least one `probe` subcommand before falling back to plain-text tools.
- Treat the installed `probe ... --help` output as the source of truth for flags and defaults.
- Fall back to `rg`, `grep`, or direct file reads only when Probe is unavailable, broken, or structurally incapable of answering the question.
- State when you are falling back and why.

## Command Surface

- `probe search <PATTERN> [PATH] [OPTIONS]`: ranked discovery and candidate file filtering.
- `probe symbols <FILES> [OPTIONS]`: table-of-contents for functions, classes, constants, methods, and nesting.
- `probe extract <FILES> [OPTIONS]`: exact body extraction by file, line, range, symbol, stdin, clipboard, or diff input.
- `probe query <PATTERN> [PATH] [OPTIONS]`: AST-pattern search for structural repetition.
- `probe lsp ...`: definitions, references, implementations, hover, call hierarchy, workspace symbols, and optional indexing.
- `probe config ...`: inspect effective Probe configuration when behavior looks surprising.
- `probe benchmark ...`: diagnose Probe performance only, not normal repository behavior.

Use Boolean search terms and hints such as `ext:`, `file:`, `dir:`, `type:`, and `lang:` to reduce noise early. Limit payloads with `--max-results`, `--max-bytes`, or `--max-tokens`. Use `--files-only` or `--dry-run` to get anchors before extracting bodies. Treat `--allow-tests` as opt-in unless the task is explicitly about tests.

## Investigation Workflow

1. Frame 2-4 search intents from the request: domain terms, symbol names, error strings, execution paths, or path constraints.
2. Run one broad `probe search "<terms>" <path>` pass. Add Boolean operators and path hints when the prompt includes multiple concepts.
3. Switch to structure before concluding. Use `probe symbols <file>`, `probe query`, or `probe extract <file>:<line|range>` / `<file>#<symbol>` on the best anchors.
4. Escalate to `probe lsp call definition`, `references`, `implementations`, or `call-hierarchy` only when cross-file ownership or control flow remains unclear.
5. Cross-check claims against extracted code, not ranked snippets alone.
6. If Probe errors, retry once with a narrower path or query before falling back.

For deep analysis, repeat the `search -> symbols/query -> extract` loop for adjacent callers, callees, validators, serializers, or parallel implementations.

## Native Subagent Handoff

When a parent task uses native subagents for independent repository investigation, make the handoff skill-explicit. Native child contexts may not inherit this loaded body, so pass either `$probe-deep-search` or the absolute path to this `SKILL.md`.

Use this prompt shape:

```text
Use $probe-deep-search at <absolute-path-to-probe-deep-search/SKILL.md> for a read-only investigation of: <bounded scope>.
Start by reading that skill, state "Using skill: probe-deep-search", run a probe-first search -> structure -> extract pass, and return commands run, extracted evidence, confidence, and open questions.
Do not edit files. Do not make review severity or remediation decisions unless explicitly asked.
```

Parent skills keep domain ownership. This skill owns the Probe retrieval loop; the caller owns review severity, remediation decisions, rewrite policy, documentation synthesis, and final integration.

Good subagent tasks are bounded by file set, feature area, error string, symbol family, or one cross-file relationship. Avoid using subagents for a single obvious `probe search`.

## Task Recipes

- Unknown codebase: search domain terms, map the top files with `symbols`, then extract likely orchestrators or interfaces.
- Bug tracing: search the error string or failing symbol, extract the nearest body, then search outward using state names, helpers, exceptions, or validators found in that body.
- Pre-edit comprehension: find all likely implementations, inspect the exact body to edit, and inspect one neighboring caller or usage site.
- Pattern inventory: use `probe query` when the pattern is syntactic; use `probe search` when names are inconsistent.
- Cross-file semantics: locate an anchor first, call the targeted LSP method, then extract returned locations before reasoning.
- Probe troubleshooting: use `probe config show` or `validate` for surprising configuration and `probe lsp status` or `doctor` for semantic navigation failures.

## References

- Read [CLI recipes](./references/cli-recipes.md) when you need ready-to-run command patterns or option inventories.
- Read [LSP and indexing recipes](./references/lsp-and-indexing-recipes.md) when `definition`, `references`, `call-hierarchy`, or workspace indexing is needed.
- Read [Investigation playbook](./references/investigation-playbook.md) when the request is broad and you need a repeatable deep-search sequence.

## Output Expectations

- Summarize the search path you took: broad query, structural follow-ups, semantic follow-ups, and the extracted evidence.
- Keep raw command output out of the final user-facing summary unless it is specifically requested.
- For subagent work, include the skill declaration, command list, evidence, confidence, and open questions.
- When a result is still tentative, say what additional `probe` pass would confirm it.
- If LSP or indexing state materially affected confidence, say so explicitly.
