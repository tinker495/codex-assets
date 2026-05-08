---
name: reviewable-commit-split
description: Splits one large dirty Git working state into reviewable semantic local commits without rewriting existing branch history. Use when the user asks to split current working tree changes, 워킹 스테이트 분할커밋, 리뷰 가능한 커밋, semantic commit grouping, or staged/unstaged changes into a clean commit stack.
---

# Reviewable Commit Split

## Quick start

Run from the target repository root:

```bash
git rev-parse --is-inside-work-tree
git status --short
git diff --stat
git diff --cached --stat
```

Goal: convert current staged, unstaged, and relevant untracked changes into a small stack of local commits, each with one reviewable intent. Do not push, open PRs, amend old commits, reset away work, or rewrite existing history unless explicitly asked.

## Workflow

### 1. Preflight and preserve evidence

Capture evidence before changing the index:

```bash
ts=$(date +%Y%m%d-%H%M%S)
out=".codex_tmp/reviewable-commit-split/$ts"
mkdir -p "$out"
git status --short > "$out/status.txt"
git diff > "$out/unstaged.patch"
git diff --cached > "$out/staged.patch"
git ls-files --others --exclude-standard > "$out/untracked.txt"
git diff --stat > "$out/unstaged.stat"
git diff --cached --stat > "$out/staged.stat"
```

Rules:
- Record current branch, `HEAD`, upstream/base if relevant, and full dirty state.
- Treat existing staging as temporary implementation state, not a semantic boundary, unless the user requested otherwise.
- Never use `git reset --hard`, `git clean`, `git checkout -- .`, or broad worktree `git restore`.

### 2. Plan semantic clusters before staging

- Read changed files and their governing `AGENTS.md` contracts.
- Cluster by code intent, not file extension, old staging, or editing order.
- If the user gives an exact commit count, satisfy it using real semantic boundaries; otherwise choose the smallest natural coherent set.
- Keep dependency order: contracts/models first, core behavior next, UI/adapters after core, docs/tests with the behavior they explain or prove.
- No “misc”, “cleanup”, or “follow-up” buckets. Each cluster needs: “This commit is reviewable because ...”.

### 3. Stage one cluster at a time

```bash
git reset
git add path/to/whole_file
git add -p path/to/mixed_file
git add path/to/read_untracked_file
```

Before each commit:

```bash
git diff --cached --stat
git diff --cached --check
git diff --cached
```

Commit only when the staged diff has one coherent review unit. Use the repository commit-message contract; if Lore is in scope, write an intent-first message with useful `Constraint`, `Rejected`, `Confidence`, `Scope-risk`, `Directive`, `Tested`, and `Not-tested` trailers.

### 4. Reviewability rules

A commit is reviewable when:
- it has one behavioral, structural, or documentation intent;
- tests/fixtures travel with the behavior they validate unless they are an independent test-harness change;
- generated files are isolated or clearly paired with their source change;
- mechanical moves/renames are not mixed with semantic edits unless inseparable;
- same-file hunks are split with `git add -p` when they belong to different intents;
- it can be explained, reviewed, and reverted independently without surprising unrelated changes.

If staged content violates the rules, unstage without touching the worktree:

```bash
git restore --staged path/to/file
# or reset staging only
git reset
```

### 5. Validate and report

After the final planned commit:

```bash
git status --short
git log --oneline --decorate -n <commit-count>
```

Run the smallest fresh validation that proves the stack is safe: targeted tests first, then lint/typecheck/docs checks when touched files or repo contracts require them. If validation cannot run or fails for a known unrelated reason, report the exact command, exit status, and residual risk.

Stop when the dirty working state is fully converted into planned local commits or only intentionally deferred files remain. Final report: commit SHAs, intent boundaries, changed-file coverage, validation evidence, and remaining risks.
