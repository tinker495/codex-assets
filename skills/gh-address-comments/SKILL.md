---
name: gh-address-comments
description: Help address review/issue comments on the open GitHub PR for the current branch using gh CLI; verify gh auth first and prompt the user to authenticate if not logged in.
metadata:
  short-description: Address comments in a GitHub PR review
---

# PR Comment Handler

Guide to find the open PR for the current branch and address its comments with gh CLI.

Prereq:
- Ensure `gh` exists first: `command -v gh`.
- Before running git-scoped commands, verify repo context: `git rev-parse --is-inside-work-tree`.
- Use non-interactive gh env for all gh calls: `GH_FORCE_TTY=0 GIT_TERMINAL_PROMPT=0 GH_PAGER=cat`.
- If any `gh` call still fails with `Error: could not open a new TTY`, rerun once with the same env and then report failure.

## 0) Resolve target PR (fork-aware)
- Preferred: run `scripts/fetch_comments.py` directly (auto-resolves current repo PR, then fork upstream parent PR by head branch when needed).
- Path guardrail (required, search-as-discovery):
  - First verify local script path: `test -f scripts/fetch_comments.py`.
  - If missing, search candidate paths before fallback: `rg --files -g 'fetch_comments.py'`.
  - If found, run the first exact path.
  - If still missing, fallback to bundled absolute path: `python /Users/mrx-ksjung/.codex/skills/gh-address-comments/scripts/fetch_comments.py`.
  - If all script paths are missing, switch to gh-only discovery:
    - `gh pr view --json number,url`
    - `gh pr list --state open --search "author:@me" --json number,url,updatedAt`
- Optional overrides:
  - `python scripts/fetch_comments.py --repo "." --pr "123"`
  - `python scripts/fetch_comments.py --repo "." --pr "https://github.com/org/repo/pull/123"`
  - `python scripts/fetch_comments.py --repo "." --gh-repo "owner/repo" --pr "123"`
- If auto resolution finds no PR in current repo and no matching upstream PR, report that explicitly and stop.

## 1) Inspect comments needing attention
- Run `scripts/fetch_comments.py` and collect:
  - conversation comments
  - reviews
  - inline review threads
  - `resolution` metadata (`repo`, `pr`, `source`, `url`)

## 2) Ask the user for clarification
- Number all the review threads and comments and provide a short summary of what would be required to apply a fix for it
- Ask the user which numbered comments should be addressed

## 3) If user chooses comments
- Apply fixes for the selected comments

Notes:
- If gh hits auth/rate issues mid-run, prompt the user to re-authenticate with `gh auth login`, then retry.
