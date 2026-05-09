---
name: ultragoal
description: "[OMX] Create and execute durable repo-native multi-goal plans over Codex goal mode artifacts."
---

# Ultragoal Workflow

Use when the user asks for `ultragoal`, `create-goals`, `complete-goals`, durable multi-goal planning, or sequential execution over Codex `/goal`.

## Purpose

`ultragoal` turns a brief into repo-native artifacts and then drives a Codex goal safely through goal tools. New plans default to an aggregate Codex goal for the whole ultragoal run while OMX tracks G001/G002 story progress in the ledger.

- `.omx/ultragoal/brief.md`
- `.omx/ultragoal/goals.json`
- `.omx/ultragoal/ledger.jsonl`

## Create goals

1. Run one of:
   - `omx ultragoal create-goals --brief "<brief>"`
   - `omx ultragoal create-goals --brief-file <path>`
   - `cat <brief> | omx ultragoal create-goals --from-stdin`
   - `omx ultragoal create-goals --codex-goal-mode per-story --brief "<brief>"` only when one fresh Codex thread per story is explicitly preferred
2. Inspect `.omx/ultragoal/goals.json` and refine if needed.

## Complete goals

Loop until `omx ultragoal status` reports all goals complete:

1. Run `omx ultragoal complete-goals`.
2. Read the printed handoff.
3. Call `get_goal`.
4. If no active Codex goal exists, call `create_goal` with the printed payload. In aggregate mode, if the same aggregate Codex objective is already active, continue the current OMX story without creating a new Codex goal.
5. Complete the current OMX story only.
6. Run a completion audit against the story objective and real artifacts/tests.
7. In aggregate mode, do **not** call `update_goal` for intermediate stories; checkpoint with a fresh `get_goal` snapshot whose aggregate objective is still `active`. On the final story only, call `update_goal({status: "complete"})`, then call `get_goal` again for a fresh `complete` snapshot.
8. Checkpoint the durable ledger with that snapshot:
   `omx ultragoal checkpoint --goal-id <id> --status complete --evidence "<evidence>" --codex-goal-json <get_goal-json-or-path>`
9. If blocked or failed, checkpoint failure:
   `omx ultragoal checkpoint --goal-id <id> --status failed --evidence "<blocker/evidence>"`
10. For legacy per-story completed-goal blockers, preserve the non-terminal blocker with:
   `omx ultragoal checkpoint --goal-id <id> --status blocked --evidence "<completed legacy Codex goal blocks create_goal in this thread>" --codex-goal-json <get_goal-json-or-path>`
11. Resume failed goals with `omx ultragoal complete-goals --retry-failed`.

## Constraints

- The shell command cannot directly invoke Codex interactive `/goal`; it emits a model-facing handoff for the active Codex agent.
- Never call `create_goal` when `get_goal` reports a different active goal.
- Never call `update_goal` unless the aggregate run or legacy per-story goal is actually complete.
- In aggregate mode, intermediate story checkpoints require a matching `active` Codex snapshot; final story completion requires a matching `complete` snapshot after `update_goal`.
- Completion checkpoints require read-only Codex snapshot reconciliation: pass fresh `get_goal` JSON/path with `--codex-goal-json`; shell commands and hooks must not mutate Codex goal state.
- Treat `ledger.jsonl` as the durable audit trail; checkpoint after every success or failure.
