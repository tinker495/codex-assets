# prd.json Schema

Use this schema for Ralph-style execution backlogs in Codex.

## Required Top-Level Fields

```json
{
  "project": "MyProject",
  "branchName": "ralph/feature-name",
  "description": "Short feature summary",
  "userStories": []
}
```

## User Story Shape

```json
{
  "id": "US-001",
  "title": "Short action-oriented title",
  "description": "As a [user], I want [capability] so that [benefit].",
  "acceptanceCriteria": [
    "Concrete check 1",
    "Concrete check 2",
    "Typecheck passes"
  ],
  "priority": 1,
  "passes": false,
  "notes": ""
}
```

## Conversion Rules

1. Keep one story small enough for one focused coding pass.
2. Set `passes` to `false` for all new stories.
3. Assign priorities by dependency order, not by prose order.
4. Require verifiable acceptance criteria.
5. Add browser verification criteria for UI stories.

## Quick Checklist

- Is every story independently shippable?
- Can the agent verify each criterion?
- Do earlier priorities unblock later work?
- Is the branch name kebab-case and prefixed with `ralph/`?

## Validation Command

```bash
python ~/.codex/skills/codex-ralph-loop/scripts/ralph_state.py validate --prd prd.json --strict-warnings
```

## Iteration State Commands

```bash
# One-shot summary for agent decision logic
python ~/.codex/skills/codex-ralph-loop/scripts/ralph_state.py brief --prd prd.json

# Suggest quality-check command set for this repo
python ~/.codex/skills/codex-ralph-loop/scripts/ralph_state.py quality-plan --repo-root . --json

# Record blocked story without flipping passes=true
python ~/.codex/skills/codex-ralph-loop/scripts/ralph_state.py mark-blocked \
  --prd prd.json \
  --story-id US-001 \
  --reason "failed quality gate" \
  --next-action "fix failing check and retry"
```
