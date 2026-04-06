---
name: simplify
description: Improve code clarity, consistency, and maintainability while preserving exact behavior. Use when asked to simplify, refactor, clean up, improve readability, assess code quality, find problems, audit code, or review a module for structural, smell, or consistency issues. Do not use for feature work, formatting-only passes, dependency upgrades, broad architecture changes, or public API redesign.
---

# Simplify

Refactor code so the next developer reads it and thinks "of course."
Preserve behavior, stay in scope, and justify every change with concrete evidence.

## Iron Laws

1. **Functionality is sacred**
   - Preserve exact behavior.
   - Treat passing tests as the floor, not the goal.
   - Stop and ask before changing public APIs or intended behavior.
2. **Clarity over cleverness**
   - Prefer explicit control flow over compressed expressions.
   - Reduce nesting, duplication, and indirection only when the result is easier to read.
3. **Consistency over local perfection**
   - Follow the surrounding codebase patterns.
   - Migrate all instances of a pattern or none when partial cleanup would create drift.
4. **Atomic changes**
   - Keep each edit reviewable on its own.
   - Group related fixes, but do not mix unrelated cleanup concerns in one pass.
5. **Evidence over opinion**
   - Name the metric improved before editing: nesting depth, branch count, duplication, dead code, naming drift, or removed indirection.

## Modes

- **Refactor**: find issues and fix them.
- **Audit**: find issues and report them without editing.

Use **Audit** when the request says `find problems`, `audit`, `scan`, `what's wrong`, or otherwise asks for diagnosis only.
Default to **Refactor** for `simplify`, `refactor`, `clean up`, `improve readability`, or similar requests.

## Workflow

### 1. Scope the pass

Resolve scope in this order:

1. User-specified files: use the exact files.
2. User-specified directory or module: recurse source files under that path.
3. Entire repo: use tracked source files and warn internally about scope cost.
4. No explicit scope: use recent work from `git diff --name-only HEAD` plus staged changes.
5. No files found: stop and ask for scope.

Stay inside the declared scope. Do not use "while I'm here" reasoning.

### 2. Load context

Read, in parallel when possible:

1. Governing instructions: `AGENTS.md`, `CLAUDE.md`, `.editorconfig`, lint and formatter configs.
2. Every target file in full.
3. Adjacent context that affects safe cleanup: imports, importers, shared types, shared helpers, and nearby tests.

Derive project conventions from the code you read:

- naming
- import ordering
- error handling
- typing style
- comments and docstring patterns
- branching and helper extraction habits

Never edit a file that was not read in the current session.

### 3. Analyze and plan before editing

Analyze all targets across three dimensions:

1. **Structural**
   - long functions
   - deep nesting
   - large parameter lists
   - repeated branching
   - unnecessary wrapper layers
2. **Smells**
   - duplication with 3+ materially identical blocks
   - dead code
   - stale flags
   - magic values
   - feature envy
   - misleading comments
3. **Consistency**
   - naming drift
   - type annotation gaps relative to local norms
   - uneven guard-clause usage
   - import/style deviations from nearby files

Record findings as:

`[file:line] - issue - confidence (0-100)`

Before any edit, write a cleanup plan with:

- scope
- target smells
- edit order
- expected verification commands

Score each finding:

- **76-100**: must fix
- **51-75**: apply
- **26-50**: apply only if obvious and zero-risk
- **0-25**: skip

Decision gate:

- In **Audit** mode, return the findings report and stop.
- If the work is fewer than 10 low-risk edits, proceed autonomously.
- If the work exceeds 10 edits, requires structural rewrites, or risks API changes, stop after the plan and ask the user.

### 4. Refactor safely

Work in priority order from highest-signal to lowest-risk.

Before each file edit:

1. Re-read the current file state.
2. Confirm the cleanup metric being improved.
3. Search references before deleting or renaming anything shared.

Editing rules:

- Lock behavior first with existing tests when available.
- If behavior is not protected and cleanup is risky, add only the narrowest regression coverage needed to preserve current behavior.
- Prefer deletion over extraction.
- Reuse existing helpers before introducing new abstractions.
- Do not add dependencies.
- Do not broaden scope.
- Keep related edits in the same file together.

Stop-loss:

- If the same edit fails twice, stop that line of work.
- Report it as `attempted, reverted - reason`.

### 5. Verify

Verification is mandatory.

Discover available commands from project files such as `package.json`, `Makefile`, `pyproject.toml`, `Cargo.toml`, or repo docs, then run the relevant checks for the touched code:

1. lint
2. typecheck
3. tests covering modified behavior
4. static analysis or equivalent repo-standard checks when available

Requirements:

- introduce zero new failures
- read command output before claiming success
- if a change breaks verification, narrow or revert that change and continue

### 6. Report

Return a concise report in this shape:

```text
## Simplification Report

### Execution
- Mode: refactor | audit
- Scope: N files (recent changes | directory: X | explicit file list)

### Changes Applied (N total)
- [file:line] - What changed - Why (confidence: N)

### Verification
- Lint: PASS/FAIL
- Typecheck: PASS/FAIL
- Tests: PASS/FAIL
- Static analysis: PASS/FAIL or N/A

### Metrics
- Lines: +N / -M (net: +/-K)
- Files touched: N

### Remaining Risks
- [none or short deferred item]
```

Always include:

- changed files
- simplifications made
- verification run
- remaining risks or consciously deferred items

## Parallelism

- 1-5 files: analyze locally.
- 6-20 files: use explorer-style subagents for independent read-only analysis slices when that reduces latency.
- 20+ files: split by independent module only when write scopes are clearly disjoint.

If independence is unclear, stay sequential.

## Anti-Rationalization Checklist

Before editing, verify every answer is `yes`:

- Can you name the exact metric improved?
- Did you search all references before removing or renaming code?
- Does any new abstraction serve at least 3 real call sites?
- Are you preserving project conventions instead of introducing a private style?
- Is the diff smaller and clearer than the code smell that triggered it?
- Are you staying strictly within scope?
- Would a senior engineer unfamiliar with the task understand why each change was made?

If any answer is `no`, stop and tighten the plan before editing.

## Boundaries

Do not use this skill to:

- add features
- do formatting-only cleanup
- upgrade dependencies
- rewrite architecture
- redesign public APIs
- run speculative rewrites with unclear payoff
