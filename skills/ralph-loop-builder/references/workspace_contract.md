# Ralph Workspace Contract

## Goal

Create a repeatable `.codex/<workspace>` loop scaffold that can be executed immediately with `./ralph.sh`.

## Required Files

- `README.md`
- `CODEX.md`
- `prd.json`
- `progress.txt`
- `ralph.sh`
- `audit/` directory

## Mode Matrix

| Mode | Intent | Story Prefix | Mutation Policy |
| --- | --- | --- | --- |
| `audit` | Evidence-first analysis loops | `AUDIT-*` | read-only recommendation |
| `delivery` | one-story implementation loops | `US-*` | implementation allowed by story scope |

## Base-Ref Rule

Every generated workspace must carry one explicit base reference (`origin/main` default) and must use it in diff summary commands.

## Story Initialization Rule

- Initialize all stories with `passes: false`.
- Keep `priority` monotonic from `1..N`.
- Keep `acceptanceCriteria` concrete and artifact-based.

## Runner Rule

- Prefer copying `ralph.sh` from an existing template workspace.
- If template runner is missing, generate a safe failing stub and stop with a clear recovery instruction.
