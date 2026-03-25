---
name: resume
description: Inspect the current git working tree and OMX session artifacts as an internal preflight, then immediately continue the user’s attached task with the right in-flight commit context. Use when a user activates `$resume` and pastes the real task they want to continue on top of staged work, an unfinished local commit, or the latest local branch state in a fresh session. Also use for resume-and-do flows such as continuing implementation, fixing a bug on the current worktree, resuming a refactor, or reconstructing current state before executing the next task.
---

# Resume

## Overview

Treat this skill as a **resume preflight wrapper**. First reconstruct the correct continuation context for the current worktree or latest local commit. Then use that context to perform the user’s actual attached task immediately.

This is **not** a report-only skill by default. If the user says:

- `$resume 이어서 구현해`
- `$resume 지금 상태 기준으로 버그 고쳐`
- `$resume 이 커밋 이어서 테스트까지 마무리해`

the attached task is the real deliverable. The resume analysis is the onboarding step.

Only switch into report-only behavior when the user explicitly asks for analysis, handoff text, briefing, summary, or state explanation.

## Invocation Rule

Interpret the rest of the user message after `$resume` as the task to execute.

- If a concrete task is attached, do the preflight quickly and then **continue the task without asking to proceed**.
- If no concrete task is attached, produce a resume brief.
- If the task is ambiguous but low-risk, make a reasonable assumption and continue.
- Ask only when the next action would be destructive, irreversible, or materially branching.

## Workflow

### 1. Confirm repo context

Run this once before any repo-scoped analysis:

```bash
git rev-parse --is-inside-work-tree
```

Stop and report if the result is not `true`.

### 2. Run the bundled collector first

Prefer the bundled script over ad-hoc command chains:

```bash
CODEX_HOME=${CODEX_HOME:-$HOME/.codex}
SKILL_DIR="$CODEX_HOME/skills/resume"
python "$SKILL_DIR/scripts/collect_resume_context.py" --repo-root . --format markdown
```

Use JSON only when structured follow-up is needed:

```bash
python "$SKILL_DIR/scripts/collect_resume_context.py" --repo-root . --format json
```

The collector gathers:
- branch/base/HEAD anchor data
- staged, unstaged, untracked, conflicted paths
- staged/unstaged/branch diff summaries with dominant areas and largest files
- recent commits
- `.omx/notepad.md` tail entries
- active or relevant `.omx/state/*.json` signals
- active/recent plan and context files
- risk hints and a suggested file inspection order

### 3. Respect the collector focus mode

Use the reported `focus_mode` to decide what to analyze next:
- `working-tree`: prioritize staged and unstaged diffs; this is the primary continuation surface.
- `latest-commit`: working tree is clean, so treat `HEAD` as the handoff unit.
- `branch-context`: there is no meaningful in-flight delta; summarize branch state only.

### 4. Build only the context needed for the attached task

Open, in order:
1. largest changed runtime files from `Suggested Inspection Order`
2. paired or nearby tests
3. the latest relevant `.omx/notepad.md` entries
4. active `.omx/state/*.json` files
5. recent `.omx/context/*.md` or active plans if they explain intent or verification state

Do not start with broad repo-wide scanning. This skill is for fast continuation, not full repository archaeology.

Stop expanding context once you can safely continue the attached task.

### 5. Continue the attached task immediately

After preflight:
- restate the continuation anchor only if it helps avoid confusion
- mention commit-boundary risk only if it materially affects the task
- then perform the attached task

Do **not** spend the whole turn explaining the current state unless the user asked for that.

### 6. Use report mode only when explicitly requested

Answer in Korean unless the user asked for another language.

State clearly:
- what the in-flight commit appears to change
- whether the current boundary is `staged`, `unstaged`, `mixed`, or `clean tree + HEAD`
- whether the current working set still looks like one coherent commit story or has drifted into multiple themes
- which runtime files are core and which tests/docs/artifacts support them
- which OMX state or prior plan still matters
- what the next session should do first
- what remains uncertain

## Analysis Rules

- Prefer working-tree evidence over branch-vs-base evidence when they disagree.
- If staged and unstaged edits both exist, call out that the commit boundary is mixed.
- If the working tree is clean but the branch is ahead of base, treat the latest local commit as the continuation anchor.
- If `.omx/state/skill-active-state.json` or related OMX mode state is still active, mention whether it looks resumable or stale.
- Separate proven evidence from inference. Mark guesses as `추정`.
- Do not claim tests passed unless you saw a real verification artifact, notepad entry, state file, or command output.
- Explicitly say when the change set no longer looks like a clean single-commit boundary.
- In default execution mode, keep the resume explanation to the minimum needed to safely perform the task.
- If the user explicitly wants a PR-style comparison against `main`/base rather than a resume packet, switch to or combine with `branch-onboarding-brief` after the working-state summary.

## Output Contract

### Default: execution mode

When the user attached a concrete task:
1. Give at most a short `재개 기준점` note only if needed
2. Execute the requested task
3. Report task results with normal verification evidence

Do not force the long resume brief structure in this mode.

### Report mode

Only when the user explicitly asks for a briefing, summary, handoff, or state explanation, return:
1. `한줄 요약`
2. `현재 경계`
3. `핵심 변경 묶음`
4. `OMX/세션 단서`
5. `바로 읽을 파일 순서`
6. `다음 액션`
7. `리스크/불확실성`

Keep the report compact but specific. Include file paths, counts, and whether each statement is evidence or `추정` when needed.

## Resources

### scripts/
- `collect_resume_context.py`: deterministic git + `.omx` collector for resume analysis.
