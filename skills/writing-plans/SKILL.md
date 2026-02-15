---
name: writing-plans
description: Use when you need an implementation plan before coding; supports single-track plans and dependency-aware swarm plans.
---

# Writing Plans

## Overview

Create an implementation plan before coding.

- `mode=single`: one primary execution lane (default)
- `mode=swarm`: dependency-aware parallel-ready plan

Announce at start:
"I'm using the writing-plans skill to create the implementation plan."

## Mode Selection

- `mode=single`
  - Use for normal implementation planning.
  - Save to `docs/plans/YYYY-MM-DD-<feature-name>.md` by default.
- `mode=swarm`
  - Use for multi-agent or parallel execution planning.
  - Require explicit `depends_on` for every task.
  - Save scratch plan outside repo by default (`/private/tmp`, fallback `$CODEX_HOME/tmp`).

If user explicitly chooses mode, follow that choice.

## Shared Preparation

1. Read requirements/spec and inspect current code paths.
2. Resolve ambiguity before final tasking.
3. For external APIs/dependencies, confirm latest docs first.
4. Use exact file paths and verifiable commands.
5. Keep plan DRY, YAGNI, TDD-aligned.
6. Use search-as-discovery before path reads (`rg --files`, then `rg` patterns).
7. For each referenced script/path, verify existence with `test -f` / `test -d` first.
8. If a path is missing, do not keep retrying the same command; fallback to:
   - `git log --since=1.week --name-only`
   - `git diff --stat`
9. Require trace-plus-rg evidence in plan rationale for risky or ambiguous file targeting.

## Mode `single` Workflow

1. Define goal, architecture approach, and tech stack.
2. Break work into sequential tasks.
3. For each task, include files, tests-first steps, verification commands.
4. Save under repo docs unless user requested another path.

### Single Header (required)

```markdown
# [Feature Name] Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan.

**Goal:** [One sentence]
**Architecture:** [2-3 sentences]
**Tech Stack:** [Key libraries/tools]

---
```

## Mode `swarm` Workflow

1. Research architecture and constraints.
2. Define atomic tasks with explicit dependencies.
3. Ensure each task is independently executable by one agent.
4. Define validation per task.
5. Save to `/private/tmp/<topic>-plan.md` by default.
   - verify destination parent with `test -w`
   - fallback to `$CODEX_HOME/tmp/<topic>-plan.md`
   - copy into repo only when user asks
6. Run plan review pass (subagent preferred, local fallback):
   - missing dependencies
   - ordering issues
   - edge-case gaps
7. Revise with review evidence before yielding.

### Swarm Task Format (required)

Every task must include:
- `id`
- `depends_on`
- `location`
- `description`
- `validation`
- `status`
- `log`
- `files edited/created`

Example:

```text
T1: [depends_on: []] Create database migration
T2: [depends_on: []] Install dependencies
T3: [depends_on: [T1]] Create repository layer
T4: [depends_on: [T1]] Create service interfaces
T5: [depends_on: [T3, T4]] Implement business logic
```

## Task Structure Baseline

```markdown
### Task N: [Component Name]

**Files:**
- Create: `exact/path/to/file.py`
- Modify: `exact/path/to/existing.py`
- Test: `tests/exact/path/to/test.py`

**Step 1: Write failing test**
**Step 2: Run test and confirm fail**
**Step 3: Write minimal implementation**
**Step 4: Run test and confirm pass**
**Step 5: Commit**
```

## Execution Handoff

After saving the plan, offer execution strategy:

1. `strategy=subagent-loop`
- same-session task-by-task delivery with review loops
- use `executing-plans`

2. `strategy=batch-checkpoint`
- checkpointed delivery with feedback between batches
- use `executing-plans`

## Remember

- include exact file paths
- include concrete commands and expected results
- keep plan actionable and minimal
- do not start implementation in this skill
