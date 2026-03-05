---
name: omx-workspace-prune
description: Safely tidy `.omx` workspace state between sessions with deterministic dry-run/apply modes. Preserves current session by default, rotates old logs/sessions, and archives non-active plans while honoring `ACTIVE.md`.
---

# OMX Workspace Prune

## Purpose

Safely prune stale `.omx` state so future sessions start with a clean workspace while preserving active context.

## Modes

- Dry-run (default): show planned actions only.
- Apply: execute the planned actions.

## Safety Contract

- Keep current session by default.
- Preserve `.omx/plans/ACTIVE.md` always.
- Keep plans referenced by `ACTIVE.md` and latest `prd-*.md` / `test-spec-*.md`.
- Move other root-level `.omx/plans/*.md` files into `.omx/plans/archive/` (never hard-delete plans).
- Remove only stale session state directories and old logs.

## Commands

From a repository root containing `.omx/`:

```bash
python ~/.codex/skills/omx-workspace-prune/scripts/prune_workspace.py --workspace-root "$PWD"
python ~/.codex/skills/omx-workspace-prune/scripts/prune_workspace.py --workspace-root "$PWD" --apply
```

Optional controls:

```bash
python ~/.codex/skills/omx-workspace-prune/scripts/prune_workspace.py --workspace-root "$PWD" --apply --keep-session omx-1772708501520-nj0zyv
python ~/.codex/skills/omx-workspace-prune/scripts/prune_workspace.py --workspace-root "$PWD" --apply --log-retention-days 3
```

## What gets pruned

1. `.omx/state/sessions/*` and legacy `.omx/state/omx-*` directories except kept session.
2. `.omx/logs/*.jsonl` older than retention window.
3. Root-level markdown plans in `.omx/plans/` that are not protected by ACTIVE contract or latest plan guards.

## Output Contract

- Print deterministic action lines prefixed with `KEEP`, `DELETE`, `ARCHIVE`, or `SKIP`.
- In dry-run, print `Mode: dry-run (no filesystem changes)`.
- In apply, print `Mode: apply` and the same action list as executed.
- If no `.omx` directory exists, fail fast with a clear error.

## Notes

- Prefer this utility before long new sessions or after heavy multi-agent runs.
- Do not run with `--apply` during an active session unless you explicitly pin `--keep-session`.
