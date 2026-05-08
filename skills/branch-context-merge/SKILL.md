---
name: branch-context-merge
description: Merge origin/main into the current branch while preserving branch-specific codebase context, intent, and architectural ownership decisions. Use when the user asks to merge/sync main into a feature branch, resolve conflicts without losing branch context, keep branch semantics during merge, or says Korean phrases like "브랜치 맥락 유지", "현재 브랜치에 origin/main 머지", or "컨플릭트 해소".
---

# Branch Context Merge

## Mission

Integrate `origin/main` into the current branch without flattening the branch's intent.
This is stricter than a mechanical merge: collect branch context first, understand both sides of each conflict, preserve current-branch ownership/architecture decisions when still valid, absorb main's newer seams/contracts, then verify with evidence.

## Quick start

```bash
git rev-parse --is-inside-work-tree
git status --short --branch
git fetch origin main
git merge origin/main
```

If conflicts occur, resolve them only after reconstructing branch intent and main-side intent.
Do not use blanket `--ours` / `--theirs` resolution.

## Workflow

1. **Load context before merging**
   - Run `branch-onboarding-brief` first. Use its collector when available: `collect_branch_info.py --base origin/main --format json`.
   - Run `codebase-recon` when the user names it or when the merge touches high-risk/core areas.
   - Inspect actual changed files, not just commit titles. Use Probe/`omx explore` for symbols and ownership boundaries.
   - Record: branch name, fork point, commit list, changed files, top churn, code-grounded branch intent.

2. **Preflight safety**
   - Confirm inside a git work tree.
   - Confirm the current branch and upstream.
   - If `git status --porcelain` is non-empty before merge, stop and ask one targeted question. Do not auto-stash, reset, or discard.
   - Fetch `origin main` immediately before merging.

3. **Merge**
   - Run `git merge origin/main`.
   - If clean, continue to validation.
   - If conflicted, list unresolved files with `git diff --name-only --diff-filter=U`.

4. **Resolve conflicts by semantic ownership**
   - For every conflict file, read applicable `AGENTS.md` ancestors and local module contracts.
   - Compare three views when needed: current branch (`:2:path`), main (`:3:path`), and working file.
   - Prefer main when it introduces newer shared seams, public contracts, or upstream integration points.
   - Prefer current branch when it encodes the branch's explicit ownership move, architecture guard, data-model invariant, or doc decision.
   - When both are valid, compose them: keep main's seam while rewriting imports/docs/tests to current branch canonical owner paths.
   - Rename/renumber docs instead of silently dropping either side when document IDs collide.
   - After each resolution, scan for conflict markers and stale owner/import paths.

5. **Stage and continue**
   - Stage only resolved files and intentional merge adjustments.
   - Continue with `git merge --continue`; use `GIT_EDITOR=true git merge --continue` in non-interactive shells.
   - If commit policy requires structured messages, amend the merge commit to the repo's commit protocol before pushing.

6. **Validate smallest sufficient proof**
   - Always run `git diff --check` before merge commit completion when possible.
   - Run import smoke checks for conflicted public seams.
   - Run architecture/boundary tests when conflicts touch ownership/import paths.
   - Run targeted tests for touched runtime areas.
   - Run docs checks when docs/AGENTS/specs changed.
   - Run full tests only when risk or user request justifies the cost.

7. **Post-merge evidence**
   - Confirm `origin/main` is an ancestor of `HEAD`.
   - Confirm the pre-merge branch HEAD is an ancestor of `HEAD`.
   - Confirm no conflict markers remain.
   - Report ahead/behind status. Do not push unless requested.

## Conflict decision checklist

- What was this branch trying to preserve?
- What newer contract did `origin/main` add?
- Which module owns the canonical type/function after both changes?
- Are compatibility facades still intended, or is this branch deleting stale paths?
- Which tests/docs encode the decision?
- Did the final import graph respect local `AGENTS.md` boundaries?

## Output contract

Put the merge outcome first, then include:

- branch, merge commit, parents, and push status
- conflict files and resolution strategy
- branch-context facts used for decisions
- validation commands and pass/fail results
- open risks and explicitly not-run checks

Ask the user only for destructive choices, dirty pre-merge state, or genuinely ambiguous branch intent.
