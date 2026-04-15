# Non-Test Reduction Queries

## Purpose
Use these focused queries to detect fragmented, under-abstracted, or duplicated non-test code that can be removed or consolidated to improve concept alignment, including justified medium/high-risk structural refactors.

## Scope Rules
- Prioritize core runtime paths (`src/` domain/application modules and related non-test runtime modules).
- Ignore `tests/`, `**/test_*.py`, `**/*_test.py`, `**/conftest.py`.
- Ignore script/CLI glue paths by default: `src/scripts/`, `scripts/`, `tools/`, `bin/`, `**/management/commands/**`.
- Include script paths only when the user explicitly asks for script minimization.
- Treat `probe search` as discovery only; validate with `probe extract` and `rg -n`.

## Query Pack
Run each query with a small result cap and filter noisy retries early.

```bash
probe search "duplicated normalization or mapping logic in stowage planning path" ./src --max-results 10
probe search "single-call helper wrappers that only forward arguments" ./src --max-results 10
probe search "repeated anomaly classification branches across modules" ./src --max-results 10
probe search "duplicate conversion or parsing paths with same field extraction" ./src --max-results 10
probe search "split responsibilities causing repeated condition checks in rotation history" ./src --max-results 10
probe search "intent-equivalent implementations with different method names" ./src --max-results 10
probe search "multi-key attribute access variants for same domain field" ./src --max-results 10
```

## Trace and Verify
After discovery, anchor each candidate with one extracted block and one exact symbol hit.

```bash
probe extract src/path/to/file.py#ExactFunctionOrClass_method
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
