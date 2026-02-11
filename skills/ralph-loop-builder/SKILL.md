---
name: ralph-loop-builder
description: Use when a user wants a new purpose-specific Ralph workspace under `.codex/` (for example `.codex/ralph-audit` style) with initialized `prd.json`, `progress.txt`, `README.md`, `CODEX.md`, and `ralph.sh`.
---

# Ralph Loop Builder

## Overview

Build a fresh Ralph workspace quickly and consistently so the team can start purpose-focused loops without hand-authoring boilerplate files.
This skill creates scaffolding only; actual story execution belongs to `ralph-driven-development`.
It also sets mutation policy (`read-only` vs `read-write`) and model routing defaults for the workspace.

## Ownership and Delegation

This skill owns:
- Creating `.codex/<workspace>/` structure and core files.
- Generating mode-specific `prd.json` and matching `progress.txt`.
- Repointing gate/diff defaults to a requested base ref.

This skill does not own:
- Running iterative story execution (`ralph-driven-development` owns that).
- General skill authoring process rules (`writing-skills` owns that).
- Topology-wide consistency audits (`skill-topology-adjuster` owns that).

## Workflow

1. Confirm scaffold inputs:
- `workspace` (folder under `.codex/`)
- `purpose` (one-line objective)
- `mode` (`audit` or `delivery`)
- `base_ref` (default `origin/main`)
- mutation policy override (`--read-only` or `--allow-write`, optional)
- model profile defaults (review/fix) and optional per-story overrides

2. Bootstrap workspace:
```bash
python ~/.codex/skills/ralph-loop-builder/scripts/bootstrap_ralph_loop.py \
  --repo-root . \
  --workspace ralph-audit \
  --purpose "delegation-integrity and main-diff reduction audit" \
  --mode audit \
  --read-only \
  --review-model gpt-5.2 \
  --review-reasoning-effort xhigh \
  --fix-model gpt-5.3-codex \
  --fix-reasoning-effort high \
  --base-ref origin/main
```

3. Validate generated state:
- `prd.json` exists and all stories have `passes: false`.
- `prd.json.workspaceSettings.readOnly` and `workspaceSettings.modelPolicy` match requested defaults.
- every story has `modelProfile` (default or story override).
- `progress.txt` checklist matches story IDs/titles.
- `README.md`/`CODEX.md` mention the requested `purpose` and `base_ref`.

4. Hand off execution:
- If user asks to run the loop, delegate to `ralph-driven-development`.

## Input Contract

- `workspace`: lowercase hyphen-case recommended (for example `ralph-audit`).
- `purpose`: short objective sentence; injected into README/CODEX/PRD descriptions.
- `mode`: use `audit` for review-first loops, `delivery` for implementation-oriented loops.
- `base_ref`: explicit diff base (`origin/main` recommended).
- mutation policy:
  - default: `audit` -> read-only, `delivery` -> read-write
  - override: `--read-only` or `--allow-write`
- model defaults:
  - review default: `--review-model gpt-5.2 --review-reasoning-effort xhigh`
  - fix default: `--fix-model gpt-5.3-codex --fix-reasoning-effort high`
- per-story model assignment:
  - `--story-model-overrides '{"US-002":{"model":"gpt-5.3-codex","reasoningEffort":"high"}}'`
  - or pass a JSON file path with the same object shape
- `--force`: allow overwrite when workspace already exists.

## Output Artifacts

Required generated files:
- `.codex/<workspace>/README.md`
- `.codex/<workspace>/CODEX.md`
- `.codex/<workspace>/prd.json`
- `.codex/<workspace>/progress.txt`
- `.codex/<workspace>/ralph.sh`
- `.codex/<workspace>/audit/` (empty output folder)

## Guardrails

- Never overwrite existing workspace contents unless `--force` is set.
- Keep `passes` initialized to `false` for all stories.
- Keep mutation policy explicit in `workspaceSettings.readOnly`.
- Keep model defaults explicit in `workspaceSettings.modelPolicy`.
- Keep per-story model decisions explicit via `userStories[].modelProfile`.
- Keep path references self-consistent (`.codex/<workspace>/...`) after generation.
- Keep base ref explicit in diff-related guidance to avoid ambiguous metrics.

## References

- `references/workspace_contract.md`
