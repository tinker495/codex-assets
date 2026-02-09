# Xenon Triage Playbook

Use this playbook when `xenon` fails on complexity thresholds.

## Goal

Reach:
- block threshold pass (for example `--max-absolute B`)
- module threshold pass (for example `--max-modules A`)
- average threshold pass (for example `--max-average A`)

## Commands

```bash
uv run radon cc src -s -n C
uv run xenon --max-absolute B --max-modules A --max-average A src
```

## Phase 1: Block-First

1. Collect all C/D block offenders from `radon` and `xenon`.
2. Refactor only those functions/methods first:
   - extract guard clauses
   - split branch-heavy loops into helpers
   - move formatting/detail branches out of main path
3. Re-run both commands after each bounded batch.
4. Continue until block offenders are zero.

## Phase 2: Module-Second

1. Re-check `xenon` for module-rank failures (`module has rank B`).
2. In each module, lower average complexity by flattening medium blocks:
   - simplify B-ranked helpers that are high churn
   - remove duplicate conditional patterns
   - keep behavior identical and avoid new abstraction layers unless reused
3. Re-run both commands until module rank passes.

## Guardrails

- Do not claim pass without command output.
- Avoid wrapper-only refactors that increase non-test LOC.
- Prefer deletion-first simplification before adding helpers.
