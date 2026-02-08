# Session Wrap-Up Checklist

## Quick Gate

1. Confirm the session has a clear end boundary.
2. Confirm at least one reusable insight exists.
3. Confirm ownership can be assigned without overlap.

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

## Topology Change Gate

Update topology only when one of these changed:
- role classification
- new delegation edge
- removed delegation edge
- ownership transfer between skills

If none changed, record: `no topology change`.
