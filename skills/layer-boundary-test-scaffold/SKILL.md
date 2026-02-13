---
name: layer-boundary-test-scaffold
description: Scaffold or extend AST-based architecture boundary tests from AGENTS.md rules (import boundaries, layer dependencies, runtime-only UI constraints). Use when converting textual architecture constraints into pytest-enforced checks.
---

# Layer Boundary Test Scaffold

## Overview

Convert architecture rules written in `AGENTS.md` or docs into deterministic `pytest` checks.
Focus on minimal, AST-based boundary tests that fail with actionable file/line evidence.

## When to Use

Use this skill when:
- a repository has textual architecture rules that are not mechanically enforced,
- a review requests layer-boundary regression tests,
- import/ownership constraints need CI enforcement.

## Workflow

1. Collect rule source
- Read boundary rules from `AGENTS.md`, `src/**/AGENTS.md`, and architecture docs.
- Extract only concrete, testable rules (for example: "planner must not import tui").

2. Normalize into rule tuples
- Convert each rule into `(scope, prohibited_pattern, allowed_exceptions)`.
- Keep one tuple per test to preserve clear failure output.

3. Place tests in architecture suite
- Prefer extending existing `tests/architecture/test_layer_boundaries.py`.
- If absent, create `tests/architecture/` with `__init__.py` and a single boundary test file.

4. Implement AST-based detectors
- Use `ast.Import` and `ast.ImportFrom` for import boundaries.
- Use parent-map checks for `TYPE_CHECKING` exceptions when rules are runtime-only.
- Emit violations as `path:line + reason` entries.

5. Write explicit tests
- Create one test per rule family.
- Keep assertion messages deterministic and rule-specific.
- Avoid coupling unrelated rules in one assertion.

6. Verify
- Run `ruff check` on changed test files.
- Run targeted `pytest` for `tests/architecture`.
- Re-run project docs/quality command only when relevant.

7. Report coverage boundaries
- State which textual rules are now mechanically enforced.
- State deferred rules and why they were not encoded yet.

## Guardrails

- Prefer AST parsing over regex for Python import rules.
- Do not introduce broad token bans that create false positives outside target scope.
- Scope filesystem traversal to relevant directories only.
- Treat runtime constraints and type-checking constraints separately.
- Keep test names generic (`test_layer_boundaries.py`) for future rule growth.

## Output Contract

Return:
1. Added/updated boundary rules list.
2. Files changed.
3. Verification commands and outcomes.
4. Remaining non-mechanized rules (if any).

## References

- AST boundary test snippets: `references/boundary_patterns.md`
