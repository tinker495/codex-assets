# Stacked PR Reference

## Stack Shape

```text
main
  -> feat/domain-models
    -> feat/service-rules
      -> feat/api-endpoints
```

The bottom branch is closest to trunk. Each branch's PR base should be the branch below it.

## Preflight Commands

```bash
git status --short
git branch --show-current
git remote -v
gh auth status
gh extension list
gh stack --help
gh stack view --json
```

Install or update the extension when missing or stale:

```bash
gh extension install github/gh-stack
gh extension list
gh extension upgrade --all
```

`gh-stack` requires GitHub CLI v2.0+ and GitHub Stacked PRs must be enabled for the target repository. If the repository cannot create a GitHub Stack, `submit` can fail even when local branch stacking works.

If `gh` cannot infer the repository, run stack commands as:

```bash
GH_REPO=owner/repo gh stack view --json
```

## Create And Add Layers

```bash
gh stack init --base main feat/domain-models feat/service-rules feat/api-endpoints
gh stack init --base develop feat/domain-models feat/service-rules
gh stack init --base main -p feat domain-models service-rules api-endpoints
gh stack add feat/frontend # no prefix stack
gh stack add frontend      # prefix stack created with -p feat
```

With `-p feat`, pass only suffixes to `gh stack add`:

```bash
gh stack add api-endpoints      # creates feat/api-endpoints
gh stack add feat/api-endpoints # wrong with prefix: creates feat/feat/api-endpoints
```

Add and commit in one command only when the staged/all-files behavior is intended:

```bash
gh stack add -Am "Add API endpoints" feat/api-endpoints # no prefix stack
gh stack add -Am "Add API endpoints" api-endpoints      # prefix stack
gh stack add -um "Update service rules" service-rules   # prefix stack
```

## Navigation

```bash
gh stack checkout feat/service-rules
gh stack bottom
gh stack up
gh stack down
gh stack top
gh stack trunk
```

## Submit And Edit PRs

```bash
gh stack submit --auto
gh stack submit --auto --remote origin
gh stack submit --auto --open
gh stack view --json
gh pr edit <number> --title "<title>" --body-file <file>
```

Use `--open` only when the user wants PRs ready for review. Without that request, preserve the default PR readiness behavior.

`--auto` title behavior:

- Single-commit branch: commit subject becomes PR title; commit body becomes PR body.
- Multi-commit branch: branch name is humanized into the PR title.

`gh stack push` only pushes branches. It does not create or update PRs; use `submit` for PR creation/update.

## Rebase And Push

For review changes on a lower layer:

```bash
gh stack checkout feat/domain-models
# edit, test, commit
gh stack rebase --upstack
gh stack push
gh stack view --json
```

With multiple remotes:

```bash
gh stack rebase --upstack --remote origin
gh stack push --remote origin
```

For a full refresh:

```bash
gh stack rebase
gh stack push
```

If conflicts occur:

```bash
git status --short
# resolve only reported conflict files
git add <resolved-files>
gh stack rebase --continue
```

Abort only to restore the stack to the pre-rebase state:

```bash
gh stack rebase --abort
```

`gh stack rebase` automatically handles already-merged lower PRs by replaying remaining commits onto the merge target.

## Sync And Prune

```bash
gh stack sync
gh stack sync --remote origin
gh stack view --json
```

`sync` fetches, fast-forwards trunk when possible, cascade-rebases branches when needed, pushes active branches, syncs PR state, and only prunes merged branches automatically when `--prune` is passed in a non-interactive environment.

Use pruning only when local merged branch deletion is in scope:

```bash
gh stack sync --prune
```

## Link Existing Branches Or PRs

```bash
gh stack link --base main feat/domain-models feat/service-rules feat/api-endpoints
gh stack link 101 102 103
gh stack link --base develop --open branch-a branch-b branch-c
```

`gh stack link` does not create local stack tracking metadata. It is useful when branches are managed by another tool or only GitHub PR stack linkage is needed.

Arguments are bottom-to-top. Branch arguments are pushed automatically, branches without open PRs get new PRs, and existing PRs with mismatched base branches are corrected. Updates are additive; existing PRs are not removed from a stack.

## Checkout And Local Metadata

```bash
gh stack checkout 42
gh stack checkout feature-auth
gh stack unstack --local
```

Checking out by PR number fetches the GitHub stack and sets it up locally. Checking out by branch resolves only local stack metadata. If a PR checkout reports an incompatible local stack composition, remove only local tracking with `gh stack unstack --local` from a checked-out stack branch, then retry. Do not run plain `gh stack unstack` unless deleting the GitHub stack is explicitly in scope.

Local tracking files live under `.git/gh-stack`; interrupted rebase state lives under `.git/gh-stack-rebase-state`. Do not edit these files manually.

## View JSON Fields

```bash
gh stack view --json
```

Use JSON output to inspect:

- `trunk`, `prefix`, `currentBranch`
- per-branch `name`, `head`, `base`, `isCurrent`, `isMerged`, `needsRebase`
- `pr.number`, `pr.url`, `pr.state` when a PR exists

Treat `needsRebase: true` as a signal to run `gh stack rebase` or the narrower `--upstack`/`--downstack` form.

## Exit Codes To Route

- `2`: not in a stack or stack not found; inspect branch and local stack metadata.
- `3`: rebase conflict; resolve files, stage them, then run `gh stack rebase --continue`.
- `5`: invalid arguments or flags; fix the command shape.
- `6`: branch belongs to multiple stacks; check out a non-shared branch or disambiguate through local metadata cleanup.
- `7`: rebase already in progress; continue or abort the active rebase.
- `8`: stack locked by another process; wait, then retry after verifying no command is still running.
- `9`: GitHub Stacked PRs unavailable for the repository; report a capability blocker instead of creating unstacked PRs silently.
