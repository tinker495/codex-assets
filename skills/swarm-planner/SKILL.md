---
name: swarm-planner
description: >
  [EXPLICIT INVOCATION ONLY] Creates dependency-aware implementation plans optimized for parallel
  multi-agent execution.
metadata:
  invocation: explicit-only
---

# Swarm-Ready Planner

Create implementation plans with explicit task dependencies optimized for parallel agent execution. This skill can be ran inside or outside of Plan Mode. 

## Core Principles

1. **Explore Codebase**: Investigate architecture, patterns, existing implementations, dependencies, and frameworks in use.
2. **Fresh Documentation First**: Use Context7 for ANY external library, framework, or API before planning tasks
3. **Ask Questions**: Clarify ambiguities and seek clarification on scope, constraints, or priorities throughout the planning process. At any time.
4. **Explicit Dependencies**: Every task declares what it depends on, enabling maximum parallelization
5. **Atomic Tasks**: Each task is independently executable by a single agent
6. **Review Before Yield**: A subagent reviews the plan for gaps before finalizing
7. **Artifact Isolation**: Save plans and all intermediate artifacts outside the target codebase by default (`/private/tmp` preferred, fallback `$CODEX_HOME/tmp`). Never write planning scratch files into the repository unless the user explicitly asks.

## Process

### 1. Research

**Codebase investigation:**
- Architecture, patterns, existing implementations
- Dependencies and frameworks in use

### 1a. Optional: Stop to Clarification Questions

- If the architecture is unclear or missing STOP AND YIELD to the user, and request user input (AskUserQuestions) before moving on. Always offer recommendations for clarification questions.
- If architecture is present, skip 1a and move onto next step. 

### 2. Documentation

**Documentation retrieval (REQUIRED for external dependencies):**

Use Context7 skill or MCP to fetch current docs for any libraries/frameworks or APIs that are or will be used in project. If Context7 is not available, use web search.

This ensures version-accurate APIs, correct parameters, and current best practices.

### 3. STOP and Request User Input

When anything is unclear or could reasonably be done multiple ways:
- Stop and ask clarifying questions immediately
- Do not make assumptions about scope, constraints, or priorities
- Questions should reduce risk and eliminate ambiguity
- Always offer recommendations for clarification questions.
- Use request_user_input or AskUserQuestion tool if available. 

### 4. Create Dependency-Aware Plan

Structure the plan with explicit task dependencies using this format:

#### Task Dependency Format

Each task MUST include:
- **id**: Unique identifier (e.g., `T1`, `T2.1`)
- **depends_on**: Array of task IDs that must complete first (empty `[]` for root tasks)
- **description**: What the task accomplishes
- **location**: File paths involved
- **validation**: How to verify completion

**Example:**
```
T1: [depends_on: []] Create database schema migration
T2: [depends_on: []] Install required packages
T3: [depends_on: [T1]] Create repository layer
T4: [depends_on: [T1]] Create service interfaces
T5: [depends_on: [T3, T4]] Implement business logic
T6: [depends_on: [T2, T5]] Add API endpoints
T7: [depends_on: [T6]] Write integration tests
```

Tasks with empty/satisfied dependencies can run in parallel (T1, T2 above).

### 4. Save Plan

Save to `/private/tmp/<topic>-plan.md` by default.

- Before writing, verify destination parent directory with `test -w`.
- If `/private/tmp` is unavailable, use `$CODEX_HOME/tmp/<topic>-plan.md`.
- Do **not** save planning artifacts in repository CWD by default.
- Only copy a plan into the repository when the user explicitly requests repository persistence.

### 5. Subagent Review

After saving, spawn a subagent to review the plan:

```
Review this implementation plan for:
1. Missing dependencies between tasks
2. Ordering issues that would cause failures
3. Missing error handling or edge cases
4. Gaps, holes, gotchas.

Provide specific, actionable feedback. Do not ask questions.

Plan location: [file path]
Context: [brief context about the task]
```

If the subagent provides actionable feedback, revise the plan before yielding.

Store review prompt files, review logs, and helper outputs in `/private/tmp` (or `$CODEX_HOME/tmp` fallback), not in the target repository.

### 5a. Review Timeout and Fallback (Required)

Treat subagent review as bounded execution:

1. Start review with a bounded command (JSONL log + explicit output path).
2. Poll progress for a fixed timeout window (recommended: 120 seconds).
   - If `timeout` wrapper is unavailable, poll using plain shell sleeps (or `gtimeout` when available).
3. If final review content is missing, incomplete, or the process hangs:
   - stop waiting,
   - record the failure mode briefly,
   - run local static review immediately using the same 4 criteria:
     1) missing dependencies, 2) ordering failures, 3) missing edge cases, 4) gaps/gotchas.
4. Revise the plan using whichever review evidence is available (subagent and/or local fallback).
5. Never claim "subagent reviewed" unless final review output was actually captured.


## Plan Template

```markdown
# Plan: [Task Name]

**Generated**: [Date]

## Overview
[Summary of task and approach]

## Prerequisites
- [Tools, libraries, access needed]

## Dependency Graph

```
[Visual representation of task dependencies]
T1 ──┬── T3 ──┐
     │        ├── T5 ── T6 ── T7
T2 ──┴── T4 ──┘
```

## Tasks

### T1: [Name]
- **depends_on**: []
- **location**: [file paths]
- **description**: [what to do]
- **validation**: [how to verify]
- **status**: Not Completed
- **log**: [leave empty, to be filled out later]
- **files edited/created**: [leave empty, to be filled out later]

### T2: [Name]
- **depends_on**: []
- **location**: [file paths]
- **description**: [what to do]
- **validation**: [how to verify]
- **status**: Not Completed
- **log**: [leave empty, to be filled out later]
- **files edited/created**: [leave empty, to be filled out later]

### T3: [Name]
- **depends_on**: [T1]
- **location**: [file paths]
- **description**: [what to do]
- **validation**: [how to verify]
- **status**: Not Completed
- **log**: [leave empty, to be filled out later]
- **files edited/created**: [leave empty, to be filled out later]

[... continue for all tasks ...]

## Parallel Execution Groups

| Wave | Tasks | Can Start When |
|------|-------|----------------|
| 1 | T1, T2 | Immediately |
| 2 | T3, T4 | Wave 1 complete |
| 3 | T5 | T3, T4 complete |
| ... | ... | ... |

## Testing Strategy
- [How to test]
- [What to verify]

## Risks & Mitigations
- [What could go wrong + how to handle]
```

## Important

- Every task must have explicit `depends_on` field
- Root tasks (no dependencies) can be executed in parallel immediately
- Do NOT implement - only create the plan
- Always use Context7 for external dependencies before finalizing tasks
- Always ask questions where ambiguity exists
- Keep all intermediate planning artifacts out of the codebase (plan drafts, prompts, logs, scratch notes)
