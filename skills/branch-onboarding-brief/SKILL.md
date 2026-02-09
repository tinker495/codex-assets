---
name: branch-onboarding-brief
description: Analyze current git branch differences against main (or a specified base), run an onboarding context phase, and produce a well-formatted branch briefing that directly supports the current user request or parent-skill workflow. Use when asked to compare branches, summarize diffs, prepare onboarding context, or provide prerequisite branch context for another skill.
---

# Branch Onboarding Brief

## Overview

Create a reliable, repeatable onboarding phase that summarizes the current branch vs base, then produce a structured branch briefing and immediately hand off to the requested next action.

## Workflow

### 1) Collect branch context

Prefer the bundled script for deterministic data:

```bash
test -f scripts/collect_branch_info.py || rg --files -g 'collect_branch_info.py'
python scripts/collect_branch_info.py --base main --format json
```

If the script is unavailable (or script path check fails), fall back to:

```bash
git log --since=1.week --name-only
git diff --stat
git branch --show-current
git log main..HEAD --oneline
git diff main..HEAD --name-only
git diff main..HEAD --numstat
git diff --stat main..HEAD
```

If the repo does not use `main`, detect the default base:

```bash
git symbolic-ref refs/remotes/origin/HEAD
```

### 2) Onboarding phase (always before new work)

Provide this phase **before** taking any additional task actions unless the user explicitly says to skip it.

Include:
- Branch name and base branch
- Commit count and short log
- File count and top changed areas
- Net LOC summary
- Risk scan (high-churn files, core modules, data format changes)
- Test status (only mention tests you actually ran; otherwise mark as not run)

### 3) Branch briefing (well-formatted)

Use the template in `assets/branch_brief_template.md`. Keep the formatting tight and use the **PR Workflow** style as a reference (sections like Overview, Key Changes, Metrics, Risks, Tests, Review Focus).

When categorizing changes, make your criteria explicit (for example: tests by `tests/`, TUI by `src/tui/`, domain logic by `src/stowage/`). If categorization is heuristic, say so.

### 4) Handoff behavior (no decision gate)

- If the user request includes onboarding + another task, execute that next task immediately after onboarding.
- If this skill is called by another skill, return onboarding output as supporting context and continue parent workflow.
- If the user requested onboarding only, stop after delivering the briefing.
- Do not ask “Proceed with next task?” unless a true blocker exists.

## Operational Noise Controls
- Use search-as-discovery: run `scripts/collect_branch_info.py` first; do not start with broad repo-wide scans.
- Apply path filtering: prioritize changed-file lists from branch diff output before expanding to repository-wide search.
- Use trace-plus-rg evidence gating: run targeted `rg` on identified files/modules first; only then expand with `rg --files`.
- Path-sensitive guardrail: verify script existence with `test -f` (or `rg --files`) before execution; if missing, skip script and continue with git-based branch context commands.
- Avoid fallback loops: if git/base-detection fails twice, resolve base once (`origin/HEAD`) and proceed with the minimal diff set.

## Output format (chat)

Always include a small ASCII flow diagram so the user can scan the process quickly.

Example:

```
[Collect] -> [Onboard] -> [Brief] -> [Handoff]
```

## Resources

### scripts/
- `collect_branch_info.py`: Gather branch diff data and emit JSON/Markdown.

### assets/
- `branch_brief_template.md`: Structured briefing template.
