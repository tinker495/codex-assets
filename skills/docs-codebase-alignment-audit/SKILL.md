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

3. Run three baseline checks
- Code/test path existence:
```bash
scripts/check_code_paths.sh <repo_root> <docs_root>
```
- Make target existence:
```bash
scripts/check_make_targets.sh <repo_root> <docs_root>
```
- Markdown relative links:
```bash
python3 scripts/check_md_links.py <docs_root>
```

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
- Write transient reports/lists to `/private/tmp` by default (for example, `/private/tmp/docs-alignment-*.md`).
- Report exact files changed and unresolved items (if any).

## Guardrails

- Do not add dependencies.
- Do not modify binaries (`.png`, `.pdf`) for alignment-only work.
- Do not rewrite large To-Be specs just to force current-code parity.
- Keep diffs narrow and reviewable.
- Keep intermediate artifacts out of the repository. Use `/private/tmp` unless the user explicitly requests a repo file.

## References

- Scope policy and boundary rules: `references/scope_and_boundary.md`
