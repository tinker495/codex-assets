---
name: gh-fix-review-comments
description: "Address open GitHub PR review feedback end-to-end when the user wants the full workflow: inspect unresolved review comments on the current branch PR, judge whether each comment is valid, apply code changes when needed, run verification, commit, push, reply on the review thread, and resolve it. Use for requests like '리뷰 코멘트 반영하고 커밋/푸시/답글/리솔브', 'address PR feedback end to end', or 'fix the review comments and resolve them'."
---

# GH Fix Review Comments

Use this skill for the full PR-feedback execution loop, not for comment listing only.
For comment discovery, PR resolution, reply posting, and thread resolution mechanics, reuse the workflow and guardrails from `$gh-address-comments`.

## Preconditions

- Ensure `gh` exists: `command -v gh`
- Ensure the current directory is a git repo: `git rev-parse --is-inside-work-tree`
- Ensure `gh` auth is active: `GH_FORCE_TTY=0 GIT_TERMINAL_PROMPT=0 GH_PAGER=cat gh auth status`
- Use the non-interactive env prefix on every `gh` call:
  - `GH_FORCE_TTY=0 GIT_TERMINAL_PROMPT=0 GH_PAGER=cat`

If auth is missing, stop and tell the user to run `gh auth login`.

## Workflow

1. Resolve the target PR and unresolved review threads.
   - Prefer the same path as `$gh-address-comments`:
     - local `scripts/fetch_comments.py` if present
     - otherwise `/Users/mrx-ksjung/.codex/skills/gh-address-comments/scripts/fetch_comments.py`
   - Collect PR number, repo, unresolved review threads, and inline `rest_id` values.

2. Summarize unresolved comments and choose targets.
   - If the user already specified which comments to address, use that selection.
   - Otherwise number unresolved threads, summarize each requested change briefly, and ask which ones to handle.

3. Evaluate each selected comment before changing code.
   - Read the referenced code and check whether the comment is valid.
   - If the comment is not valid, do not make speculative edits.
   - Draft a concise reply explaining why the current behavior is intentional or why the comment does not apply.

4. If the comment is valid, implement the fix.
   - Make the smallest change that addresses the review point directly.
   - Do not broaden scope unless the fix requires it.
   - Keep existing repo conventions and AGENTS.md rules.
   - If multiple selected comments need disjoint edits, batch them only when one commit still reads clearly.

5. Verify before claiming the fix is done.
   - Run targeted tests first.
   - Run broader verification required by the repo or the touched area.
   - At minimum, ensure the checks referenced in the planned reply actually passed.
   - If verification fails, continue iterating before replying.

6. Commit and push before posting any reply that says the fix is applied.
   - Stage only the intended files.
   - Follow repo commit rules if the repo defines them.
   - Push the current branch to the PR remote.
   - If push fails, do not post a 'fixed' reply yet.

7. Reply on the review thread.
   - Use the inline review comment `rest_id` when available.
   - Preserve the final Korean reply text exactly.
   - Include what changed and what verification ran.
   - Mention the pushed commit hash when useful.

8. Resolve the thread after the reply is posted.
   - Resolve only after the applicable fix is committed and pushed, or after posting the final rationale reply for a non-fix path.
   - Use GraphQL `resolveReviewThread` with the thread id.

## Reply Rules

- If code changed, the reply should state:
  - what changed
  - what verification ran
  - optionally the commit hash
- If no code changed because the comment was not valid, the reply should state:
  - why no code change was made
  - what evidence was checked
- Never claim a fix was applied if the commit or push is still pending.

## Operational Guardrails

- Reuse `$gh-address-comments` discovery/reply conventions instead of inventing a new PR lookup flow.
- Prefer `rest_id` for PR review comment replies; use GraphQL ids only for thread resolution.
- If `gh api` fails due to TTY issues, rerun once with the same non-interactive env.
- If the reply API says parent comment not found, refresh PR comments and remap node id to numeric id.
- If the user asks for commit/push/reply/resolve in one flow, do not stop after code changes; finish the full sequence.
- If the user asked to address several comments, report which ones were fixed, which got rationale-only replies, and which remain.

## Handoff Checklist

- target PR resolved
- selected review comments addressed
- code changes verified
- commit created
- branch pushed
- replies posted
- threads resolved
