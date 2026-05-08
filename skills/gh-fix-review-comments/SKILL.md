---
name: gh-fix-review-comments
description: "Runs the full GitHub PR review-fix closure loop, starting with complete branch/PR context reconstruction before touching review comments. Use when the user asks to fix PR review comments end to end, especially requests mentioning review feedback, requested changes, current branch context, commit/push, reply, resolve, or Korean phrases like '리뷰 코멘트 반영', '브랜치 맥락', '답글', '리솔브'."
---

# GH Fix Review Comments

Use this skill for end-to-end PR review closure. The first goal is to fully understand the current branch's work context; review comments are interpreted only after the branch intent, PR scope, diff, and existing verification contract are reconstructed. Invocation authorizes normal review-fix side effects: local edits, verification, commit, push, inline replies, and thread resolution.

## Preconditions

- Run from the repository that owns the PR.
- Confirm tools/context: `command -v gh`, `git rev-parse --is-inside-work-tree`, and `GH_FORCE_TTY=0 GIT_TERMINAL_PROMPT=0 GH_PAGER=cat gh auth status`.
- Prefix every `gh` command with `GH_FORCE_TTY=0 GIT_TERMINAL_PROMPT=0 GH_PAGER=cat`.
- If `gh` auth is missing or expired, stop and ask the user to run `gh auth login`; do not fake GitHub writes.

## Branch Context Gate

Complete this gate before building the review-comment work queue.

1. Resolve the live PR and branch topology.
   - If the user supplied a PR URL/number, use it; otherwise run `gh pr view --json number,url,title,body,headRefName,baseRefName,headRepositoryOwner,headRepository,baseRepository`.
   - Fetch latest remote refs, identify base/head, and compute the PR-facing merge base.
   - Never infer branch purpose from branch name alone.
2. Reconstruct the branch intent and actual scope.
   - Prefer repo tooling when present, e.g. `collect_branch_info.py --base <base> --format json`.
   - Otherwise collect `git log --oneline <base>..HEAD`, `git diff --stat <base>...HEAD`, and the changed-file list.
   - Read PR title/body, relevant docs, AGENTS.md files for touched paths, and representative changed code before judging comments.
3. Capture a short context brief for yourself before editing.
   - Include: intended behavior, changed subsystems, semantic boundaries, verification expectations, and known risk areas.
   - If the comment appears to contradict branch intent, inspect deeper before deciding whether it is valid.

## Review-Fix Workflow

1. Fetch thread-aware review data.
   - Prefer a repo-local `scripts/fetch_comments.py`; otherwise locate the bundled GitHub plugin script with `find /Users/mrx-ksjung/.codex/plugins/cache/openai-curated/github -path '*/skills/gh-address-comments/scripts/fetch_comments.py' | head -1`.
   - Persist raw fetch output in a temp file so thread ids, paths, lines, and bodies can be rechecked after fixes.
2. Build the work queue.
   - Default to all unresolved review threads unless the user narrowed scope.
   - Skip resolved/outdated threads unless explicitly requested.
   - Cluster related threads by branch subsystem or behavior, not just by file.
   - Classify each thread as `code-fix`, `rationale-only`, `duplicate`, or `blocked`.
3. Validate each comment against branch context.
   - Accept a comment only when it identifies a real defect, contract mismatch, maintainability issue, missing evidence, or PR-scope inconsistency.
   - For invalid, duplicate, already-satisfied, or out-of-scope comments, prepare a concise evidence-backed rationale reply.
4. Patch valid comments narrowly.
   - Make the smallest change that preserves the branch intent while addressing the review point.
   - Do not add unrelated TODOs, compatibility shims, broad cleanup, or new dependencies.
   - If comments conflict, fix the safe shared contract or mark the conflict as `blocked` with evidence.
5. Verify before any “fixed” reply.
   - Run targeted checks proving the changed behavior, then broader repo-required checks when touched paths demand them.
   - If verification fails, diagnose root cause and iterate before committing.
   - Record exact commands and pass/fail evidence for GitHub replies and final handoff.
6. Commit and push.
   - Stage only intended files, follow repository commit-message rules, and push the current branch to the PR remote.
   - Do not post a “fixed” reply until the relevant commit is pushed.
7. Reply inline.
   - Map GraphQL review comment ids to numeric REST ids with `gh api repos/OWNER/REPO/pulls/PR/comments --paginate`; REST `node_id` corresponds to the GraphQL comment `id`.
   - Post replies with `gh api repos/OWNER/REPO/pulls/PR/comments/REST_ID/replies -f body='...'`.
   - Reply in the user’s language. Include what changed, verification run, and commit hash when code changed.
8. Resolve and prove closure.
   - Resolve after the pushed fix or final rationale reply with `resolveReviewThread`:
     - `gh api graphql -f query='mutation($thread:ID!){resolveReviewThread(input:{threadId:$thread}){thread{id isResolved}}}' -f thread=THREAD_ID`
   - Re-run the thread fetch after resolving. Stop only when all targeted threads are resolved; for broad requests, target `unresolved_threads=0`.

## Reply Template

```md
반영했습니다.
- 맥락: <branch intent / affected subsystem>
- 변경: <what changed or why no code change was needed>
- 검증: `<command>` 통과
- 커밋: <short_sha>
```

Never claim branch context, a fix, a push, or resolution that has not actually been verified.

## Failure Handling

- Missing branch context: pause code edits, gather PR metadata/diff/log/docs first, then continue.
- `gh api` TTY/pager issue: retry once with the required non-interactive env prefix.
- Missing numeric REST id: refresh PR review comments and remap by `node_id`, then by path/line/body only as a last resort.
- Push failure: report the blocker and do not reply “fixed”.
- Resolve mutation failure: keep the GitHub reply posted, re-fetch the thread id, retry once, then report exact error.

## Handoff Checklist

- Branch/PR context reconstructed and summarized.
- Target PR identified.
- Unresolved thread queue classified against branch intent.
- Valid comments patched or rationale-only replies prepared.
- Verification passed or blocker captured.
- Commit pushed when code changed.
- Inline replies posted and threads resolved.
- Final re-fetch proves targeted closure.
