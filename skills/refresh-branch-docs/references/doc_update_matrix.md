# Doc Update Matrix

Use this matrix to map changed code paths to documentation update targets. Start with the auto-generated set from `collect_doc_refresh_context.py`, then expand manually using this guide.

## Primary mapping

| Changed area prefix | Primary docs to refresh | What to verify |
| --- | --- | --- |
| `src/stowage/dataclasses/stowage_plan/` | `docs/data-structure/stowage-plan.md`, `docs/data-structure/calculators.md`, `docs/anomaly-aggregation-analysis.md` | Anomaly model, calculator ownership, overlay priority, type/dataclass fields |
| `src/stowage/dataclasses/rotation_history/` | `docs/data-structure/rotation-history.md`, `docs/anomaly-aggregation-analysis.md`, `docs/data-structure-analysis.md` | Port-step anomaly projection, phase filters, render assumptions |
| `src/stowage/dataclasses/vessel_define/` | `docs/data-structure/cargo.md`, `docs/data-structure/infrastructure.md`, `docs/data-structure/stability.md` | Bay/row/tier mappings, hatch-cover semantics, derived constraints |
| `src/tui/` | `docs/data-structure/stowage-plan.md`, `docs/data-structure/rotation-history.md`, `docs/data-structure/infrastructure.md` | UI state shape, overlay payload, tooltip/detail rendering contracts |

## Constraint and objective docs

Update these docs whenever rule semantics, marker conditions, or scoring terms changed in code:

- `docs/HardConstraints_Constraint_API_Spec.md`
- `docs/Raw_objectiveFunction_Canonical_List.md`
- any additional objective canonical docs that actually exist in the current repo

Check:
- renamed/removed rule IDs or helper names
- changed input/output payload fields
- changed precedence or conflict resolution logic

## Evidence checklist per doc

For each edited doc, keep at least two evidence anchors:

1. Code anchor: file path + symbol (function/class/method).
2. Verification anchor: related test path or spec/API reference.

Preferred proof shape for reliability:

1. `trace graph` anchor for call-path/context.
2. `rg -n` anchor for exact symbol/location.

Example anchor format:

- Code: `src/stowage/dataclasses/stowage_plan/anomaly.py::AnomalyReport`
- Test: `tests/calculators/test_anomaly_basic.py::test_*`
