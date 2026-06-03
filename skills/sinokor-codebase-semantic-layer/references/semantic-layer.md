# Sinokor Codebase Semantic Layer

## Quick Reference

- Area: `snk2501o-sinokor-placement-optimization` repository analytics and operational codebase risk.
- Intended users: Data Analytics and Codex runs analyzing repo health, SPP benchmark evidence, TUI planning diagnostics, architecture/test risk, and future data-work setup.
- Coverage level: Limited.
- Source inventory: `references/source-inventory.md`.
- Last synthesized: 2026-06-04.
- Freshness expectations: Re-run git-history commands after new commits. Re-run `uv run spp-bench` for current SPP performance evidence. Re-read local AGENTS files before editing any subtree.
- Default date and time zone rules: Use local repo git dates for commit history. This setup used the Asia/Seoul local date 2026-06-04.

## Entity Clarification

| Entity | Means | Does Not Mean | Primary IDs | Grain Notes | Sources |
| --- | --- | --- | --- | --- | --- |
| Repository | The local checkout at `/Users/mrx-ksjung/project/snk2501o-sinokor-placement-optimization` | Remote GitHub state unless explicitly queried | Git `HEAD`, working tree path | Repo-level | Root AGENTS, docs index, git history |
| Pure SPP | Slot-level abstract SPP result with `CargoClassKey`, F/E, average weight, and no standard `ContainerData` binding | Materialized PostSPP plan | `PureSPPOutput`, `SppSlotDecision`, `SPPStageArtifacts` | Stage output | `src/stowage/planner/spp/AGENTS.md` |
| PostSPP | Materialization after SPP, producing actual standard container binding and materialized diagnostics | Pure SPP itself | PostSPP snapshot fields, materialize diagnostics | Stage output | `src/stowage/planner/pipeline/AGENTS.md` |
| TUI planning diagnostics | Textual UI rendering and dispatch of Input, PreMPP, MPP, SPP, and PostSPP snapshots | Domain calculation ownership | `planning-tabs`, `planning-oracle-tabs`, `PipelineStepDiagnostics` | UI view-model and snapshot | `src/tui/AGENTS.md`, `src/tui/mixins/AGENTS.md` |
| SPP benchmark | Official current-code SPP performance benchmark and anomaly export command | A historical git recon metric | `uv run spp-bench`, `benchmark.json`, `benchmark_summary.csv`, `anomaly_details.json` | Vessel x rotation matrix by default | `src/scripts/AGENTS.md` |

## Key Metrics

| Metric | Definition | Numerator | Denominator | Time Grain | Canonical Source | Caveats |
| --- | --- | --- | --- | --- | --- | --- |
| Code hotspot count | Count of commits touching a file from `git log --name-only` with blank separator lines filtered out | File appearances in commit history | Not applicable | All-time at local `HEAD` | Git history recon | Stale after new commits; use explicit `HEAD` and filter blank lines |
| Bug-magnet count | Count of files touched by commits whose messages match `fix|bug|broken` | File appearances in matching commits | Not applicable | All-time at local `HEAD` | Git history recon | Commit-message heuristic; not all fixes use those words |
| High-risk file | File that appears in both hotspot and bug-magnet lists | Intersection of the two ranked lists | Top 10 in each list | All-time at local `HEAD` | Git history recon | Ranking is relative to the selected window |
| Active contributor ratio | Contributors active in last 3 months divided by total contributors | Active contributors | Total contributors | Last 3 months vs all-time | `git shortlog -sn --no-merges --since='3 months ago' HEAD` | In this repo, `git shortlog` needed explicit `HEAD` for non-empty output |
| Firefighting rate | Revert/hotfix/emergency/rollback commits divided by total commits | Matching emergency commits | Total commits in window | All-time at local `HEAD` | Git history recon | Keyword heuristic; zero observed in setup recon |
| SPP performance | Placed, reject, anomaly, and timing metrics from the official SPP benchmark | Benchmark-specific metric | Benchmark matrix or selected pair | Current working tree run | `uv run spp-bench` | Not measured during this semantic-layer setup |

## Standard Filters And Dimensions

| Filter Or Dimension | Default Logic | Override When | Applies To | Sources |
| --- | --- | --- | --- | --- |
| Analysis window | Small repo default: all-time, top 10 files | Repo exceeds 500 commits or user requests a date range | Git recon | `codebase-recon` skill, setup commands |
| Stage boundary | Keep PreMPP, MPP, SPP, and PostSPP separate | User explicitly asks for end-to-end loading pipeline behavior | Planner diagnostics and SPP analysis | `CONTEXT.md`, SPP AGENTS, pipeline AGENTS |
| Evidence type | Prefer code/tests/AGENTS/docs for As-Is facts; use specs for To-Be facts | User asks for roadmap or target design | Documentation analysis | `docs/_meta/docs-contract.md` |
| SPP performance proof | Use `uv run spp-bench` output | User asks only for static code risk or design docs | SPP performance analysis | `src/scripts/AGENTS.md` |

## Key Local Sources

| Source | When To Use | Grain | Join Keys | Freshness | Caveats | Sources |
| --- | --- | --- | --- | --- | --- | --- |
| `AGENTS.md` | Repo-wide agent rules, commands, validation expectations | Repo | Path | Re-read per task | User may update between turns | Root AGENTS |
| `CONTEXT.md` | Domain language and planner-stage concepts | Domain concept | Concept name | Re-read for architecture or terminology work | Broad glossary, not implementation proof | Domain context |
| `docs/_meta/docs-contract.md` | Decide As-Is vs To-Be evidence source | Doc policy | Doc status | Low drift but verify if docs changed | Contract only, not a full audit | Docs contract |
| `src/stowage/planner/spp/AGENTS.md` | Pure SPP contract, SPP entry points, validation commands | Stage | Function/class names | Re-read before SPP edits | Does not replace code/tests | SPP rules |
| `src/stowage/planner/pipeline/AGENTS.md` | Pipeline snapshot and pure/materialized boundary | Stage snapshot | Snapshot field names | Re-read before diagnostics/export edits | Orchestration only | Pipeline rules |
| `src/scripts/AGENTS.md` | SPP benchmark and diagnostics export entry points | CLI command | Command/output artifact | Re-read before benchmark work | Benchmark must be run for current evidence | Scripts rules |
| `src/tui/AGENTS.md` and `src/tui/mixins/AGENTS.md` | TUI planning diagnostics, render dispatch, scroll ownership | UI subtree | Widget/tab/snapshot ids | Re-read before TUI edits | UI-only | TUI rules |

## Query Patterns

- Pattern: Codebase recon refresh
  - Use when: The user asks for current repo health, hotspots, risk, contributor momentum, or where to start reading.
  - Key sources: Git history and local AGENTS files.
  - Required filters: Use all-time while repo remains under 500 commits; otherwise calibrate the window.
  - Common joins: Intersect hotspot and bug-magnet ranked lists, then attribute primary owner with `git shortlog -sn HEAD -- <file>`.
  - Example skeleton:

```sh
git log --format=format: --name-only HEAD | sed '/^$/d' | sort | uniq -c | sort -nr | head -10
git log -i -E --grep='fix|bug|broken' --name-only --format='' HEAD | sed '/^$/d' | sort | uniq -c | sort -nr | head -10
git shortlog -sn --no-merges HEAD
```

- Pattern: SPP performance analysis
  - Use when: The user asks whether SPP changed, improved, regressed, or needs benchmark evidence.
  - Key sources: `src/scripts/AGENTS.md`, benchmark outputs, SPP pipeline/evaluator code.
  - Required filters: Current working tree, selected vessel/rotation matrix if specified.
  - Common joins: Compare benchmark aggregate, anomaly details, and git diff scope.
  - Example skeleton:

```sh
uv run spp-bench
```

- Pattern: TUI planning diagnostics analysis
  - Use when: The user asks about planning tabs, snapshot rendering, evidence export, or oracle profile behavior.
  - Key sources: TUI AGENTS, TUI mixins AGENTS, pipeline AGENTS, relevant tests.
  - Required filters: Active planning tab and oracle level.
  - Common joins: Map TUI snapshot fields to `PipelineStepDiagnostics`.

## Gotchas

- Gotcha: Pure SPP and PostSPP are intentionally separate.
  - Impact: Mixing materialized fields into pure SPP reporting can create misleading metrics and contract drift.
  - How to avoid: Use SPP AGENTS and pipeline AGENTS before changing evaluator, export, or TUI diagnostics.
  - Source: `src/stowage/planner/spp/AGENTS.md`, `src/stowage/planner/pipeline/AGENTS.md`.

- Gotcha: Git hotspot command can count blank separator lines.
  - Impact: A blank entry may rank first and distort the report.
  - How to avoid: Filter blank lines with `sed '/^$/d'`.
  - Source: Setup recon command behavior on 2026-06-04.

- Gotcha: `git shortlog -sn --no-merges` may return empty output without a revision in this local environment.
  - Impact: Contributor and active-ratio metrics can look like zero.
  - How to avoid: Use explicit `HEAD`.
  - Source: Setup recon command behavior on 2026-06-04.

- Gotcha: TUI render layers should not reimplement domain calculations.
  - Impact: UI changes can silently diverge from domain/planner behavior.
  - How to avoid: Route file loading through `src/tui/data_loader.py` and keep widgets/renderers presentation-only.
  - Source: `src/tui/AGENTS.md`, `src/tui/mixins/AGENTS.md`.

## Current Recon Snapshot

This snapshot is evidence from local `HEAD` on 2026-06-04. Re-run before using it as current fact.

- Repo vitals: 353 commits, first commit 2026-04-15, latest commit 2026-06-04, 250 branches, all-time analysis window.
- Contributors: 3 total, 3 active in the last 3 months. Top authors: `tinker495` 258 commits, `kh-mo` 23 commits, `KyuSeok Jung` 1 commit.
- Momentum: 97 commits in 2026-04, 212 in 2026-05, 44 in 2026-06 so far.
- Firefighting commits: 0 matching `revert|hotfix|emergency|rollback` out of 353 commits.
- Top high-risk files from hotspot x bug-magnet overlap:
  - `tests/tui/test_app.py` - hotspot rank 1, bug-magnet rank 1, primary owner `tinker495`.
  - `tests/stowage/planner/spp/test_regression_spp_diagnostics_evaluator.py` - hotspot rank 2, bug-magnet rank 2, primary owner `tinker495`.
  - `src/tui/mixins/render_mixin.py` - hotspot rank 5, bug-magnet rank 3, primary owner `tinker495`.
  - `src/stowage/planner/spp/pipeline.py` - hotspot rank 6, bug-magnet rank 8, primary owner `tinker495`.

## Related Dashboards And Docs

| Source | Use It For | Caveats |
| --- | --- | --- |
| `docs/index.md` | Find repo docs and SSOT entry points | Re-read before documentation work |
| `docs/_meta/docs-contract.md` | Determine As-Is vs To-Be source authority | Does not validate every link by itself |
| `src/scripts/AGENTS.md` | SPP diagnostics and benchmark workflow | Run benchmark for current performance |
| Data warehouse, BI, team communication | Not connected during setup | Needed for business/product data analysis beyond local repo context |

## Open Questions

- Question: Which structured data warehouse, if any, should Data Analytics use for live business metrics?
  - Why it matters: Future metric diagnostics need current source-backed tables rather than repo-only context.
  - Best owner or source to check next: User source setup choice.

- Question: Which team communication source should Data Analytics search for recent decisions and owner notes?
  - Why it matters: Git/docs do not capture recent undocumented caveats.
  - Best owner or source to check next: Slack or Teams setup choice, or pasted thread links.

- Question: Should this repository semantic layer be refreshed weekly?
  - Why it matters: Git hotspots, branch state, and source docs drift quickly.
  - Best owner or source to check next: User automation preference.
