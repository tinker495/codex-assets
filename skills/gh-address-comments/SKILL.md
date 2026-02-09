---
name: gh-address-comments
description: Help address review/issue comments on the open GitHub PR for the current branch using gh CLI; verify gh auth first and prompt the user to authenticate if not logged in.
metadata:
  short-description: Address comments in a GitHub PR review
---

# PR Comment Handler

Guide to find the open PR for the current branch and address its comments with gh CLI. Run all `gh` commands with elevated network access.

Prereq: ensure `gh` is authenticated (for example, run `gh auth login` once), then run `gh auth status` with escalated permissions (include workflow/repo scopes) so `gh` commands succeed. If sandboxing blocks `gh auth status`, rerun it with `sandbox_permissions=require_escalated`.

## 0) Resolve target PR (fork-aware)
- Preferred: run `scripts/fetch_comments.py` directly (auto-resolves current repo PR, then fork upstream parent PR by head branch when needed).
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
