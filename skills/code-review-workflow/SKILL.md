---
name: code-review-workflow
description: Use when requesting a code review before merge or when triaging incoming review feedback before implementing changes.
---

# Code Review Workflow

Unify outbound review requests and inbound review triage in one skill.

## Phase Selection

- `phase=request`
  - Use after task/feature completion or before merge.
- `phase=triage-feedback`
  - Use when review comments were received and must be evaluated before implementation.

If phase is unclear, infer from user intent; ask one targeted question only if blocked.

## Phase `request`

1. Define review scope (what changed, requirements/plan reference).
2. Collect SHAs:

```bash
BASE_SHA=$(git rev-parse HEAD~1)  # or origin/main
HEAD_SHA=$(git rev-parse HEAD)
```

3. Dispatch review subagent using template:
- `/Users/mrx-ksjung/.codex/skills/code-review-workflow/code-reviewer.md`

Required placeholders:
- `{WHAT_WAS_IMPLEMENTED}`
- `{PLAN_OR_REQUIREMENTS}`
- `{BASE_SHA}`
- `{HEAD_SHA}`
- `{DESCRIPTION}`

4. Process findings by severity:
- Critical: fix now
- Important: fix before proceeding
- Minor: backlog or opportunistic fixes

## Phase `triage-feedback`

Apply this strict sequence:
1. read all feedback fully
2. restate technical requirement or ask clarification
3. verify against actual codebase behavior
4. assess technical validity for this repo
5. implement one item at a time with tests

Rules:
- never implement unclear items first; clarify scope before coding
- do not do performative agreement; respond with technical facts
- push back with evidence when suggestion is incorrect or conflicts with constraints
- if reviewer suggestion conflicts with prior user architectural decisions, stop and confirm

## Ordering for multi-item feedback

1. blocking issues (breakage/security/data risk)
2. simple deterministic fixes
3. complex refactors/logic changes

After each fix: run relevant verification and confirm no regression.

## Output Contract

- `phase=request`: summarize requested scope, SHAs, reviewer findings, and fix plan.
- `phase=triage-feedback`: summarize accepted/rejected items with evidence and implemented changes.

## Integration

- `executing-plans` (subagent-loop) should call this skill for review gates.
- `verification-before-completion` remains the final completion evidence gate.
