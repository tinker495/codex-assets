# Source Inventory

## Coverage

- Coverage level: Limited
- Sources checked: Local repo docs, local AGENTS rules, `CONTEXT.md`, and git history at local `HEAD` on 2026-06-04.
- Missing high-value lanes: Data warehouse or table catalog, verified dashboards, team communication, product analytics tools, recurring KPI reports, current `spp-bench` artifacts, and GitHub issue/PR state.
- Rejected or lower-confidence candidates: Ambient connector availability was not used as source evidence; no external connector reads were performed during setup.

## Sources

| Source | Type | Locator | Connector Or Tool | Permission Status | Last Checked | Supports | Gaps Or Caveats | Automation Eligible | Update Boundary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Root agent rules | Local documentation | `/Users/mrx-ksjung/project/snk2501o-sinokor-placement-optimization/AGENTS.md` | Local filesystem | Available | 2026-06-04 | Repo rules, validation commands, no-CCASP boundary, docs reading order | User-provided prompt contained the current file body; re-read from disk before editing decisions | Yes | Draft proposed updates only |
| Documentation index | Local documentation | `/Users/mrx-ksjung/project/snk2501o-sinokor-placement-optimization/docs/index.md` | Local filesystem | Available | 2026-06-04 | Docs entry points, As-Is vs To-Be map, SPP docs deletion note | Does not replace live code inspection | Yes | Draft proposed updates only |
| Docs contract | Local documentation | `/Users/mrx-ksjung/project/snk2501o-sinokor-placement-optimization/docs/_meta/docs-contract.md` | Local filesystem | Available | 2026-06-04 | As-Is and To-Be evidence rules | Does not certify individual docs are current | Yes | Draft proposed updates only |
| Domain context | Local documentation | `/Users/mrx-ksjung/project/snk2501o-sinokor-placement-optimization/CONTEXT.md` | Local filesystem | Available | 2026-06-04 | Canonical domain language and planner-stage boundaries | Broad domain glossary; verify implementation details in code/tests | Yes | Draft proposed updates only |
| TUI rules | Local documentation | `/Users/mrx-ksjung/project/snk2501o-sinokor-placement-optimization/src/tui/AGENTS.md` | Local filesystem | Available | 2026-06-04 | TUI ownership, render boundaries, scroll rules, planning tabs, validation points | Applies only to TUI subtree | Yes | Draft proposed updates only |
| TUI mixin rules | Local documentation | `/Users/mrx-ksjung/project/snk2501o-sinokor-placement-optimization/src/tui/mixins/AGENTS.md` | Local filesystem | Available | 2026-06-04 | Render mixin responsibilities, snapshot dispatch, verification points | Applies only to TUI mixin subtree | Yes | Draft proposed updates only |
| SPP rules | Local documentation | `/Users/mrx-ksjung/project/snk2501o-sinokor-placement-optimization/src/stowage/planner/spp/AGENTS.md` | Local filesystem | Available | 2026-06-04 | Pure SPP boundary, entry points, output contract, verification commands | SPP performance still needs fresh benchmark artifacts | Yes | Draft proposed updates only |
| Pipeline rules | Local documentation | `/Users/mrx-ksjung/project/snk2501o-sinokor-placement-optimization/src/stowage/planner/pipeline/AGENTS.md` | Local filesystem | Available | 2026-06-04 | Pipeline snapshots, pure/materialized boundary, oracle rules | Applies to orchestration, not stage calculation internals | Yes | Draft proposed updates only |
| Scripts rules | Local documentation | `/Users/mrx-ksjung/project/snk2501o-sinokor-placement-optimization/src/scripts/AGENTS.md` | Local filesystem | Available | 2026-06-04 | `uv run spp-bench` as SPP diagnostics SSOT, CLI boundaries | No benchmark command was run during setup | Yes | Draft proposed updates only |
| Git history recon | Git metadata | Local repo `HEAD` | `git` CLI | Available | 2026-06-04 | Hotspots, bug-magnet heuristic, momentum, ownership | Stale after new commits; bug magnet uses commit-message grep heuristic | Yes | Regenerate semantic-layer references from fresh commands |
