---
name: ralph-driven-development
description: Unified Ralph execution skill that combines one-story PRD loop delivery, ordered spec-runner workflow, and quality-remediation loops (xenon/radon fail fix). Use when asked to run Ralph loops, execute one story at a time from `prd.json`, continue iterative delivery, run sequential specs, or fix quality-gate failures.
---

# Ralph Driven Development

Run Ralph-style iterative delivery with one unified skill.
This skill merges the former Codex in-session loop and external spec-runner workflow.

## Ownership and Delegation

This skill owns:

- Ralph loop sequencing and stop conditions.
- State updates for iterative progress artifacts (`prd.json`, `progress.txt`, `docs/done.md`, `docs/logs/agent-run.log`).
- Story/spec pass-block gating.
- Quality-remediation loop gating when complexity checks fail.

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
3. If user explicitly asks to fix quality-gate failures (for example xenon/radon FAIL), choose Mode C.
4. If both contexts exist but user intent is ambiguous, default to Mode A and state that assumption.
5. Do not run multiple modes in one invocation unless user explicitly requests it.

### Mode A: In-Codex PRD Loop (default)

Use this mode when `prd.json` exists or user asks for one-story iterative implementation.

Expected files:

- `prd.json`
- `progress.txt`
- `AGENTS.md` (repo or nearest parent)

Fallback when `prd.json` is missing:

- If the user intent is iterative optimization/remediation (for example "계속", "최적화 계속"), run one bounded ad-hoc iteration instead of stopping.
- Ad-hoc iteration contract:
  1. Pick one measurable target with evidence (for example edge_count reduction, complexity offender count).
  2. Apply TDD (`red -> green`) for that single target.
  3. Run required quality checks from `AGENTS.md` or `quality-plan`.
  4. Report as `ad-hoc iteration (no prd)` and do not mark story pass state.
  5. Recommend creating `prd.json` before the next multi-iteration cycle.
- If user intent is feature delivery (not optimization/remediation), ask for PRD preparation instead of guessing backlog.
- Path guardrail (required): before any `ralph_state.py --prd prd.json` command, verify `test -f prd.json`.

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

### Mode C: Quality Remediation Loop (complexity-fail fix)

Use this mode when the user asks to remove `xenon`/`radon` failures rather than deliver a new story.

Expected files:

- `AGENTS.md` (repo quality rules)
- source files reported by complexity tools

Workflow:

1. Run baseline checks:
   - `uv run radon cc src -s -n C`
   - `uv run xenon --max-absolute B --max-modules A --max-average A src` (or repo-defined thresholds)
2. Delegate metric localization to `code-health` lane and collect offender list.
3. Apply bounded remediation in this order:
   1. block offenders (C/D)
   2. module-rank offenders (B modules to A)
4. Re-run baseline checks after each bounded patch batch.
5. Stop when checks pass or when progress stalls; report blockers with concrete file-level evidence.
6. In this mode, do not mark PRD stories passed unless the user also requested story delivery.

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

# If `--json` is rejected by the tool, rerun without it and parse text output
python ~/.codex/skills/ralph-driven-development/scripts/ralph_state.py quality-plan --repo-root .

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

## Operational Noise Controls

- Before git commands, verify repo context: `git rev-parse --is-inside-work-tree`.
- Use search-as-discovery first: run Ralph state/script commands before broad repository scans.
- Apply path filtering for `rg`: start from files surfaced by PRD/story/spec state outputs.
- Use trace-plus-rg evidence gating: widen search only after concrete failing checks/story evidence.
- Before running repo scripts or shared paths, verify with `test -f` / `test -d` (or `rg --files` for discovery).
- If repo helper paths are missing, fallback to branch context commands: `git log --since=1.week --name-only` and `git diff --stat`.
- If `grepai` is unavailable, skip grepai-only steps and continue with `rg`-based discovery.
- If `timeout` is unavailable, rerun without timeout wrapper (or use `gtimeout` when available).
- If `pdfinfo` is unavailable, use Python PDF metadata fallback (`pypdf`/`pdfplumber`) or skip with note.
- Avoid here-doc syntax; use `python -c` or single-line commands.

## Guardrails

- Never mark a story passed unless required checks pass.
- Never silently implement multiple stories in one iteration.
- Keep `progress.txt` append-only.
- Preserve user-authored changes outside the current story scope.
- In spec-runner mode, do not mark spec done without the magic phrase.
- In quality-remediation mode, never report completion without fresh xenon/radon pass output.

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

- Mode C (quality remediation):
- "xenon fail fix"
- "radon complexity fix"
- "Complexity (xenon): FAIL"
- "복잡도 실패 항목 전부 수정"
- "quality gate failure fix"

## References

- `references/scenario-catalog.md`: recommended use cases, anti-patterns, trigger phrases.
- `references/prd-json-schema.md`: JSON contract and quality checklist.
- `references/quality-profiles.md`: stack-based fallback quality checks when AGENTS.md is incomplete.
- `references/jaxtar-quality-profile.md`: optional specialization example for one repository.
- `references/quality-remediation-mode.md`: mode-C triage/remediation checklist for xenon/radon failures.
