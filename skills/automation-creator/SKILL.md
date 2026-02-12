---
name: automation-creator
description: Create, update, and inspect Codex automations (recurring tasks). Use when the user asks to add a recurring task, schedule an automation, change cadence/settings, or review existing automations.
---

# Automation Creator

## Overview

Translate user intent into Codex automation directives for creating, updating, or viewing recurring tasks.

## Workflow

### 1) Gather Inputs

- Identify the task objective and expected output.
- Identify schedule requirements (frequency, days, time) and confirm the user's local time zone.
- Identify which workspaces (`cwds`) the automation should use.
- If a required detail is missing, ask one targeted question.

### 2) Decide Mode

- If the user asks about existing automations, list them and emit view-mode directives.
- If the user wants to change an existing automation, read the current automation TOML, then emit a suggested update directive.
- If the user wants a new automation, emit a suggested create directive.

### 3) Construct Fields

- `name`: Short, human-friendly label. Propose one if the user does not provide it.
- `prompt`: Task only. Do not include schedule or workspace details.
- `prompt` safety: If prompt text includes double quotes (for example `python -c "..."`), escape inner quotes as `\"` so the TOML string stays valid.
- `rrule`: Use supported formats only:
  - Hourly interval: `FREQ=HOURLY;INTERVAL=<hours>[;BYDAY=MO,TU,...]`
  - Weekly schedule: `FREQ=WEEKLY;BYDAY=MO,TU,...;BYHOUR=<0-23>;BYMINUTE=<0-59>`
- `cwds`: Comma-separated list or JSON array string of workspace paths.
- `status`: Default to `ACTIVE` unless user requests paused.
- `validation`: After editing an automation TOML, parse it once with `tomllib`. If default `python` lacks `tomllib`, use `python3.11` fallback.

### 4) Emit Directive

- Output a single `::automation-update{...}` directive.
- If helpful, add a short explanation of assumptions and any defaults.

## Directive Examples

```text
::automation-update{mode="suggested create" name="Daily report" prompt="Summarize Sentry errors" rrule="FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR;BYHOUR=9;BYMINUTE=0" cwds="/path/one,/path/two" status="ACTIVE"}
```

```text
::automation-update{mode="view" id="123"}
```
