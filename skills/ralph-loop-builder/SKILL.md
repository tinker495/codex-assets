---
name: ralph-loop-builder
description: Use when a user wants a new purpose-specific Ralph workspace under `.codex/` (for example `.codex/ralph-audit` style) with initialized `prd.json`, `progress.txt`, `README.md`, `CODEX.md`, and `ralph.sh`.
---

# Ralph Loop Builder

## Overview

Build a fresh Ralph workspace quickly and consistently so the team can start purpose-focused loops without hand-authoring boilerplate files.
This skill creates scaffolding only; actual story execution belongs to `ralph-driven-development`.

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

2. Bootstrap workspace:
```bash
python ~/.codex/skills/ralph-loop-builder/scripts/bootstrap_ralph_loop.py \
  --repo-root . \
  --workspace ralph-audit \
  --purpose "delegation-integrity and main-diff reduction audit" \
  --mode audit \
  --base-ref origin/main
```

3. Validate generated state:
- `prd.json` exists and all stories have `passes: false`.
- `progress.txt` checklist matches story IDs/titles.
- `README.md`/`CODEX.md` mention the requested `purpose` and `base_ref`.

4. Hand off execution:
- If user asks to run the loop, delegate to `ralph-driven-development`.

## Input Contract

- `workspace`: lowercase hyphen-case recommended (for example `ralph-audit`).
- `purpose`: short objective sentence; injected into README/CODEX/PRD descriptions.
- `mode`: use `audit` for read-only evidence loops, `delivery` for implementation-oriented loops.
- `base_ref`: explicit diff base (`origin/main` recommended).
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
- Keep path references self-consistent (`.codex/<workspace>/...`) after generation.
- Keep base ref explicit in diff-related guidance to avoid ambiguous metrics.

## References

- `references/workspace_contract.md`
