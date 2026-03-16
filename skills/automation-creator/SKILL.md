---
name: automation-creator
description: Create, update, and inspect Codex automations (recurring tasks). Use when the user asks to add a recurring task, schedule an automation, change cadence/settings, or review existing automations.
---

# Automation Creator

## Overview

Translate user intent into Codex automation directives for creating, updating, or viewing recurring tasks. When reviewing or updating an existing automation, audit prompt quality in addition to model, schedule, and workspace settings.

## Workflow

### 1) Gather Inputs

- Set `CODEX_HOME=${CODEX_HOME:-$HOME/.codex}` before any automation file access.
- Identify the task objective and expected output.
- Identify schedule requirements (frequency, days, time) and confirm the user's local time zone.
- Identify which workspaces (`cwds`) the automation should use.
- If reviewing or updating an existing automation, read the current `automation.toml` first and read `memory.md` when present to understand prior run outcomes.
- If a required detail is missing, ask one targeted question.

### 2) Decide Mode

- If the user asks about existing automations, list them and emit view-mode directives.
- If the user wants to change an existing automation, read the current automation TOML, then emit a suggested update directive.
- If the user wants a new automation, emit a suggested create directive.

### 3) Audit Existing Automation Quality

For existing automations, review the current prompt before proposing changes.

- Check whether the prompt duplicates data already owned by a script or structured output; prefer one canonical source of truth.
- Check whether the prompt has a clear output contract, for example exact decision buckets, ranked recommendations, required evidence, or explicit no-change behavior.
- Check whether execution order and prioritization are explicit enough for repeated runs.
- Check whether guardrails or fallback rules are stale, contradictory, or drifting from actual file paths/resources.
- Prefer shorter prompts after the audit; remove restated lists when a script or file already owns them.
- Preserve `rrule` and `cwds` unless the user asked to change them or the evidence shows cadence/workspace is part of the problem.
- When the automation audits machine-wide Codex state under `~/.codex` (for example `sessions`, `automations`, or `skills`), default `cwds` to `~/.codex` rather than a backup/admin repo such as `~/project/codex-skills`.
- If the automation reviews many repos from session history, keep `cwds` at `~/.codex` and recover per-repo context from session metadata instead of anchoring the run to one repo.

### 4) Construct Fields

- `name`: Short, human-friendly label. Propose one if the user does not provide it.
- `prompt`: Task only. Do not include schedule or workspace details.
- `prompt` safety: If prompt text includes double quotes (for example `python -c "..."`), escape inner quotes as `\"` so the TOML string stays valid.
- `rrule`: Use supported formats only:
  - Hourly interval: `FREQ=HOURLY;INTERVAL=<hours>[;BYDAY=MO,TU,...]`
  - Weekly schedule: `FREQ=WEEKLY;BYDAY=MO,TU,...;BYHOUR=<0-23>;BYMINUTE=<0-59>`
- `cwds`: Comma-separated list or JSON array string of workspace paths.
- `cwds` rule: Choose the narrowest real execution root for the task. Repo-local automation uses the target repo. Machine-wide Codex automation uses `~/.codex`.
- `status`: Default to `ACTIVE` unless user requests paused.
- `validation`: After editing an automation TOML, parse it once with `tomllib`. If default `python` lacks `tomllib`, use `python3.11` fallback.
- `path checks`: Before reading or writing automation files, verify with `test -d` and `test -w` on the parent directory.
  If the parent is not writable, fallback outputs to repo root or `$CODEX_HOME`; if neither is writable, stop and report.
- `path convention`: Never use `/automations/...` absolute paths. Always use `$CODEX_HOME/automations/<id>`.
- `shell guardrail`: Avoid here-doc syntax and prefer `python -c` or single-line commands.
- `date guardrail`: If `date -I` fails, use `python -c "import datetime; print(datetime.date.today().isoformat())"`.
- `flag fallback`: If a tool rejects `--json`, rerun without it and parse plain-text output.
- `repo fallback`: If repo context is needed but the automation runs from `~/.codex`, recover `repo_root` from session `workdir` or absolute file paths, verify with `git -C <repo_root> rev-parse --is-inside-work-tree`, then run `git -C <repo_root> ...`. Do not assume the automation `cwd` is the repo.

### 5) Emit Directive

- Output a single `::automation-update{...}` directive.
- If helpful, add a short explanation of assumptions and any defaults.

## Directive Examples

```text
::automation-update{mode="suggested create" name="Daily report" prompt="Summarize Sentry errors" rrule="FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR;BYHOUR=9;BYMINUTE=0" cwds="/path/one,/path/two" status="ACTIVE"}
```

```text
::automation-update{mode="view" id="123"}
```
