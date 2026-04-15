---
name: branch-archive-rechunk-rebase
description: "Rebuild the current branch history through a fixed git workflow: onboard the branch, archive the full pre-rewrite state to a legacy branch, regroup the total branch diff into exactly N logical commits centered on the branch's real semantic changes rather than the old commit boundaries, and rebase the rewritten branch onto origin/main when it is not already directly based on main. Use when asked to clean up a noisy feature branch, reorganize fragmented semantic changes into N commits, archive legacy history before rewriting, or restack current work onto main without losing recoverability."
---

# Branch Archive Rechunk Rebase

## Overview

Run a deterministic history-rewrite workflow for the current branch. Treat rechunking as semantic branch reconstruction: the goal is not to preserve or merely merge existing commits, but to rebuild the branch around the fragmented semantic changes that matter now. Collect onboarding context first, create a recoverable legacy branch before any rewrite, collapse the branch delta back to its base, rebuild it into exactly N intent-based commits, then rebase onto `origin/main` only when the rewritten branch is not already stacked on it.

Assume local-only history rewriting by default. Do not push, force-push, or delete archive branches unless the user explicitly asks.

## Workflow

### 1. Run onboarding first

Delegate branch diff collection and risk briefing to `branch-onboarding-brief` before touching history. The onboarding output must be code-grounded: it must include actual changed-file reading and AST-oriented inspection of risky modules, not just git metadata.

Capture and keep:
- current branch name
- short commit log
- changed areas and file count
- net LOC summary
- risky or cross-cutting files
- code-grounded findings from changed files and symbols actually inspected

Do not duplicate the onboarding collector inside this skill.

### 2. Run preflight checks

Before any destructive command, verify repository state once:

```bash
git rev-parse --is-inside-work-tree
git branch --show-current
git status --short
git fetch origin main
```

Require all of the following before rewriting:
- `HEAD` is attached to a named branch
- working tree and index are clean
- `origin/main` resolves successfully
- the user supplied `N` and `N` is a positive integer

If `git status --short` is non-empty, stop and report the blocker. Do not auto-stash, reset, or discard local edits.

Capture stable refs once:

```bash
original_branch=$(git branch --show-current)
original_head=$(git rev-parse HEAD)
main_tip=$(git rev-parse origin/main)
base_commit=$(git merge-base "$original_head" "$main_tip")
```

Treat `base_commit != main_tip` as “not directly based on current main”, which means a rebase is required after regrouping.

### 3. Archive the legacy branch before rewriting

Create a local archive branch from the untouched original tip before any reset or rebase.

```bash
ts=$(date +%Y%m%d-%H%M%S)
safe_branch=${original_branch//\//-}
archive_branch="legacy/${safe_branch}-${ts}"
git branch "$archive_branch" "$original_head"
```

Rules:
- keep the archive branch local unless the user explicitly asks to publish it
- never rewrite or delete the archive branch during the same run
- if the generated name already exists, append `-1`, `-2`, and so on until unique

### 4. Build the N-commit clustering plan before resetting

Inspect the total branch delta first:

```bash
git log --oneline "${base_commit}..${original_head}"
git diff --name-status "${base_commit}...${original_head}"
git diff --stat "${base_commit}...${original_head}"
```

Before deriving clusters, inspect actual changed code on the branch. Git history alone is insufficient for reliable rechunking, because the target branch should express consolidated semantic changes rather than a cleaned-up copy of the old commit boundaries.

Minimum clustering-grounding contract:
- start from the changed-file list from onboarding and `git diff ... --name-status`
- read all risky or cross-cutting changed files and any file touched by multiple original commits or candidate clusters
- use `probe symbols`, `probe extract`, and `probe query` on changed Python modules to understand the real function/class boundaries
- when commit subjects disagree with code evidence, trust the changed-file code evidence
- record 1-3 anchor files or symbols for each planned cluster

Suggested commands:
```bash
probe symbols src/stowage/planner/spp/pipeline.py
probe extract src/stowage/planner/spp/pipeline.py#run_loading_spp_pipeline_result
probe query "class $NAME: $$$" src/stowage/planner/spp --language python
```

Then derive exactly `N` clusters using `references/commit-clustering.md`.

Clustering rules:
- group by code intent proven by changed-file inspection first, not by file extension or commit subject alone
- treat original commits as raw evidence only; do not merge or preserve them mechanically when the semantic change boundaries should be redrawn
- keep schema/model changes ahead of dependent runtime changes
- keep tests with the runtime change they prove unless the test work is a standalone intent
- isolate risky cross-cutting rewrites into their own cluster when possible
- inspect same-file overlaps structurally before deciding whether clusters should merge or split
- preserve dependency order so every intermediate commit is coherent

Exact-`N` contract:
- if natural clusters are more than `N`, merge the closest related clusters and state the merge rationale
- if natural clusters are fewer than `N`, split only along real sub-intents or hunk boundaries
- do not fabricate meaningless micro-commits just to hit the number

### 5. Collapse the branch back to its base

After the clustering plan is stable, collapse the branch history while keeping the full diff in the working tree:

```bash
git reset --soft "$base_commit"
git reset
```

At this point:
- `HEAD` points at `base_commit`
- all branch changes remain in the working tree
- nothing is staged

### 6. Recreate exactly N commits

Stage each planned cluster in dependency order and commit immediately.

For file-scoped clusters:

```bash
git add path/to/file_a path/to/file_b
git commit -m "<intent-focused message>"
```

When a single file belongs to multiple clusters, choose the least-lossy replay method first.

For small overlaps, split by hunk:

```bash
git add -p path/to/file
```

For heavy overlaps across multiple original commits, replay the file state commit-by-commit instead of hand-splitting every hunk:

```bash
git restore --source <old-commit> --staged --worktree -- path/to/file_a path/to/file_b
git commit -m "<intent-focused message>"
```

If the later cluster deletes a file that an earlier replay restored, remove it explicitly in the later cluster:

```bash
git rm path/to/file
git commit -m "<intent-focused message>"
```

Use commit-state replay when it is easier to reproduce the original branch intent by restoring exact file states from old commits than by manually curating patches with `git add -p`.

After each commit:
- verify only the intended paths or hunks were included
- keep commit messages intent-focused and reviewable
- prefer the smallest coherent unit that another engineer could revert independently

Before moving on, confirm the remaining diff still matches the unfinished plan:

```bash
git status --short
git diff --stat
```

After the Nth commit, require a clean tree:

```bash
git status --short
```

If changes remain, the regrouping is incomplete.

### 7. Rebase onto main only when needed

If `base_commit` already equals `main_tip`, skip rebase.

Otherwise, rebase the rewritten stack onto `origin/main`:

```bash
git rebase origin/main
```

If conflicts appear:

```bash
git diff --name-only --diff-filter=U
```

Resolve conflicts intentionally, then continue with:

```bash
git add <resolved-files>
git rebase --continue
```

If the shell blocks on editor launch, retry with:

```bash
GIT_EDITOR=true git rebase --continue
```

Do not use `git rebase --skip` or `git rebase --abort` unless the user explicitly asks or the workflow becomes unrecoverable.

### 8. Validate the rewritten history

Report the rebuilt stack first:

```bash
git log --oneline --decorate -n "$((N + 5))"
```

Validation rules:
- if no rebase happened, prefer direct tree equality against the archive branch
- if rebase happened, compare old-vs-new intent with `git range-diff`

Suggested checks:

```bash
git diff --exit-code "$archive_branch" HEAD
git range-diff "${base_commit}..${archive_branch}" "origin/main..HEAD"
```

Interpretation:
- `git diff --exit-code` is only valid as a strict equality check when rebase was skipped
- `git range-diff` is the primary post-rebase proof that the branch intent survived the rewrite

Include in the final handoff:
- onboarding summary
- archive branch name
- requested `N` and delivered commit count
- cluster titles and ordering rationale
- code-grounding evidence used for clustering (key changed files / symbols inspected)
- whether rebase was skipped or executed
- validation commands actually run and their results
- any remaining risks, especially around hunk-splitting or conflict resolution

## Operational guardrails

- Treat the archive branch as the rollback point for the entire run.
- Optimize for a reviewable semantic branch, not for maximum fidelity to the original commit graph.
- Re-read `git status --short` before every destructive git command.
- Prefer path-scoped staging first; use `git add -p` only when the same file truly spans multiple intents. If a file appears in multiple candidate clusters, inspect it structurally with `probe` before choosing between split-by-hunk and commit-state replay.
- If several planned clusters touch the same file, prefer deterministic `git restore --source <commit>` replay over fragile repeated hunk surgery.
- Do not mix mechanical formatting with semantic changes unless the formatting is inseparable from the semantic edit.
- Do not finalize the cluster plan until representative changed files and risky symbols have been read directly.
- Keep docs-only or test-only commits separate only when they are independently meaningful.
- If the branch contains generated files, classify them with the source change they derive from.

## Cross-skill usage

- `branch-onboarding-brief`: mandatory before any rewrite.
- `main-merge`: do not call for this workflow; this skill performs rebase, not merge.
- `code-health`: use only when regrouping exposes unusually large or risky non-test churn.

## Resources

- `references/commit-clustering.md`: heuristics for turning one branch diff into exactly N coherent commits.
