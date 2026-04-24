---
name: branch-onboarding-brief
description: Analyze current git branch changes from the branch fork point (resolved from origin/HEAD or a specified upstream base), run an onboarding context phase, and produce a well-formatted branch briefing that directly supports the current user request or parent-skill workflow. Use when asked to compare branches, summarize branch diffs, inspect branch-scoped changes, prepare onboarding context, or provide prerequisite branch context for another skill.
---

# Branch Onboarding Brief

## Overview

Create a reliable, repeatable onboarding phase that summarizes the current branch changes since its fork point, grounds that summary in actual changed-code inspection, then produces a structured branch briefing and immediately hands off to the requested next action.

## Workflow

### 1) Collect branch context

Before running repo-scoped branch commands, verify context once:

```bash
git rev-parse --is-inside-work-tree
```

Prefer the bundled script for deterministic data:

```bash
CODEX_HOME=${CODEX_HOME:-$HOME/.codex}
SKILL_DIR="$CODEX_HOME/skills/branch-onboarding-brief"
test -f "$SKILL_DIR/scripts/collect_branch_info.py" && python "$SKILL_DIR/scripts/collect_branch_info.py" --format json
```

Bundled collector semantics:
- `--base` names the upstream branch used only to resolve the branch fork point; omit it to default to `origin/HEAD`, then `main`/`master`
- the fork point is resolved with `git merge-base --fork-point <base> HEAD`, falling back to `git merge-base <base> HEAD`
- commit subjects, file list, numstat, and diff stat use `fork_point..HEAD`
- the JSON payload now exposes `compare_mode` so parent workflows can see which range each metric used
- the JSON payload also exposes `base` and `fork_point`

If the bundled skill path is missing, search exact candidates under `"$CODEX_HOME/skills"` first and run the first returned absolute path:

```bash
rg --files "$CODEX_HOME/skills" -g 'collect_branch_info.py'
python /absolute/path/from-search/collect_branch_info.py --format json
```

If the script is unavailable (or script path check fails), fall back to:

```bash
git log --since=1.week --name-only
git diff --stat
git branch --show-current
base=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null || printf '%s\n' main)
fork=$(git merge-base --fork-point "$base" HEAD 2>/dev/null || git merge-base "$base" HEAD)
git log "$fork"..HEAD --oneline
git diff "$fork"..HEAD --name-only
git diff "$fork"..HEAD --numstat
git diff --stat "$fork"..HEAD
```

If the repo does not use `main`, detect the default upstream branch:

```bash
git symbolic-ref refs/remotes/origin/HEAD
```

### 2) Ground the diff in actual code before briefing

Do not stop at commit subjects, file counts, or diff stats. Before writing the briefing, inspect the actual changed code on the current branch.

Minimum grounding contract:
- start from the changed-file list produced by the collector or `git diff ... --name-only`
- read every high-risk or cross-cutting changed file, plus at least one representative changed file from each major area
- delegate the AST-first changed-file discovery and symbol extraction pass to `probe-deep-search`
- inspect the exact functions, classes, and symbols touched in changed Python modules with AST-first tools
- summarize concrete code-level intents and boundary shifts, not just directory names

Preferred tool order:
1. `probe symbols <changed-file>`
2. `probe extract <changed-file>#<symbol>` or `probe extract <changed-file>:<line-range>`
3. `probe query <pattern> <changed-path> --language python` for structural matches
4. `rg` / `sed` / direct file reads only when `probe` is unavailable or insufficient

Suggested commands:
```bash
probe symbols src/stowage/planner/spp/pipeline.py
probe extract src/stowage/planner/spp/pipeline.py#run_loading_spp_pipeline_result
probe query "def $NAME($$$)" src/stowage/planner/spp --language python
```

If the branch is large, still read all risky/core files and inspect at least the top churn modules plus one representative file per remaining changed area before briefing.

### 3) Onboarding phase (always before new work)

Provide this phase **before** taking any additional task actions unless the user explicitly says to skip it.

Include:
- Branch name, upstream base branch used for fork-point detection, and fork-point commit
- Commit count and short log
- File count and top changed areas
- Net LOC summary
- Risk scan (high-churn files, core modules, data format changes)
- Code-grounded findings (actual changed files/symbols inspected, key boundary or behavior shifts)
- Test status (only mention tests you actually ran; otherwise mark as not run)

### 4) Branch briefing (well-formatted)

Use the template in `"$CODEX_HOME/skills/branch-onboarding-brief/assets/branch_brief_template.md"`. Keep the formatting tight and use the **PR Workflow** style as a reference (sections like Overview, Key Changes, Metrics, Risks, Tests, Review Focus).

When categorizing changes, make your criteria explicit (for example: tests by `tests/`, TUI by `src/tui/`, domain logic by `src/stowage/`). If categorization is heuristic, say so. Include at least a short code-grounded subsection describing which changed files/symbols were actually inspected and what they imply for the next task.

### 5) Handoff behavior (no decision gate)

- If the user request includes onboarding + another task, execute that next task immediately after onboarding.
- If this skill is called by another skill, return onboarding output as supporting context and continue parent workflow.
- If the user requested onboarding only, stop after delivering the briefing.
- Do not ask “Proceed with next task?” unless a true blocker exists.

## Operational Noise Controls
- Use search-as-discovery: run the bundled `"$CODEX_HOME/skills/branch-onboarding-brief/scripts/collect_branch_info.py"` first; do not start with broad repo-wide scans.
- Treat git metadata as discovery only; the onboarding pass is incomplete until representative changed files have been read and risky changed modules have been inspected structurally.
- Apply path filtering: prioritize changed-file lists from branch diff output before expanding to repository-wide search. Use `probe` against those changed paths before any broad text search.
- Use trace-plus-rg evidence gating: run targeted `rg` on identified files/modules first; only then expand with `rg --files`.
- Before any repo-scoped script or git command, verify repo context with `git rev-parse --is-inside-work-tree`; if it fails, stop branch-only analysis and report.
- Path-sensitive guardrail: never assume the current repo contains `scripts/collect_branch_info.py`; verify the bundled skill path with `test -f` first, then use `rg --files "$CODEX_HOME/skills" -g 'collect_branch_info.py'` before any repo-wide search.
- If `rg --files "$CODEX_HOME/skills" -g 'collect_branch_info.py'` finds a path, run that exact absolute path instead of retrying a repo-local `scripts/collect_branch_info.py`.
- Avoid fallback loops: if git/base-detection fails twice, resolve base once (`origin/HEAD`) and proceed with the minimal diff set.

## Output format (chat)

## Resources

### scripts/
- `collect_branch_info.py`: Gather branch diff data and emit JSON/Markdown.

### assets/
- `branch_brief_template.md`: Structured briefing template.
