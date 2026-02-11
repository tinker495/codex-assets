---
name: executing-plans
description: Use when executing a written implementation plan; supports batch-checkpoint and subagent-loop strategies.
---

# Executing Plans

## Overview

Execute an existing implementation plan with explicit strategy selection.

- `strategy=batch-checkpoint` (default)
- `strategy=subagent-loop`

Announce at start:
"I'm using the executing-plans skill to implement this plan."

## Strategy Selection

- `strategy=batch-checkpoint`
  - Use for checkpointed delivery with human feedback between batches.
- `strategy=subagent-loop`
  - Use for same-session execution when tasks are mostly independent.
  - Execute task-by-task with implementer + two-stage review.

If user explicitly sets strategy, follow it.

## Shared Preflight (all strategies)

1. Read the full plan.
2. Check for ambiguity, contradictions, and blockers.
3. If critical gaps exist, stop and ask before coding.
4. Create a task tracker (TodoWrite or equivalent).
5. Never start on `main`/`master` without explicit user consent.

## Strategy `batch-checkpoint`

### Step 1: Execute batch

Default batch size: first 3 pending tasks.

Per task:
1. mark `in_progress`
2. execute the task as written
3. run required verification
4. mark `completed`

### Step 2: Report and wait

After each batch:
- summarize changes
- show verification output
- report `Ready for feedback.`
- wait for feedback before next batch

### Step 3: Continue

Apply feedback and repeat until all tasks complete.

## Strategy `subagent-loop`

Per task loop:
1. dispatch implementer subagent with full task context
2. if implementer asks questions, answer and continue
3. implementer executes/tests/self-reviews
4. run spec review; if issues exist, fix then re-review
5. run code-quality review; if issues exist, fix then re-review
6. mark task complete only after both reviews pass

Rules:
- do not run overlapping implementer tasks in parallel
- do not start code-quality review before spec review passes
- do not move to next task with unresolved review issues

Prompt templates:
- `/Users/mrx-ksjung/.codex/skills/executing-plans/prompts/implementer-prompt.md`
- `/Users/mrx-ksjung/.codex/skills/executing-plans/prompts/spec-reviewer-prompt.md`
- `/Users/mrx-ksjung/.codex/skills/executing-plans/prompts/code-quality-reviewer-prompt.md`

## Completion

After all tasks are done and verified:
1. announce finishing step
2. use `superpowers:finishing-a-development-branch`
3. follow its integration/cleanup workflow

## Stop Conditions

Stop immediately and ask for clarification when:
- plan instructions are unclear or contradictory
- required verification repeatedly fails
- hidden dependencies block execution

Do not guess through blockers.

## Integration

Required workflow skills:
- `superpowers:using-git-worktrees`
- `superpowers:writing-plans`
- `superpowers:finishing-a-development-branch`

Recommended in `strategy=subagent-loop`:
- `superpowers:code-review-workflow`
- `superpowers:test-driven-development`
