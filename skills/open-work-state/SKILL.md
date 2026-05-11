---
name: open-work-state
description: Reconstructs the current GitHub work state by reading every open issue and every open pull request for the active repository, including bodies, comments, reviews, checks, labels, assignees, and links. Use when the user asks to understand current project status, read all open issues/PRs, get a work-state briefing, resume from GitHub state, or Korean phrases like "현재 열린 이슈와 PR", "현재 작업 상태 숙지", "open issue/PR 전부 읽기".
---

# Open Work State

## Mission

Build a source-backed briefing of the repository's live work state from GitHub, not from memory or branch-name guesses. Default scope is all **open issues** and all **open pull requests** in the current repo.

## Quick start

From the target repository root:

```bash
python3 ~/.codex/skills/open-work-state/scripts/collect_open_work_state.py \
  --out .codex_tmp/open-work-state
```

Then read the generated Markdown and raw JSON before answering:

```bash
sed -n '1,220p' .codex_tmp/open-work-state/open-work-state.md
```

## Required workflow

1. **Confirm repository identity.** Run `git rev-parse --is-inside-work-tree`, `git status --short --branch`, and `gh repo view --json nameWithOwner,url,defaultBranchRef`.
2. **Fetch live GitHub state.** Use the bundled collector unless blocked. It is read-only and captures open issues, open PRs, comments, PR reviews, review comments, check runs, commit status, mergeability fields, and review-thread data when GitHub permissions allow it.
3. **Inspect artifacts, not just counts.** Read `open-work-state.md` first, then inspect `open-work-state.json` for any issue/PR that has blockers, recent activity, review changes requested, failed checks, unresolved threads, stale labels, or unclear ownership.
4. **Correlate issues and PRs.** Map PR closing references, issue mentions, labels, branch names, titles, and comments. Mark inferences explicitly; do not present inferred linkage as confirmed.
5. **Summarize current work state.** Separate: active PR lanes, issue-only backlog, blocked work, ready-for-agent work, ready-for-human work, stale/ambiguous items, and merged/closed context only if explicitly requested.
6. **Preserve source evidence.** Include issue/PR numbers, URLs, updated timestamps, labels, review/check state, and artifact paths. Quote sparingly; prefer concise paraphrase.

## Output contract

Return Korean by default when the user used Korean. Put the current state first:

- repo, capture timestamp, open issue count, open PR count
- active PR table with `#`, title, branch/base, draft/review/check/merge/thread status, linked issues, blocker
- issue backlog table grouped by label/owner/readiness
- top risks and next recommended actions
- evidence: commands run, artifact paths, and notable GitHub URLs
- gaps: permissions, truncated data, failed collector sections, or not-run checks

## Safety and boundaries

- This skill is read-only. Do not comment, label, close, merge, push, or rerun CI unless another explicit workflow asks for it.
- Always re-fetch live GitHub data for this turn. Prior memory can guide what to look for but never replaces current state.
- If `gh` auth or API permissions fail, stop at that boundary and report the exact failing command/output.
- If the repo has too many items for a readable answer, keep the complete JSON artifact and summarize by priority while preserving item numbers and URLs.
