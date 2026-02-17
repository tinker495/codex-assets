---
name: docs-codebase-alignment-audit
description: Run deterministic docs integrity audits and minimal repairs for repository Markdown docs. Use when users ask to check/fix broken links, stale paths, missing make targets, AGENTS chain references, docs-check/CI guardrails, or map-first/SSOT/progressive-disclosure conformance. Prefer this for audit-and-fix passes, not full branch-wide narrative refresh.
---

# Docs Codebase Alignment Audit

## Mission

Run deterministic docs alignment checks and apply minimal, evidence-based fixes.
Keep As-Is runtime docs aligned to code. Keep To-Be docs intentionally future-facing when boundary text is explicit.

## Operational Noise Guardrails
- Before direct file access (`sed`/`cat`/`rg` on explicit paths), run `test -f` or `rg --files -g` preflight.
- For script/shared paths, run `test -f`/`test -d` first; if missing, report once and fallback to `git log --since=1.week --name-only` plus `git diff --stat`.
- Keep command retry budget strict: one retry max for identical failures, then fallback.
- Before git-based fallback, verify repo context with `git rev-parse --is-inside-work-tree`.

## Harness Principles (must enforce)

1. Map-first AGENTS
- Treat root `AGENTS.md` as a table of contents, not an encyclopedia.
- Keep detailed guidance in `docs/` and local `src/**/AGENTS.md`.

2. Repository knowledge as SSOT
- Prefer repository-local, versioned docs (`docs/`, `AGENTS.md`, `src/**/AGENTS.md`) over external context.
- Keep As-Is/To-Be boundaries explicit and auditable.

3. Progressive disclosure
- Ensure a stable top-level map (`AGENTS.md` -> `docs/index.md`) and layered navigation (`guides/`, `reference/`, `specs/`).

4. Mechanical enforcement
- Validate path/link/target integrity with scripts and CI, not manual spot checks.

5. Continuous doc-gardening
- Classify stale docs and produce focused cleanup diffs instead of broad rewrites.

## Workflow

1. Inventory scope
- Default target is tracked docs: `git ls-files docs`
- Limit edits to files explicitly in scope.

2. Read repository map and contracts first
- Prioritize: `AGENTS.md`, `docs/index.md`, `docs/_meta/docs-contract.md`, then local `src/**/AGENTS.md`.
- Detect progressive-disclosure breaks (missing index links, missing layer entrypoints).

3. Detect document type boundary
- Treat files under `docs/specs/` (and legacy `docs/full-plan/`) as potential To-Be design docs.
- Before editing those files, confirm they contain As-Is/To-Be boundary statements.
- If boundary statements exist, prefer clarifying language over implementation-forcing edits.

4. Run three baseline checks (path-guarded)
- Code/test path existence:
  - Preflight: `test -f scripts/check_code_paths.sh`.
  - If missing, search: `rg --files -g "check_code_paths.sh"` and run the first exact match.
  - If still missing, skip with note and continue.
  - Run: `scripts/check_code_paths.sh <repo_root> <docs_root>`
- Make target existence:
  - Preflight: `test -f scripts/check_make_targets.sh`.
  - If missing, search: `rg --files -g "check_make_targets.sh"` and run the first exact match.
  - If still missing, skip with note and continue.
  - Run: `scripts/check_make_targets.sh <repo_root> <docs_root>`
- Markdown relative links:
  - Preflight: `test -f scripts/check_md_links.py`.
  - If missing, search: `rg --files -g "check_md_links.py"` and run the first exact match.
  - If still missing, skip with note and continue.
  - Run: `python3 scripts/check_md_links.py <docs_root>`

5. Verify AGENTS reference chain (when AGENTS files exist)
- Detect local AGENTS: `find src -type f -name AGENTS.md | sort`.
- Check hub/index references:
  - root `AGENTS.md` should reference key local AGENTS entry points.
  - `docs/index.md` Local AGENTS section should include discovered local AGENTS paths.
- Check parent-child references:
  - parent AGENTS files (for example `src/stowage/AGENTS.md`) should list direct child-context AGENTS where applicable.
- Classify missing AGENTS references as `fix-now` unless the doc explicitly states a temporary exception.

6. Verify harness mechanical guards
- Check `Makefile` for `docs-check` (or equivalent) target.
- Check CI (for example `.github/workflows/`) for docs integrity execution.
- If missing, classify as `fix-now` unless user scope excludes tooling updates.

7. Classify findings
- `fix-now`: broken path, missing make target, broken relative link, stale direct code reference.
- `fix-now`: missing AGENTS chain reference (index or parent-child), missing docs mechanical guard.
- `keep-with-note`: intentional To-Be mismatch with explicit boundary text.
- `ignore`: examples/placeholders that are explicitly marked as template syntax.
- `doc-gardening`: stale but non-blocking drift candidates safe for follow-up PR.

8. Apply minimal fixes
- Prefer path normalization over paragraph rewrites.
- Replace non-existent file references with existing canonical paths.
- Preserve document intent and section structure.
- For AGENTS chain fixes, update reference lists first; avoid rewriting policy paragraphs.

9. Re-run checks and report
- Re-run all three baseline checks.
- If AGENTS chain checks were in scope, re-run the chain checklist before reporting.
- Before writing transient reports, verify destination: `test -w /private/tmp`.
- If not writable, fallback to a writable repo-root temp dir (for example, `<repo_root>/.codex_tmp`) or `$CODEX_HOME`, and report the fallback.
- Report exact files changed, unresolved items, and harness-conformance status:
  - map-first AGENTS
  - docs SSOT contract
  - progressive disclosure links
  - mechanical guard presence
  - AGENTS chain integrity

## Guardrails

- Do not add dependencies.
- Do not modify binaries (`.png`, `.pdf`) for alignment-only work.
- Do not rewrite large To-Be specs just to force current-code parity.
- Keep diffs narrow and reviewable.
- Keep AGENTS concise and map-oriented; push detail into linked docs.
- Keep intermediate artifacts out of the repository. Use `/private/tmp` unless the user explicitly requests a repo file.
- Avoid here-doc syntax; use `python -c` or single-line commands for inline scripts.

## Operational Noise Controls
- Use search-as-discovery: run the bundled scripts first, then `rg` only if a script path is missing.
- Apply path filtering: scope `rg` to `docs/` or the script directory before broader searches.
- Use trace-plus-rg evidence gating: require a concrete failing path before any wide scan.
- Before git fallback commands, verify repo context: `git rev-parse --is-inside-work-tree`.
- If path-check scripts are all missing, continue with git evidence fallback: `git log --since=1.week --name-only` and `git diff --stat`.
- Avoid fallback loops: one fallback per missing script, then continue.

## References

- Shared harness checklist: `../_shared/references/docs_harness_checklist.md`
- Scope policy and boundary rules: `references/scope_and_boundary.md`
- AGENTS chain checklist: `references/agents_chain.md`
