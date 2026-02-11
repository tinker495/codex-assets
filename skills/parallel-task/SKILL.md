---
name: parallel-task
description: >
  Use when executing 2+ tasks in parallel; supports dependency-aware plan execution (`mode=standard`), UI-routed execution (`mode=design-route`), and independent-domain dispatch without a plan (`mode=independent`).
---

# Parallel Task Executor

You are an Orchestrator for parallel execution.

This skill owns three lanes:
- `mode=standard`: plan-based dependency waves
- `mode=design-route`: plan-based waves with design-task routing
- `mode=independent`: no plan file, dispatch one agent per independent domain

Choose one mode at start and keep it for the full invocation.

## Mode Selection

- `mode=standard`
  - Use when a plan file exists and tasks should run via dependency waves.
- `mode=design-route`
  - Use when plan tasks include significant UI/styling scope.
  - Route `design` tasks via `claude -p` and `standard` tasks via Task tool subagents.
- `mode=independent`
  - Use when there is no plan file and the request is multiple independent tasks/failures.
  - Dispatch one subagent per domain in parallel.

If the user explicitly sets mode, follow it.
If no mode is set:
- choose `mode=standard` when a plan path/task IDs are provided
- choose `mode=independent` when the request is ad-hoc independent work

Legacy command wording `/co-design` should be interpreted as `mode=design-route`.

## Design Task Classification (`mode=design-route`)

Classify task as `design` when it includes:
- CSS/SCSS/Tailwind/themes/tokens
- template/markup/layout/responsiveness
- visual effects/transitions/animations
- UI visual accessibility

Otherwise classify as `standard`.
If mixed, classify as `design`.

## Plan-Based Process (`mode=standard` and `mode=design-route`)

### Step 1: Parse request

Extract:
1. plan file path
2. optional task subset

### Step 2: Read and parse plan

For each task, extract:
- task ID and name
- `depends_on`
- description/location/acceptance criteria/validation

If subset was requested, keep requested IDs plus required dependencies.
In `mode=design-route`, classify each task as `design` or `standard`.

### Step 3: Launch by dependency wave

A task is unblocked when all `depends_on` task IDs are complete.
Launch all unblocked tasks in parallel.

- `mode=standard`: all tasks via Task tool subagents.
- `mode=design-route`:
  - `standard` tasks -> Task tool subagents
  - `design` tasks -> `claude -p` background process

```bash
claude -p "YOUR_PROMPT_HERE" \
  --allowedTools "Bash,Read,Edit,Write,Glob,Grep,WebFetch,WebSearch" \
  --max-turns 50 \
  --output-format text \
  > /tmp/parallel-task-[TASK_ID]-output.log 2>&1 &
```

Track PID and output log for each background task.

### Step 4: Validate wave output

After each wave:
1. inspect outputs for completeness/correctness
2. verify plan task status and logs were updated
3. retry/escalate failed tasks
4. proceed to next unblocked wave

Repeat until all tasks are complete.

## Independent Process (`mode=independent`)

Use this when tasks are independent and no formal plan is provided.

### Step 1: Split into domains

Group work by independent domains (different files/subsystems/root causes).
If tasks are coupled or share state heavily, stop and ask one targeted question.

### Step 2: Create per-domain prompt

Each subagent prompt must include:
- narrow scope (one domain)
- explicit constraints (avoid unrelated edits)
- expected output (root cause, changed files, validation)

### Step 3: Dispatch in parallel

Launch one subagent per independent domain.
Do not dispatch overlapping domains in parallel.

### Step 4: Integrate and verify

- review each subagent result
- resolve conflicts if any
- run final integration checks/tests
- summarize by domain with status

## Error Handling

- Plan file missing or parse failure: show what failed and ask for corrected path/input.
- Task subset not found: list available task IDs.
- Background process crash/timeout: inspect logs, retry or reroute.
- Overlapping domains in `mode=independent`: stop parallelization and run sequentially.

## Example Usage

```text
/parallel-task plan.md
/parallel-task ./plans/auth-plan.md T1 T2 T4
/parallel-task --mode design-route plans/landing-page.md
/parallel-task "Fix 3 independent failures in auth tests, billing API, and CSV export"
```

## Delegation Boundaries

- This skill owns parallel launch policy, dependency waves, and independent-domain dispatch.
- `writing-plans` owns plan authoring and dependency schema.
- `executing-plans` owns non-parallel sequential execution strategies.

## Execution Summary Template

```markdown
# Execution Summary

## Tasks Assigned: [N]
- Mode: [standard | design-route | independent]
- Design tasks (if any): [count]
- Standard tasks: [count]
- Independent domains (if any): [count]

### Completed
- [Task/Domain ID]: [Summary]

### Issues
- [Task/Domain ID]
  - Issue: [What went wrong]
  - Resolution: [How resolved or what is needed]

### Blocked
- [Task/Domain ID]
  - Blocker: [What blocks completion]
  - Next steps: [Needed action]

## Overall Status
[Completion summary]

## Files Modified
[List]

## Next Steps
[Recommendations]
```
