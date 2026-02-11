---
name: docs-codebase-alignment-audit
description: Audit and fix documentation alignment against the current repository codebase with minimal diffs. Use when users ask to sync `docs/` with real code paths, verify Markdown links, validate `make` commands in docs, or run end-to-end docs consistency checks.
---

# Docs Codebase Alignment Audit

## Overview

Run deterministic docs-to-codebase alignment checks and apply minimal, evidence-based fixes.
Keep As-Is runtime docs aligned to code, and avoid forcing To-Be spec docs to match current implementation when they explicitly declare design-target status.

## Workflow

1. Inventory scope
- Default target is tracked docs: `git ls-files docs`
- Limit edits to files explicitly in scope.

2. Detect document type boundary
- Treat files under `docs/full-plan/` as potential To-Be design docs.
- Before editing those files, confirm they already contain As-Is/To-Be boundary statements.
- If boundary statements exist, prefer clarifying language over implementation-forcing edits.

3. Run three baseline checks (path-guarded)
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

4. Classify findings
- `fix-now`: broken path, missing make target, broken relative link, stale direct code reference.
- `keep-with-note`: intentional To-Be mismatch with explicit boundary text.
- `ignore`: examples/placeholders that are explicitly marked as template syntax.

5. Apply minimal fixes
- Prefer path normalization over paragraph rewrites.
- Replace non-existent file references with existing canonical paths.
- Preserve document intent and section structure.

6. Re-run checks and report
- Re-run all three baseline checks.
- Before writing transient reports, verify destination: `test -w /private/tmp`.
- If not writable, fallback to a writable repo-root temp dir (for example, `<repo_root>/.codex_tmp`) or `$CODEX_HOME`, and report the fallback.
- Report exact files changed and unresolved items (if any).

## Guardrails

- Do not add dependencies.
- Do not modify binaries (`.png`, `.pdf`) for alignment-only work.
- Do not rewrite large To-Be specs just to force current-code parity.
- Keep diffs narrow and reviewable.
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

- Scope policy and boundary rules: `references/scope_and_boundary.md`
