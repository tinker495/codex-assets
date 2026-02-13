# Doc Update Matrix

Use this matrix to map changed code paths to documentation refresh targets.
Start with `collect_doc_refresh_context.py` output, then expand manually.

## Primary mapping

| Changed area prefix | Primary docs to refresh | What to verify |
| --- | --- | --- |
| `src/stowage/dataclasses/stowage_plan/` | `docs/reference/data-structure/stowage-plan.md`, `docs/reference/data-structure/calculators.md`, `docs/reference/anomaly/aggregation.md`, `docs/reference/constraints/hard-constraints.md`, `docs/reference/constraints/objective-functions.md`, `docs/reference/data-structure/index.md` | Anomaly model, calculator ownership, overlay priority, type/dataclass fields |
| `src/stowage/dataclasses/rotation_history/` | `docs/reference/data-structure/rotation-history.md`, `docs/reference/anomaly/aggregation.md`, `docs/reference/data-structure/index.md` | Port-step anomaly projection, phase filters, render assumptions |
| `src/stowage/dataclasses/vessel_define/` | `docs/reference/data-structure/cargo.md`, `docs/reference/data-structure/infrastructure.md`, `docs/reference/data-structure/stability.md`, `docs/reference/data-structure/index.md` | Bay/row/tier mappings, hatch-cover semantics, derived constraints |
| `src/stowage/config/` | `docs/reference/constraints/hard-constraints.md`, `docs/reference/constraints/objective-functions.md`, `docs/reference/data-structure/index.md` | Constraint constants, policy boundaries, naming consistency |
| `src/tui/` | `docs/reference/data-structure/stowage-plan.md`, `docs/reference/data-structure/rotation-history.md`, `docs/reference/data-structure/infrastructure.md`, `docs/reference/data-structure/index.md` | UI state shape, overlay payload, tooltip/detail rendering contracts |
| `scripts/`, `.github/workflows/` | `docs/guides/development.md`, `docs/guides/testing.md`, `docs/guides/code-search.md`, `docs/index.md` | Command contract, docs-check wiring, CI execution paths |

## Harness map/contract docs (always consider)

- `AGENTS.md`
- `docs/index.md`
- `docs/_meta/docs-contract.md`

Refresh these when:
- doc navigation structure changes
- local `src/**/AGENTS.md` inventory changes
- As-Is/To-Be boundary policy changes
- docs integrity gates (`docs-check`, CI) change

## Constraint and objective docs

Update these docs whenever rule semantics, marker conditions, or scoring terms change:

- `docs/reference/constraints/hard-constraints.md`
- `docs/reference/constraints/objective-functions.md`
- additional canonical objective docs that actually exist

Check:
- renamed/removed rule IDs or helper names
- changed input/output payload fields
- changed precedence or conflict resolution logic

## Evidence checklist per doc

For each edited doc, keep at least two anchors:

1. Code anchor: file path + symbol (function/class/method).
2. Verification anchor: related test path or spec/API reference.

Preferred proof shape:

1. `trace graph` anchor for call-path/context.
2. `rg -n` anchor for exact symbol/location.

Example anchor format:

- Code: `src/stowage/dataclasses/stowage_plan/anomaly.py::AnomalyReport`
- Test: `tests/calculators/test_anomaly_basic.py::test_*`
