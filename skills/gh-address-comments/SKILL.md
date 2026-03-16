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
- When the user already has final reply text and wants it posted to an existing review thread, identify the target review `comment_id` first:
  - Preferred: use the inline review thread/comment ids returned by `scripts/fetch_comments.py`.
  - If needed, confirm with gh directly: `GH_FORCE_TTY=0 GIT_TERMINAL_PROMPT=0 GH_PAGER=cat gh api repos/{owner}/{repo}/pulls/{pr}/comments --paginate`

## 2) Ask the user for clarification
- Default path: number all the review threads and comments, summarize the required fix briefly, and ask which numbered comments should be addressed.
- Fast path: if the user already provides final reply text plus a target review comment/thread, skip the drafting loop and move directly to posting.

## 3) If user chooses comments
- Apply fixes for the selected comments.
- If the planned reply says or implies that a code fix has already been applied, do not post yet. First verify the change exists locally, then commit it, then push it to the PR branch.
- If the commit or push is still pending, stop before posting and tell the user that the push is still pending.

## 4) Fast path: drafted reply -> post to existing review thread
Use this when the user already has final comment text and wants it uploaded to a specific PR review comment thread.

1. Find the target PR with Step 0 and keep the resolved `owner/repo` + PR number.
2. Identify the target review `comment_id` from `scripts/fetch_comments.py` output or `gh api repos/{owner}/{repo}/pulls/{pr}/comments --paginate`.
3. Decide which posting path applies:
   - **Non-code-claim fast path:** if the user supplied final reply text and it does not claim that a fix/change has already been applied, do not redraft it; preserve the final Korean text exactly as provided, including line breaks.
   - **Applied-fix path:** if the reply says or implies that a fix/change has already been applied, verify the code change is present locally, committed, and pushed to the PR branch before posting. If commit or push has not happened yet, stop and tell the user that push is still pending.
4. Post the reply non-interactively with the required gh env only after the applicable checks above pass:
   ```bash
   GH_FORCE_TTY=0 GIT_TERMINAL_PROMPT=0 GH_PAGER=cat \
   gh api \
     repos/{owner}/{repo}/pulls/{pr}/comments/{comment_id}/replies \
     --method POST \
     --raw-field body="$(cat /absolute/path/to/reply.txt)"
   ```
   - This `gh api repos/{owner}/{repo}/pulls/{pr}/comments/{comment_id}/replies` pattern is the preferred reliable method for replying to an existing PR review comment thread.
   - For short single-line replies, `--raw-field body='final reply text'` is acceptable.
   - Keep the env prefix on every gh retry to avoid interactive TTY failures.
5. Report the posted reply target (`owner/repo`, PR number, review comment id) and the API result. If the API returns a reply URL or id, include it in the handoff.

## Operational Noise Controls

- If any `--json` flag is rejected by the local tool version, rerun without `--json` and parse plain-text output.
- If `gh` reports `Error: unknown flag: --repo`, rerun without `--repo` and pass `OWNER/REPO` as positional repository argument.
- If `jq` parsing fails (`jq: parse error`), rerun without `--jq`/`--json` and continue in text-parsing mode.
- If PR resolution fails with `unable to resolve PR from current branch`, fallback to `gh pr list --author @me --state open --limit 20` and continue with explicit PR choice.
- Before writing temp/output files, verify destination parent directory with `test -w`; if not writable, fallback to repo root or `$CODEX_HOME`.
- Keep path filtering tight: run `rg --files -g 'fetch_comments.py'` before broad searches.

Notes:
- If gh hits auth/rate issues mid-run, prompt the user to re-authenticate with `gh auth login`, then retry.
