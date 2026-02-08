---
name: codex-ralph-loop
description: Run a Ralph-style PRD-driven delivery loop in Codex with fresh-context iterations, one-story-at-a-time implementation, and persistent memory in `prd.json` plus `progress.txt`. Use when asked to "run Ralph", "work story-by-story from a PRD", "convert PRD to execution backlog", or "autonomously iterate until all stories pass". Korean trigger intents include "반복", "반복 실행", "계속 반복", "다음 반복", "다음 스토리 반복 처리", and "반복 루프".
---

# Codex Ralph Loop

Execute a Ralph-style loop inside Codex. Treat this document as an execution contract for one iteration.

## Ownership and Delegation

This skill owns one-story iteration sequencing, pass/block gating, and state updates in `prd.json` and `progress.txt`.
As a top-level loop policy owner, it may delegate to any relevant specialist or utility skill when needed.
Do not treat any single downstream skill as a fixed dependency unless the scenario explicitly requires it.

1. Delegate repository baseline and diff onboarding to `branch-onboarding-brief` when scope is unclear at iteration start.
2. Delegate deep code-path uncertainty resolution to `grepai-deep-analysis` before implementing risky stories.
3. Delegate hotspot/risk scans to `code-health` when selecting or splitting the next story.
4. Optionally delegate isolated long-running or fresh-context execution to `codex-exec-sub-agent`.
5. Optionally delegate AGENTS policy drafting or rewrite tasks to `agents-md-builder`.

When using `codex-exec-sub-agent`, prefer quoting-safe and bounded calls:

```bash
~/.codex/skills/codex-exec-sub-agent/scripts/run.sh --timeout-sec 600 --prompt-file /full/path/prompt.txt
```

Use workspace paths or `~/.codex/sub_agent_runs` for outputs; avoid `/tmp`/`/var/tmp` paths in prompts when sandbox rules may block writes.

## Invocation Contract

Assume these files exist in repository root unless user overrides paths:

- `prd.json`
- `progress.txt`
- `AGENTS.md` (repo or nearest parent)

Start each invocation by reading:

1. `references/scenario-catalog.md`
2. `references/prd-json-schema.md`
3. repo-local `AGENTS.md`
4. `references/quality-profiles.md`
5. Optional repo-specific profile only if it matches target repo (example: `references/jaxtar-quality-profile.md`)
6. `references/plan-save-load-integration.md`

## Plan Lifecycle (Required)

Manage iteration plans with `plan-save-load` skill assets:
`python ~/.codex/skills/plan-save-load/scripts/plan_save_load.py ...`

1. Resume latest plan for this repo/branch/group:
   `load --repo-dir . --plan-group ralph-loop --latest`
2. If missing, create it:
   `create --repo-dir . --plan-group ralph-loop`
3. At iteration start/end, append plan updates:
   `save --repo-dir . --plan-group ralph-loop --latest --stdin --append`
4. When all stories pass, archive completion:
   `complete --repo-dir . --plan-group ralph-loop --latest --summary "all stories passed" --move`

## One-Iteration Procedure

1. Run `validate` on `prd.json`.
2. Run `brief` and pick `nextStory`.
3. If no pending story exists, return `<promise>COMPLETE</promise>`.
4. Implement exactly one story.
5. Select quality checks with `quality-plan` and run them.
6. If checks pass:
   1. Commit with `feat: [Story ID] - [Story Title]`.
   2. Mark story passed.
   3. Append structured progress entry.
   4. Append success note to plan via `plan_save_load.py save --append`.
7. If checks fail:
   1. Keep `passes: false`.
   2. Mark story blocked with reason and next action.
   3. Append structured failure progress entry.
   4. Append failure note to plan via `plan_save_load.py save --append`.
8. Stop after one story unless user explicitly requests multiple iterations.

## PRD Preparation

If user provides only an idea and no backlog:

1. Ask 3-5 clarifying questions.
2. Write `tasks/prd-[feature].md` with small, verifiable user stories.
3. Convert it into `prd.json` matching `references/prd-json-schema.md`.
4. Run `validate --strict-warnings`.

## Story Sizing Rules

- Keep stories dependency-safe and ordered: schema -> backend -> UI -> polish.
- Reject vague acceptance criteria like "works well".
- Require concrete checks (commands, observable UI behavior, test expectations).
- For UI stories, include browser verification in acceptance criteria.

## Definition of Done

Mark a story done only when all conditions hold:

1. Acceptance criteria are met with objective evidence.
2. Required quality checks pass.
3. Changes are committed with `feat: [Story ID] - [Story Title]`.
4. `prd.json` is updated (`passes: true`) for exactly that story.
5. `progress.txt` has an appended structured entry.

If any condition fails, keep `passes: false` and record blockers in story `notes`.

## Failure Handling

When iteration checks fail:

1. Do not mark story passed.
2. Use `mark-blocked` to append blocker reason and next action in `notes`.
3. Add a concise progress entry describing failure, evidence, and recovery plan.
4. If scope is too large, split story and re-prioritize.

## Completion Rule

When all stories in `prd.json` have `passes: true`, return:
`<promise>COMPLETE</promise>`

## Helper Script

Use `scripts/ralph_state.py` for deterministic state operations:

```bash
# Show progress summary
python ~/.codex/skills/codex-ralph-loop/scripts/ralph_state.py status --prd prd.json

# Print machine-readable iteration brief (includes nextStory and complete flag)
python ~/.codex/skills/codex-ralph-loop/scripts/ralph_state.py brief --prd prd.json

# Suggest quality checks for current repository
python ~/.codex/skills/codex-ralph-loop/scripts/ralph_state.py quality-plan --repo-root . --json

# Try to load latest plan (create if missing)
python ~/.codex/skills/plan-save-load/scripts/plan_save_load.py load --repo-dir . --plan-group ralph-loop --latest
python ~/.codex/skills/plan-save-load/scripts/plan_save_load.py create --repo-dir . --plan-group ralph-loop

# Print the next story to execute
python ~/.codex/skills/codex-ralph-loop/scripts/ralph_state.py next --prd prd.json

# Mark a story complete
python ~/.codex/skills/codex-ralph-loop/scripts/ralph_state.py mark-pass --prd prd.json --story-id US-003

# Mark a story blocked after failed checks
python ~/.codex/skills/codex-ralph-loop/scripts/ralph_state.py mark-blocked \
  --prd prd.json \
  --story-id US-003 \
  --reason "pytest failed in tests/test_diffusion_drop_analysis.py" \
  --next-action "fix failing assertion and rerun focused test"

# Validate schema + criteria quality gates
python ~/.codex/skills/codex-ralph-loop/scripts/ralph_state.py validate --prd prd.json --strict-warnings

# Append one structured progress entry
python ~/.codex/skills/codex-ralph-loop/scripts/ralph_state.py append-progress \
  --progress progress.txt \
  --story-id US-003 \
  --summary "Implemented queue reuse optimization in search expansion." \
  --file src/search/engine.py \
  --learning "Keep loop state immutable to avoid trace divergence."

# Append iteration summary to plan markdown (pipe text)
cat <<'EOF' | python ~/.codex/skills/plan-save-load/scripts/plan_save_load.py save \
  --repo-dir . \
  --plan-group ralph-loop \
  --latest \
  --stdin \
  --append
## Iteration: US-003
- Result: success
- Checks: pytest -q, pre-commit run --all-files
- Next: pick next pending story
EOF

# Archive finished plan when backlog is complete
python ~/.codex/skills/plan-save-load/scripts/plan_save_load.py complete \
  --repo-dir . \
  --plan-group ralph-loop \
  --latest \
  --summary "all stories passed" \
  --move
```

## Guardrails

- Never mark a story passed unless quality checks for that story pass.
- Never implement multiple stories silently in one iteration.
- Keep `progress.txt` append-only; do not delete prior entries.
- Preserve user-authored changes outside the current story scope.
- Prefer small commits to keep iteration rollback cheap.

## Output Contract

At end of invocation:

1. If backlog complete, include `<promise>COMPLETE</promise>`.
2. Otherwise report completed story id, checks run, and updated pending count.

## References

- `references/prd-json-schema.md`: JSON contract and quality checklist for conversion.
- `references/scenario-catalog.md`: recommended use cases, anti-patterns, trigger phrases.
- `references/quality-profiles.md`: stack-based fallback quality checks when AGENTS.md is incomplete.
- `references/plan-save-load-integration.md`: plan create/load/save/complete playbook for ralph-loop iterations.
- `references/jaxtar-quality-profile.md`: optional specialization example for one repository.
