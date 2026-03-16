# Session Wrap-Up Checklist

## Quick Gate

1. Confirm the session has a clear end boundary.
2. Confirm at least one reusable insight exists.
3. Confirm ownership can be assigned without overlap.
4. If any action retires/removes skill assets, require `mirror` sync mode.
5. If no reusable insight survives review, mark the wrap-up as `no-op` and stop after reporting.

## Evidence Priority

Use evidence in this order:
1. Current task summary and delivered result.
2. Changed files, command traces, validations, and failure/retry notes.
3. User corrections or repeated steering.
4. Local session artifacts such as `.omx/notepad.md` or saved reports.

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
