# Non-Test Reduction Queries

## Purpose
Use these focused queries to detect fragmented, under-abstracted, or duplicated non-test code that can be removed or consolidated to improve concept alignment, including justified medium/high-risk structural refactors.

## Scope Rules
- Prioritize core runtime paths (`src/` domain/application modules and related non-test runtime modules).
- Ignore `tests/`, `**/test_*.py`, `**/*_test.py`, `**/conftest.py`.
- Ignore script/CLI glue paths by default: `src/scripts/`, `scripts/`, `tools/`, `bin/`, `**/management/commands/**`.
- Include script paths only when the user explicitly asks for script minimization.
- Treat `grepai search` as discovery only; validate with `grepai trace` and `rg -n`.

## Grepai Query Pack
Run each query with `--json --compact` and cap noisy retries.

```bash
grepai search "duplicated normalization or mapping logic in stowage planning path" --json --compact
grepai search "single-call helper wrappers that only forward arguments" --json --compact
grepai search "repeated anomaly classification branches across modules" --json --compact
grepai search "duplicate conversion/parsing paths with same field extraction" --json --compact
grepai search "split responsibilities causing repeated condition checks in rotation history" --json --compact
grepai search "intent-equivalent implementations with different method names" --json --compact
grepai search "multi-key attribute access variants for same domain field" --json --compact
```

## Trace and Verify
After discovery, anchor each candidate with one trace and one exact symbol hit.

```bash
grepai trace graph "<ExactFunctionOrClass.method>" --depth 4 --json
rg -n "<ExactFunctionOrSymbol>" src --glob '!src/scripts/**' --glob '!**/scripts/**' --glob '!**/tools/**' --glob '!**/bin/**'
```

## Candidate Scoring
Keep only candidates that satisfy all conditions:
- projected removable non-test LOC >= 20
- no mandatory external API behavior change
- replacement path is simpler or shorter
- candidate removes executable duplication or fragmentation (not comment/docstring-only edits)

Prioritize by `high conceptual misalignment + high removable LOC + manageable validation surface`.
Use low regression risk only as a tiebreaker, not as the primary ranking rule.
