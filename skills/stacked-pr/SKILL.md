---
name: stacked-pr
description: Guides agents through creating, maintaining, and publishing GitHub stacked pull requests with the gh-stack CLI. Use when the user mentions stacked PRs, gh stack, dependent PR chains, splitting a large change into reviewable PR layers, rebase upstack/downstack, or submitting/syncing a PR stack.
---

# Stacked PR

Use this skill to turn one large change into a bottom-to-top chain of small GitHub PRs, then keep the chain rebased and published with `gh stack`.

## Quick Start

```bash
gh extension install github/gh-stack
git config rerere.enabled true
git config remote.pushDefault origin
gh stack init --base main -p feat data-models service api
gh stack checkout feat/data-models  # edit, test, commit
gh stack checkout feat/service      # edit, test, commit
gh stack checkout feat/api          # edit, test, commit
gh stack submit --auto --remote origin
gh stack view --json
```

## When To Use

Use stacked PRs when the work has dependent review layers, for example:

- schema/model -> service/domain logic -> API -> UI
- interface/contract -> implementation -> call-site migration
- behavior lock -> refactor core -> cleanup callers

Prefer one normal PR for a small bug fix, a narrow feature, or unrelated changes that should not depend on each other.

## Workflow

1. Read applicable `AGENTS.md` files, then inspect `git status --short`, current branch, remotes, `gh auth status`, and `gh extension list`.
2. Verify `gh stack` live in the target repository with `gh stack --help`; if repository inference fails, prefix commands with `GH_REPO=owner/repo`.
3. Plan branches from bottom to top. The bottom branch reviews against trunk; every higher branch reviews against the branch below it.
4. Preconfigure prompt-prone defaults when safe:
   ```bash
   git config rerere.enabled true
   git config remote.pushDefault origin
   ```
5. Create or adopt the stack non-interactively:
   ```bash
   gh stack init --base main -p feat domain-models service-rules api-endpoints
   ```
6. Work one layer at a time: `gh stack checkout <branch>`, edit only that layer, run targeted validation, then commit.
7. Submit/update PRs only when publishing is in scope:
   ```bash
   gh stack submit --auto --remote origin
   gh stack view --json
   ```
8. After lower-layer review changes, rebase and push the affected upper stack:
   ```bash
   gh stack rebase --upstack --remote origin
   gh stack push --remote origin
   gh stack view --json
   ```
9. After merges, use `gh stack sync --remote origin`; use `--prune` only when deleting merged local stack branches is in scope.

## Existing Branches Or PRs

If branches or PRs already exist and local `gh stack` metadata is not needed, link them bottom-to-top:

```bash
gh stack link --base main feat/domain-models feat/service-rules feat/api-endpoints
gh stack link 101 102 103
```

## Agent Guardrails

- Always provide branch names or PR numbers to `init`, `add`, and `checkout`; omitted arguments can prompt.
- Prefer prefix stacks, but pass only the suffix to `gh stack add` when a prefix is set.
- Always use `gh stack submit --auto` and `gh stack view --json`; plain `submit` or `view` can prompt or open a TUI.
- Use `--remote <name>` for `push`, `submit`, `sync`, and `link` when multiple remotes exist; also set `git config remote.pushDefault origin`.
- Avoid `gh stack modify` and argument-less `gh stack checkout` in non-interactive agent sessions because they open interactive UIs.
- Prefer `gh stack push` over manual force pushes; it pushes the whole stack with stack-aware safety.
- Treat `gh stack submit` failure for unavailable stacked PRs as a capability blocker; do not silently fall back to unstacked PRs.
- Do not use destructive git commands to reshape a stack unless the user explicitly requested that exact operation.
- Keep PR layers small enough that each reviewer can understand the delta against the branch below.
- Verify completion with `gh stack view --json`, `git status --short`, and relevant tests before reporting done.

## Reference

For command recipes, conflict handling, PR body edits, and compact branch creation, see [REFERENCE.md](REFERENCE.md).
