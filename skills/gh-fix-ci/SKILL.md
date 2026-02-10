---
name: "gh-fix-ci"
description: "Use when a user asks to debug or fix failing GitHub PR checks that run in GitHub Actions; use `gh` to inspect checks and logs, summarize failure context, draft a fix plan, and implement only after explicit approval. Treat external providers (for example Buildkite) as out of scope and report only the details URL."
---


# Gh Pr Checks Plan Fix

## Overview

Use gh to locate failing PR checks, fetch GitHub Actions logs for actionable failures, summarize the failure snippet, then propose a fix plan and implement after explicit approval.
- Draft the fix plan inline in this skill and request approval before implementing.

Prereq:
- Ensure `gh` exists first: `command -v gh`.
- Before git-scoped commands, verify repo context: `git rev-parse --is-inside-work-tree`.
- Authenticate with GitHub CLI once (for example, `gh auth login`) and confirm with `gh auth status`.
- Use non-interactive gh env for all gh calls: `GH_FORCE_TTY=0 GIT_TERMINAL_PROMPT=0 GH_PAGER=cat`.
- If a `gh` command fails with `Error: could not open a new TTY`, rerun once with the same env and then report failure.

## Inputs

- `repo`: path inside the repo (default `.`)
- `pr`: PR number or URL (optional; defaults to current branch PR)
- `gh_repo`: GitHub repo slug `owner/repo` override (optional)
- `gh` authentication for the repo host

## Quick start

- `python "<path-to-skill>/scripts/inspect_pr_checks.py" --repo "." --pr "<number-or-url>"`
- `python "<path-to-skill>/scripts/inspect_pr_checks.py" --repo "."` (auto current PR, then fork-upstream fallback)
- `python "<path-to-skill>/scripts/inspect_pr_checks.py" --repo "." --gh-repo "owner/repo" --pr "123"`
- Add `--json` if you want machine-friendly output for summarization.

## Workflow

1. Verify gh authentication.
   - Run `gh auth status` in the repo.
   - If unauthenticated, ask the user to run `gh auth login` (ensuring repo + workflow scopes) before proceeding.
2. Resolve the PR.
   - Preferred auto path:
     - Try current repo PR first: `gh pr view --json number,url`
     - If not found and current repo is a fork, resolve parent repo and search by head branch:
       - `gh repo view --json nameWithOwner,isFork,parent`
       - `gh pr list --repo <parent-owner>/<parent-repo> --state open --head <fork-owner>:<current-branch> --json number,url,updatedAt`
       - If `--head <owner>:<branch>` returns empty on your gh version, fallback:
         - `gh pr list --repo <parent-owner>/<parent-repo> --state open --search "head:<current-branch> author:<fork-owner>" --json number,url,updatedAt`
   - If user provides PR number or URL, use it directly.
   - Always carry `target_repo` + `target_pr` for all subsequent `gh` commands.
3. Inspect failing checks (GitHub Actions only).
   - Preferred: run the bundled script (handles gh field drift and job-log fallbacks):
     - `python "<path-to-skill>/scripts/inspect_pr_checks.py" --repo "." --pr "<number-or-url>"`
     - Auto/fork-aware: `python "<path-to-skill>/scripts/inspect_pr_checks.py" --repo "."`
     - Override repo: `python "<path-to-skill>/scripts/inspect_pr_checks.py" --repo "." --gh-repo "<owner/repo>" --pr "123"`
     - Add `--json` for machine-friendly output.
     - If `--json` is rejected by a tool/version, rerun without `--json` and parse text output.
   - Manual fallback:
     - `gh pr checks <pr> --repo <target_repo> --json name,state,bucket,link,startedAt,completedAt,workflow`
       - If a field is rejected, rerun with the available fields reported by `gh`.
     - For each failing check, extract the run id from `detailsUrl` and run:
       - `gh run view <run_id> --repo <target_repo> --json name,workflowName,conclusion,status,url,event,headBranch,headSha`
       - `gh run view <run_id> --repo <target_repo> --log`
     - If the run log says it is still in progress, fetch job logs directly:
       - `gh api "/repos/<target_repo>/actions/jobs/<job_id>/logs" > "<path>"`
4. Scope non-GitHub Actions checks.
   - If `detailsUrl` is not a GitHub Actions run, label it as external and only report the URL.
   - Do not attempt Buildkite or other providers; keep the workflow lean.
5. Summarize failures for the user.
   - Provide the failing check name, run URL (if any), and a concise log snippet.
   - Call out missing logs explicitly.
   - If workflow file lookup is needed, use path filtering first:
     - `test -d .github/workflows || true`
     - `rg --files .github/workflows -g '*.yml' -g '*.yaml'`
     - If no file matches expected name, continue with gh run metadata and do not fail on local path assumptions.
6. Create a plan.
   - Draft a concise inline plan with: failure cause, proposed fix, tests to run, rollback note.
   - Request explicit approval before implementation.
7. Implement after approval.
   - Apply the approved plan, summarize diffs/tests, and ask about opening a PR.
8. Recheck status.
   - After changes, suggest re-running the relevant tests and `gh pr checks` to confirm.

## Sub-Agent Delegation (Scenario-Bound)
- If CI forensic collection is heavy (large multi-run logs or repeated extraction), optionally delegate a bounded log-mining pass to `codex-exec-sub-agent`.
- Keep fix-plan gating and final decisioning in this skill; sub-agent output is supporting evidence.
- Use prompt files and explicit timeout to keep nested execution deterministic.

```bash
~/.codex/skills/codex-exec-sub-agent/scripts/run.sh --timeout-sec 600 --prompt-file /full/path/prompt.txt
```

## Delegation Boundaries

- This skill owns GitHub Actions failure inspection, log analysis, and fix-plan gating.
- `gh-address-comments` owns PR review comment response workflows.

## Bundled Resources

### scripts/inspect_pr_checks.py

Fetch failing PR checks, pull GitHub Actions logs, and extract a failure snippet. Exits non-zero when failures remain so it can be used in automation.

Usage examples:
- `python "<path-to-skill>/scripts/inspect_pr_checks.py" --repo "." --pr "123"`
- `python "<path-to-skill>/scripts/inspect_pr_checks.py" --repo "." --pr "https://github.com/org/repo/pull/123" --json`
- `python "<path-to-skill>/scripts/inspect_pr_checks.py" --repo "." --json` (fork-aware auto resolution)
- `python "<path-to-skill>/scripts/inspect_pr_checks.py" --repo "." --gh-repo "org/repo" --pr "123"`
- `python "<path-to-skill>/scripts/inspect_pr_checks.py" --repo "." --max-lines 200 --context 40`
