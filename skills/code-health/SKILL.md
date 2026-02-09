---
name: code-health
description: "Run and summarize repository code health checks (duplication, dead code, complexity, maintainability, coverage hotspots, diff summary) using internalized skill scripts (no Makefile dependency). Also use for xenon/radon complexity-fail triage and remediation localization."
---

# Code Health

## Overview
Run the repo's code-health pipeline and deliver a concise, actionable report that highlights risks and cleanup opportunities.
Always split diff reporting into non-test vs test. Minimize non-test diff; do not constrain test diff.

## Workflow
1. Confirm repo root (the script expects to run from the repository root).
2. Ensure tools exist in the environment: `pytest`, `coverage`, `vulture`, `radon`, `xenon`, and `jscpd` (via `npx` or global install). Use `uv` if available.
3. Run pipeline (preferred):
   - `test -f /Users/mrx-ksjung/.codex/skills/code-health/scripts/run_code_health.py || rg --files /Users/mrx-ksjung/.codex/skills/code-health -g 'run_code_health.py'`
   - `python /Users/mrx-ksjung/.codex/skills/code-health/scripts/run_code_health.py --mode summary --top 20`
   - Use `--mode full` for deeper scans.
   - Use `--top-files 20` to expand the main-branch churn list.
   - Use `--skip-coverage` only if tests are too heavy; ask before skipping coverage when accuracy matters.
   - Use `--out-dir /tmp/code-health` or another global directory to avoid repo pollution.
4. If the request is complexity-fix oriented (`xenon FAIL`, `radon C+`), run:
   - `uv run radon cc src -s -n C`
   - `uv run xenon --max-absolute B --max-modules A --max-average A src` (or repo-provided thresholds)
5. On complexity fail, apply two-phase triage from `references/xenon_triage_playbook.md`:
   - Phase 1: clear block-level offenders (C/D blocks first).
   - Phase 2: clear module-rank offenders (B modules -> A) without behavior drift.
6. Summarize outputs using the report template below, keeping non-test and test diffs separate.
7. Call out net code growth and missing tests; prefer deletion-first actions.
8. If the task includes repository navigation/localization comparison, report efficiency metrics:
   - `steps` (average tool or reasoning steps)
   - `cost_usd` (if available from logs)
   - `efficiency = Acc@5 / cost_usd` (or mark unavailable when no cost metric exists)

## Operational Noise Controls
- Use search-as-discovery: execute bundled health scripts first, then run ad-hoc search only when script output leaves a gap.
- Apply path filtering: scope follow-up `rg` to files surfaced by diff/health outputs before any broader scan.
- Use trace-plus-rg evidence gating: require a concrete hotspot/module trace before escalating to `rg --files` or `find`.
- Path-sensitive guardrail: verify script/shared path existence with `test -f` / `test -d` first; when `$CODEX_HOME/shared/code-health` is missing, skip it and continue with `/tmp/code-health`.
- Avoid fallback loops: if a tool invocation fails twice, use the documented fallback once (for example `--skip-coverage`) and continue.

## Report template
- Summary: duplication %, xenon status, coverage included/skipped.
- Diff summary: net non-test lines (minimize), net test lines (no constraint), new/deleted files split by type.
- Main diff (deep): top churn files vs main, split non-test/test.
- Duplication: clones, duplicated lines, top offenders if present.
- Dead code: top vulture findings with confidence.
- Complexity: top cyclomatic entries (radon).
- Maintainability: lowest MI entries (radon).
- Coverage hotspots: lowest covered files and missing-line hotspots.
- Navigation efficiency (optional): steps/cost/efficiency when localization workflows are in scope.
- Actions: 3-5 concrete follow-ups, prioritize deletions and simplifications.

## Heuristics
- Flag duplication > 5% or large clone clusters.
- Treat xenon FAIL as blocking for refactors.
- If cyclomatic complexity is C or worse, or MI is low, suggest refactors or tests.
- If non-test diff shows net growth without tests, call it out explicitly.

## Bundled resources
- `scripts/run_code_health.py`: orchestrate tool execution and write global reports (not in repo).
- `scripts/diff_summary_compact.py`: compact git diff summary.
- `scripts/code_health_compact.py`: vulture/radon/xenon summary with thresholds.
- `scripts/coverage_hotspots.py`: coverage hotspot report from `coverage.json`.
- `references/xenon_triage_playbook.md`: block-first/module-second remediation order for xenon failures.

## Output naming
- Default output directory: `$CODEX_HOME/shared/code-health` if `CODEX_HOME` is set, otherwise `/tmp/code-health`.
- Filenames include project and branch: `<project>__<branch>__code_health.{md,json}`.
- On re-run, previous files are renamed with `legacy__...__YYYYmmdd_HHMMSS` to keep history.
- Before reading the shared output directory, check `test -d "$CODEX_HOME/shared/code-health"`; if missing, use `/tmp/code-health` and continue.
