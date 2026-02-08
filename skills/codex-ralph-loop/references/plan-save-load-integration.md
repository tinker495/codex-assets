# Plan Save Load Integration

Use `plan-save-load` to persist iteration planning outside the repository.

Script path:
`python ~/.codex/skills/plan-save-load/scripts/plan_save_load.py`

Prerequisite: run inside a git repository with at least one commit.

## Group Convention

- Default group: `ralph-loop`
- Optional stable continuity token: `--ticket <ID>`
- For policy-bound groups (`hotfix`, `release-checklist`, `pr-review`), provide `--ticket`.

## Start of Invocation

1. Try resume:
```bash
python ~/.codex/skills/plan-save-load/scripts/plan_save_load.py load \
  --repo-dir . \
  --plan-group ralph-loop \
  --latest
```
2. If no file found, create:
```bash
python ~/.codex/skills/plan-save-load/scripts/plan_save_load.py create \
  --repo-dir . \
  --plan-group ralph-loop
```

## During Invocation

Append start note:
```bash
cat <<'EOF' | python ~/.codex/skills/plan-save-load/scripts/plan_save_load.py save \
  --repo-dir . \
  --plan-group ralph-loop \
  --latest \
  --stdin \
  --append
## Iteration Start
- Story: US-001
- Goal: implement one story and keep checks green
EOF
```

Append result note:
```bash
cat <<'EOF' | python ~/.codex/skills/plan-save-load/scripts/plan_save_load.py save \
  --repo-dir . \
  --plan-group ralph-loop \
  --latest \
  --stdin \
  --append
## Iteration Result
- Story: US-001
- Result: success|blocked
- Checks: <commands run>
- Next: <next action>
EOF
```

## End of Backlog

When all stories are complete:
```bash
python ~/.codex/skills/plan-save-load/scripts/plan_save_load.py complete \
  --repo-dir . \
  --plan-group ralph-loop \
  --latest \
  --summary "all stories passed" \
  --move
```

## Status and Recovery

Check active/archive status:
```bash
python ~/.codex/skills/plan-save-load/scripts/plan_save_load.py status \
  --repo-dir . \
  --plan-group ralph-loop
```

Reopen archived plan for follow-up work:
```bash
python ~/.codex/skills/plan-save-load/scripts/plan_save_load.py reopen \
  --repo-dir . \
  --plan-group ralph-loop \
  --latest \
  --reason "follow-up fixes"
```
