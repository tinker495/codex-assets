---
name: simplify
description: Improve code clarity, consistency, and maintainability while preserving exact behavior. Use when asked to simplify, refactor, clean up, improve readability, assess code quality, find problems, audit code, review a module for structural, smell, or consistency issues, or analyze commit, branch, or whole-codebase changes and carry out safe follow-up cleanup. Trigger this skill for requests such as recent commit follow-up, HEAD cleanup, branch-wide cleanup, latest refactor review, diff-driven cleanup, or whole-codebase forensic simplification before behavior-preserving fixes. Do not use for feature work, formatting-only passes, dependency upgrades, broad architecture changes, or public API redesign.
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
- **Forensic-Followup**: analyze a commit, branch, diff, or full codebase slice in detail, classify cleanup patterns, and carry out safe follow-up fixes.

Use **Audit** when the request says `find problems`, `audit`, `scan`, `what's wrong`, or otherwise asks for diagnosis only.
Default to **Refactor** for `simplify`, `refactor`, `clean up`, `improve readability`, or similar requests.
Use **Forensic-Followup** when the request is centered on a change set or a broad cleanup evidence pass, for example `last commit analysis`, `recent commit follow-up`, `HEAD cleanup`, `branch cleanup`, `diff-driven cleanup`, `whole codebase simplification`, `직전 커밋 분석`, `브랜치 단위 정리`, or `전체 코드베이스 기준 후속 수정`.

## Workflow

### 1. Scope the pass

Resolve scope in this order:

1. User-specified files: use the exact files.
2. User-specified directory or module: recurse source files under that path.
3. Entire repo: use tracked source files and warn internally about scope cost.
4. No explicit scope: use recent work from `git diff --name-only HEAD` plus staged changes.
5. No files found: stop and ask for scope.

Stay inside the declared scope. Do not use "while I'm here" reasoning.

### Forensic-Followup scope

When running in **Forensic-Followup** mode:

1. Resolve the forensic unit first:
   - explicit files or module
   - explicit commit, SHA, or git range
   - explicit branch or PR diff
   - whole codebase
   - otherwise default to `HEAD`
2. For a single commit or `HEAD`, inspect it with `git log -1`, `git show --stat`, and `git diff --numstat HEAD~1 HEAD`.
3. For a branch-level pass, inspect branch state with `git status --short --branch`, determine the comparison base from user input, repo docs, or the default branch, then inspect the branch diff with `git diff --stat` and `git diff --numstat` against the merge base.
4. For a whole-codebase pass, inventory tracked source files, identify hotspots from recent changes, tests, lint/type errors, or complexity signals, then process the codebase in bounded clusters instead of pretending the entire repo is one edit batch.
5. Read every touched or selected file in full before editing.
6. Read adjacent importers, shared types, re-export surfaces, and nearby tests that could break from the refactor.

### 2. Load context

Read, in parallel when possible:

1. Governing instructions: `AGENTS.md`, `CLAUDE.md`, `.editorconfig`, lint and formatter configs.
2. Every target file in full.
3. Adjacent context that affects safe cleanup: imports, importers, shared types, shared helpers, and nearby tests.

Before direct reads or targeted searches, verify each concrete file or directory operand with `test -f` or `test -d`. If a guessed path is missing, recover with repo-root-aware discovery such as `rg --files` instead of retrying the same path or assuming siblings like `src/tests` exist.

Derive project conventions from the code you read:

- naming
- import ordering
- error handling
- typing style
- comments and docstring patterns
- branching and helper extraction habits

Never edit a file that was not read in the current session.

For **Forensic-Followup**, read touched tests and import surfaces even when they are outside the edited set. The goal is to catch cleanup fallout, not only obvious local smells.

### 3. Analyze and plan before editing

Analyze all targets across three dimensions:

1. **Structural**
   - long functions
   - deep nesting
   - large parameter lists
   - repeated branching
   - unnecessary wrapper layers
   - redundant alias pairs or pass-through forwarders for the same concept
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

For **Forensic-Followup**, also classify each touched change into one of these archetypes before editing:

- trivial wrapper removal or inline
- single-use local removal
- re-export or `__all__` cleanup
- type annotation tightening
- signature propagation into tests and importers
- guard removal that may alter runtime contracts
- concrete return-type drift

Decision gate:

- In **Audit** mode, return the findings report and stop.
- If the work is fewer than 10 low-risk edits, proceed autonomously.
- If the work exceeds 10 edits, requires structural rewrites, or risks API changes, stop after the plan and ask the user.

Exception for **Forensic-Followup**:

- Do not use raw edit count as the stop condition.
- Proceed cluster by cluster when the changes are behavior-preserving and the risk is local.
- Stop only for public API changes, ambiguous intent, destructive actions, or refactors that are no longer clearly cleanup.

### 4. Refactor safely

Work in priority order from highest-signal to lowest-risk.

Before each file edit:

1. Re-read the current file state.
2. Confirm the cleanup metric being improved.
3. Search references before deleting or renaming anything shared.

Tooling guardrail:

- If an interactive shell session needs follow-up input and `write_stdin` reports that stdin is closed, restart with a fresh `exec_command` using `tty=true` once instead of continuing to poke the dead session.

Editing rules:

- Lock behavior first with existing tests when available.
- If behavior is not protected and cleanup is risky, add only the narrowest regression coverage needed to preserve current behavior.
- Prefer deletion over extraction.
- Reuse existing helpers before introducing new abstractions.
- Do not introduce or preserve redundant alias/forwarder wrappers such as `_name()` forwarding to `name()` or one-line pass-through accessors for the same concept unless a documented compatibility boundary requires them.
- Do not add dependencies.
- Do not broaden scope.
- Keep related edits in the same file together.

Forensic-followup rules:

- Treat the selected scope as forensic evidence, not as truth. Verify the cleanup did not leave drift in tests, imports, wrappers, or return contracts.
- If the scope is a branch diff, validate both branch-local cleanup patterns and cross-file fallout introduced across the branch.
- If the scope is the whole codebase, cluster by module or smell family and finish one cluster with verification before moving to the next.
- Search references before removing or moving anything that used to be re-exported.
- When a wrapper is removed, verify every new required argument is propagated at direct callers and tests.
- When a same-concept alias pair or pass-through forwarder is found, collapse it onto one canonical accessor instead of keeping both names alive unless an external compatibility contract requires otherwise.
- When a guard such as `getattr`, `hasattr`, or `None` fallback is removed, confirm the surrounding contract is now truly strict and canonical.
- When a refactor changes a return expression, check whether the concrete return type changed even if the value shape still passes shallow tests.
- Prefer to finish safe follow-up fixes in the same run instead of stopping at analysis.

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

For **Forensic-Followup**, also include:

- scope summary
- risk clusters
- follow-up fixes applied because of the forensic review

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

## Forensic-Followup Checklist

Before applying follow-up edits after a commit, branch diff, or codebase forensic pass, verify every answer is `yes`:

- Did you inspect the selected scope with the right inventory first: commit stats, branch diff stats, or repo hotspot inventory?
- Did you read every touched or clustered file that could contain fallout?
- Did you check importers, tests, and re-export surfaces for moved or removed symbols?
- Did you check for concrete return-type drift such as `defaultdict` vs `dict`?
- Did you verify wrapper removal propagated required arguments at every call site?
- Did you verify removed guards were replaced by an intentional strict contract rather than wishful thinking?
- Are you still doing behavior-preserving cleanup rather than silently redesigning APIs?

## Boundaries

Do not use this skill to:

- add features
- do formatting-only cleanup
- upgrade dependencies
- rewrite architecture
- redesign public APIs
- run speculative rewrites with unclear payoff
