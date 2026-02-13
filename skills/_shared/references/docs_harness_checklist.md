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
