# Grepai Query Pack for Doc Refresh

Run these queries in order and keep `--json` enabled.

## 0: Noise control preflight (required)

`grepai search` is discovery-only. Always filter first and ground with `trace graph + rg`.

```bash
python /Users/mrx-ksjung/.codex/skills/refresh-branch-docs/scripts/collect_doc_refresh_context.py --base main --format json > /tmp/doc_ctx.json
jq '.changed_files[]' /tmp/doc_ctx.json | head
```

After any search, filter noisy hits immediately:

```bash
grepai search "<query>" --json --compact \
  | jq 'map(select(.file_path|startswith("src/"))) | map(select(.file_path|contains("/stowage/") or contains("/tui/"))) | .[0:15]'
```

When docs/tests evidence is needed, query those explicitly in separate commands.

## Pass 1: Surface map

```bash
grepai search "AnomalyReport AnomalyMixin overlay flags stowage plan" --json --compact \
  | jq 'map(select(.file_path|startswith("src/"))) | .[0:10]'
grepai search "rotation history anomaly tiers render step" --json --compact \
  | jq 'map(select(.file_path|startswith("src/"))) | .[0:10]'
grepai search "TUI overlay tooltip rotation detail state" --json --compact \
  | jq 'map(select(.file_path|startswith("src/"))) | .[0:10]'
grepai search "hard constraints objective function canonical" --json --compact \
  | jq 'map(select(.file_path|startswith("docs/"))) | .[0:10]'
```

## Pass 2: Control flow

```bash
grepai trace graph "prepare_anomaly_tiers_for_plans" --depth 6 --json
grepai trace graph "build_cell_context" --depth 6 --json
grepai trace graph "set_step_data" --depth 6 --json
```

If a root symbol is unresolved, trace a nearby confirmed symbol first, then retry.
If search results stay noisy, skip extra broad search and derive roots with `rg`:

```bash
rg -n "AnomalyReport|prepare_anomaly_tiers_for_plans|build_cell_context|set_step_data|overlay_additions_by_port" src
```

## Pass 3: Data flow and contracts

```bash
grepai search "slot_detail overlay_flags_for_slot anomaly_tiers_by_bay" --json --compact \
  | jq 'map(select(.file_path|startswith("src/"))) | .[0:10]'
grepai search "RotationOverlayAdditions overlay_additions_by_port" --json --compact \
  | jq 'map(select(.file_path|startswith("src/"))) | .[0:10]'
grepai search "AnomalySpec slots_source details_source" --json --compact \
  | jq 'map(select(.file_path|startswith("src/"))) | .[0:10]'
rg -n "slot_detail|overlay_flags_for_slot|anomaly_tiers_by_bay|overlay_additions_by_port|slots_source|details_source" src docs
```

Focus on:
- dataclass fields and optionality
- dict key shape and slot key format
- cross-module assumptions between stowage/rotation/tui

## Pass 4: Edge and test evidence

```bash
grepai search "warning fallback default invalid" --json --compact
grepai search "test_anomaly test_overlay test_rotation_history_render" --json --compact
rg -n "warning|fallback|default|invalid" src
rg -n "test_anomaly|test_overlay|test_rotation_history_render|prepare_anomaly_tiers_for_plans" tests
```

Map each doc claim to:

1. One code anchor.
2. One test/spec anchor.

## Stability check

Re-run one control-flow query and one data-flow query after drafting doc updates.
If new symbols appear in rerun, revise docs before finalizing.

## Evidence gate (required)

Do not keep a documentation claim unless it has:

1. One `trace graph` call-path anchor.
2. One `rg -n` symbol anchor.
3. One test/spec anchor when available.
