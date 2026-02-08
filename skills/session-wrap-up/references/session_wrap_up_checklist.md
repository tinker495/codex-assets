# Session Wrap-Up Checklist

## Quick Gate

1. Confirm the session has a clear end boundary.
2. Confirm at least one reusable insight exists.
3. Confirm ownership can be assigned without overlap.
4. If any action retires/removes skill assets, require `mirror` sync mode.

## Insight Extraction Grid

| Insight | Evidence | Reuse Likelihood | Action Type |
| --- | --- | --- | --- |
| Trigger mismatch | repeated prompt correction | high | update-existing-skill |
| Missing sequence guardrail | repeated manual workaround | high | update-existing-skill |
| New repeated workflow | appears in multiple tasks | high | create-new-skill |
| One-off failure | isolated environment issue | low | none |

## Handoff Packet to skill-creator

Provide:
- `name`: English hyphen-case.
- `description`: what + when-to-use trigger.
- `role`: specialist/orchestrator/utility/meta.
- `ownership`: what this skill owns.
- `delegation`: one-hop edges only.
- `resources`: scripts/references/assets needs.
- `validation`: quick_validate + topology consistency.

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
