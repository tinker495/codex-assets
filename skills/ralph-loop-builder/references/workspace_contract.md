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
| `audit` | Evidence-first analysis loops | `AUDIT-*` | read-only default (`--allow-write` can override) |
| `delivery` | one-story implementation loops | `US-*` | read-write default (`--read-only` can override) |

## Mutation Policy Rule

- Persist explicit mutation policy under `prd.json.workspaceSettings.readOnly`.
- Prefix every story note with the active mutation policy.
- Generated `CODEX.md` must repeat the same policy to prevent execution ambiguity.
- In `audit` mode, `CODEX.md` must also include explicit no-fix/no-plan language.

## Strict Audit Instruction Rule

When `mode=audit`, generated `CODEX.md` must include all of:
- `Safety Notice`
- `Web Research Policy`
- `Critical Rules` with `DO NOT FIX ANYTHING`
- `Output Format` with required finding fields (`severity`, `file`, `lines`, `category`, `code`, `impact`)
- stop condition for one-task-per-iteration output

And generated `prd.json` audit stories must enforce:
- exhaustive scope read requirement (no skipped files in story scope)
- finding-level evidence requirement (line numbers + code snippets)
- explicit ban on fix proposals

## Model Routing Rule

- Persist workspace model defaults under `prd.json.workspaceSettings.modelPolicy`.
- Default review profile:
  - model: `gpt-5.2`
  - reasoning effort: `xhigh`
- Default fix profile:
  - model: `gpt-5.3-codex`
  - reasoning effort: `high`
- Every story must include `modelProfile`.
- Story-level overrides are allowed via `--story-model-overrides` and must target valid story IDs only.

## Base-Ref Rule

Every generated workspace must carry one explicit base reference (`origin/main` default) and must use it in diff summary commands.

## Story Initialization Rule

- Initialize all stories with `passes: false`.
- Keep `priority` monotonic from `1..N`.
- Keep `acceptanceCriteria` concrete and artifact-based.

## Runner Rule

- Prefer copying `ralph.sh` from an existing template workspace, then normalize it to a mode-agnostic runner.
- Runner must resolve sandbox mode from `prd.json.workspaceSettings.readOnly` (`read-only` vs `workspace-write`) at runtime.
- Runner model defaults must be read from `prd.json.workspaceSettings.modelPolicy.defaultProfile`.
- If template runner is missing, generate a safe failing stub and stop with a clear recovery instruction.
