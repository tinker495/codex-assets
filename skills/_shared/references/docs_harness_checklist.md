# Docs Harness Checklist (Shared)

Use this checklist for documentation operations across skills.

## 1) Map-first AGENTS

Goal:
- Keep root `AGENTS.md` as a navigation map.

Checks:
- `AGENTS.md` links to `docs/index.md`.
- `AGENTS.md` links to active local `src/**/AGENTS.md` entrypoints.
- Deep policy stays in linked leaf docs, not duplicated at root.

## 2) Repository SSOT boundaries

Goal:
- Keep As-Is and To-Be scopes explicit and auditable.

Checks:
- As-Is sources are explicit (`src/`, `tests/`, `README.md`, `AGENTS.md`, local AGENTS).
- To-Be sources are explicit (`docs/specs/**` or declared legacy equivalents).
- `docs/_meta/docs-contract.md` (or equivalent) is present and current.

## 3) Progressive disclosure continuity

Goal:
- Preserve stable top-down reading flow.

Checks:
- `AGENTS.md` -> `docs/index.md` path exists.
- `docs/index.md` exposes `guides/`, `reference/`, and `specs/`.
- Local AGENTS inventory in docs matches discovered `src/**/AGENTS.md`.

## 4) Mechanical enforcement

Goal:
- Enforce docs integrity with scripts and CI.

Checks:
- `make docs-check` (or equivalent) exists.
- CI executes docs integrity checks.
- Path, make-target, and markdown-link checks are wired and passing.

## 5) Doc-gardening split

Goal:
- Keep review focused by separating blockers from cleanup.

Classification:
- `fix-now`: broken links/paths/targets, boundary regression, missing guardrails.
- `doc-gardening`: stale wording/structure that is non-blocking.

Reporting:
- Always report `fix-now` and `doc-gardening` separately.

## 6) Metric SSOT and baseline wording

Goal:
- State evaluation/performance metrics from code-defined SSOT with an explicit comparison baseline.

Guidance:
- Do: verify the evaluator's current metrics from code, name the SSOT positively (for example `performance SSOT is X + Y`), and spell out the comparison baseline pair (`after_discharge -> rebuilt_plan`, `after_load vs rebuilt`).
- Don't Do: describe internal heuristic counters as performance SSOT when they are not evaluator outputs, or use ambiguous wording like `also sees anomaly_counts` without saying what is actually compared.

## 7) Deletion-first refresh wording

Goal:
- Keep refreshed docs aligned to the current scope without tombstone prose.

Guidance:
- Do: when a statement is no longer current or in scope, delete it outright and rewrite the surrounding doc so the stale content no longer exists.
- Don't Do: leave wording like "this was removed/deleted" unless the document is explicitly a changelog, migration guide, or retirement record.
