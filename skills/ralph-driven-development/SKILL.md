---
name: ralph-driven-development
description: Unified Ralph execution skill that combines one-story PRD loop delivery in Codex with an external ordered-spec runner workflow. Use when asked to run Ralph loops, execute one story at a time from `prd.json`, continue iterative delivery, or run sequential spec files until a completion phrase is emitted.
---

# Ralph Driven Development

Run Ralph-style iterative delivery with one unified skill.
This skill merges the former Codex in-session loop and external spec-runner workflow.

## Ownership and Delegation

This skill owns:

- Ralph loop sequencing and stop conditions.
- State updates for iterative progress artifacts (`prd.json`, `progress.txt`, `docs/done.md`, `docs/logs/agent-run.log`).
- Story/spec pass-block gating.

This skill may delegate specialist work as needed:

1. Delegate branch baseline/diff onboarding to `branch-onboarding-brief` when scope is unclear.
2. Delegate deep implementation-path uncertainty to `grepai-deep-analysis` before risky changes.
3. Delegate hotspot/risk scans to `code-health` for sizing or prioritization.
4. Delegate AGENTS policy rewrite tasks to `agents-md-builder` when requested.
5. Optionally delegate long-running isolated execution to `codex-exec-sub-agent` when fresh context or retry isolation is useful.

When using `codex-exec-sub-agent`, prefer bounded calls:

```bash
~/.codex/skills/codex-exec-sub-agent/scripts/run.sh --timeout-sec 600 --prompt-file /full/path/prompt.txt
```

## Execution Modes

Choose exactly one mode per invocation.

### Mode Selection Gate (required)

Use this decision order before execution:

1. If user explicitly asks for story-by-story PRD execution, choose Mode A.
2. If user explicitly asks to run ordered `docs/tasks/*.md` specs with a completion phrase, choose Mode B.
3. If both contexts exist but user intent is ambiguous, default to Mode A and state that assumption.
4. Do not run both modes in one invocation unless user explicitly requests it.

### Mode A: In-Codex PRD Loop (default)

Use this mode when `prd.json` exists or user asks for one-story iterative implementation.

Expected files:

- `prd.json`
- `progress.txt`
- `AGENTS.md` (repo or nearest parent)

Workflow:

1. Read `references/scenario-catalog.md`, `references/prd-json-schema.md`, `references/quality-profiles.md`, and repo-local `AGENTS.md`.
2. Validate `prd.json`.
3. Read `brief` output and pick `nextStory`.
4. If no pending story exists, return `<promise>COMPLETE</promise>`.
5. Implement exactly one story.
6. Run quality checks from repo `AGENTS.md` or `quality-plan` fallback.
7. If checks pass:
   1. Commit with `feat: [Story ID] - [Story Title]`.
   2. Mark story passed.
   3. Append one structured progress entry.
8. If checks fail:
   1. Keep `passes: false`.
   2. Mark story blocked with reason and next action.
   3. Append one structured failure progress entry.
9. Stop after one story unless user explicitly asks for multiple iterations.

### Mode B: Ordered Spec Runner (external loop)

Use this mode when user asks to drive a `docs/tasks/*.md` sequence with a magic completion phrase.

Expected files:

- `docs/specifications.md` (plan)
- `docs/tasks/*.md` (ordered spec units like `0001-...md`)
- `docs/done.md` (completed specs)
- `docs/logs/agent-run.log` (run transcript)

Workflow:

1. Run `scripts/ralph.py` against the repository root.
2. For each pending spec, invoke Codex with the spec prompt contract.
3. Mark completion only when magic phrase appears after implementation/commit.
4. Append full run output to `docs/logs/agent-run.log`.
5. Append finished spec paths to `docs/done.md`.
6. Resume safely by rerunning; completed specs are skipped.

## PRD Preparation

If user provides only an idea and no backlog:

1. Ask 3-5 clarifying questions.
2. Write `tasks/prd-[feature].md` with small, verifiable user stories.
3. Convert it into `prd.json` matching `references/prd-json-schema.md`.
4. Run `validate --strict-warnings`.

## Story Sizing Rules

- Keep stories dependency-safe and ordered: schema -> backend -> UI -> polish.
- Reject vague acceptance criteria like "works well".
- Require concrete checks (commands, observable behavior, test expectations).
- For UI stories, include browser verification in acceptance criteria.

## Definition of Done

Mark a story done only when all conditions hold:

1. Acceptance criteria are met with objective evidence.
2. Required quality checks pass.
3. Changes are committed with `feat: [Story ID] - [Story Title]`.
4. `prd.json` is updated (`passes: true`) for exactly that story.
5. `progress.txt` has an appended structured entry.

If any condition fails, keep `passes: false` and record blockers in story `notes`.

## Completion Rule

When all stories in `prd.json` have `passes: true`, return:
`<promise>COMPLETE</promise>`

## Commands

```bash
# PRD state summary
python ~/.codex/skills/ralph-driven-development/scripts/ralph_state.py status --prd prd.json

# Machine-readable brief with next story
python ~/.codex/skills/ralph-driven-development/scripts/ralph_state.py brief --prd prd.json

# Suggested quality checks
python ~/.codex/skills/ralph-driven-development/scripts/ralph_state.py quality-plan --repo-root . --json

# Print next pending story
python ~/.codex/skills/ralph-driven-development/scripts/ralph_state.py next --prd prd.json

# Mark pass
python ~/.codex/skills/ralph-driven-development/scripts/ralph_state.py mark-pass --prd prd.json --story-id US-003

# Mark blocked
python ~/.codex/skills/ralph-driven-development/scripts/ralph_state.py mark-blocked \
  --prd prd.json \
  --story-id US-003 \
  --reason "pytest failed in tests/test_diffusion_drop_analysis.py" \
  --next-action "fix failing assertion and rerun focused test"

# Validate PRD contract + quality gates
python ~/.codex/skills/ralph-driven-development/scripts/ralph_state.py validate --prd prd.json --strict-warnings

# Append structured progress
python ~/.codex/skills/ralph-driven-development/scripts/ralph_state.py append-progress \
  --progress progress.txt \
  --story-id US-003 \
  --summary "Implemented queue reuse optimization in search expansion." \
  --file src/search/engine.py \
  --learning "Keep loop state immutable to avoid trace divergence."

# Run ordered spec loop from repository root
python ~/.codex/skills/ralph-driven-development/scripts/ralph.py --repo-root .
```

## Guardrails

- Never mark a story passed unless required checks pass.
- Never silently implement multiple stories in one iteration.
- Keep `progress.txt` append-only.
- Preserve user-authored changes outside the current story scope.
- In spec-runner mode, do not mark spec done without the magic phrase.

## Output Contract

At end of invocation:

1. If backlog complete, include `<promise>COMPLETE</promise>`.
2. Otherwise report completed story/spec, checks run, and remaining pending count.

## Trigger Phrases

- Mode A (PRD loop):
- "run Ralph"
- "Ralph loop"
- "ralph-driven-development"
- "work story-by-story from prd.json"
- "continue iterative delivery"
- "반복"
- "반복 실행"
- "계속 반복"
- "다음 반복"
- "다음 스토리 반복 처리"
- "반복 루프"

- Mode B (ordered spec runner):
- "run specs in docs/tasks"
- "process 0001, 0002... specs"
- "use magic phrase completion"
- "resume from docs/done.md"

## References

- `references/scenario-catalog.md`: recommended use cases, anti-patterns, trigger phrases.
- `references/prd-json-schema.md`: JSON contract and quality checklist.
- `references/quality-profiles.md`: stack-based fallback quality checks when AGENTS.md is incomplete.
- `references/jaxtar-quality-profile.md`: optional specialization example for one repository.
