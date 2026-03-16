# Session Wrap-Up Checklist

## Quick Gate

1. Confirm the session has a clear end boundary.
2. Confirm at least one reusable insight exists.
3. Confirm ownership can be assigned without overlap.
4. If any action retires/removes skill assets, require `mirror` sync mode.
5. If TODO or deferred-follow-up visibility matters, collect TODO status before synthesis.
6. If no reusable insight survives review, mark the wrap-up as `no-op` and stop after reporting.

## Evidence Priority

Use evidence in this order:
1. Current task summary and delivered result.
2. Changed files, command traces, validations, and failure/retry notes.
3. User corrections or repeated steering.
4. Local session artifacts such as `.omx/notepad.md` or saved reports.
5. TODO inventory evidence (`todo-inventory` output, inline `TODO:` markers, or explicit deferred follow-up notes).

Do not reference a non-installed recall skill to fill evidence gaps.

## Insight Extraction Grid

| Insight | Evidence | Reuse Likelihood | Action Type |
| --- | --- | --- | --- |
| Trigger mismatch | repeated prompt correction | high | update-existing-skill |
| Missing sequence guardrail | repeated manual workaround | high | update-existing-skill |
| New repeated workflow | appears in multiple tasks | high | create-new-skill |
| One-off failure | isolated environment issue | low | none |

Default bias:
- prefer `update-existing-skill`
- use `create-new-skill` only when no installed owner is a clean fit

## Handoff Packet to skill-creator

Provide:
- `name`: English hyphen-case.
- `target_path`: `$CODEX_HOME/skills/<skill-name>`.
- `action`: `update-existing-skill`, `create-new-skill`, `retire-skill`, or `none`.
- `description`: what + when-to-use trigger.
- `description_delta`: new trigger, removed trigger, or ownership correction.
- `role`: specialist/orchestrator/utility/meta.
- `ownership`: what this skill owns.
- `delegation`: one-hop edges only.
- `resources`: scripts/references/assets needs.
- `interface`: whether `agents/openai.yaml` needs refresh.
- `validation`: quick_validate + topology consistency when role/edges changed.
- `todo_status`: new TODOs added, remaining scoped TODOs, and follow-up items reported without inline TODOs.

If sub-agent execution is part of the proposed workflow, include:
- `sub-agent invocation`: `--prompt-file` + `--timeout-sec` standard.
- `output path policy`: avoid `/tmp`/`/var/tmp`; prefer workspace or `~/.codex/sub_agent_runs`.

## Topology Change Gate

Update topology only when one of these changed:
- role classification
- new delegation edge
- removed delegation edge
- ownership transfer between skills

If none changed, record: `no topology change`.
Never keep delegation notes that point to non-installed skills.

## TODO Status Gate

When wrap-up output mentions deferred follow-up work:
1. Prefer concrete TODO evidence from `todo-inventory` over memory or guesswork.
2. Distinguish current TODO inventory from TODOs newly added in the current diff.
3. If work was deferred without an inline TODO comment, label it explicitly as `reported-without-inline-TODO`.
4. If diff status is unavailable, say so instead of implying zero new TODOs.

## Retirement and Sync Mode Gate

When an action includes skill retirement, rename, or removal:

1. Move retired skill out of active root first:
   - `~/.codex/skills/<skill-name>` -> `~/.codex/archived-skills/<skill-name>`
2. Require mirror sync for deletion reflection:
   - `cd <mirror-repo> && ./scripts/sync_and_push.sh --mirror --repo <owner/name>`
3. Use default merge sync only for additive/non-deleting changes.

## Sub-Agent Stability Gate

1. If `codex-exec-sub-agent` is involved, verify quoting-safe call examples use `--prompt-file`.
2. Require bounded execution (`--timeout-sec`) for long-running or uncertain scans.
3. Ensure failure handling keeps JSONL run path discoverable for postmortem.
