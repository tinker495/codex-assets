# Meta Clean Codebase Reference

Use this reference only after loading `SKILL.md`.

## What This Skill Is For

Behavior-preserving cleanup answers: "Can we make this cleaner while current behavior stays identical?"

Meta cleanup answers: "Is current behavior itself carrying obsolete structure, legacy compatibility, or shallow interfaces that the project should intentionally stop preserving?"

The output is not a patch. It is a ranked set of behavior-change candidates with enough evidence for the user or planner to choose a contract change.

## Candidate Taxonomy

### Legacy Interface Shell

Signal:
- An old name, import path, CLI flag, route, widget mode, config key, or public wrapper forwards to a newer canonical module.
- Tests assert the old path mostly to keep compatibility alive.

Same-behavior gate:
- Existing callers still use the old surface.
- The compatibility promise may be public.

Meta-clean question:
- "Can the old interface be removed after a migration note, deprecation window, or caller update?"

Recommended action after approval:
- Move tests to the canonical interface.
- Delete the alias or wrapper.
- Update docs and release notes if user-facing.

### One-Adapter Seam

Signal:
- A seam exists but has exactly one adapter.
- Callers pay the interface cost, but no runtime variation, test variation, or product variation exists.

Same-behavior gate:
- The abstraction is currently observable through injection points, configs, or tests.

Meta-clean question:
- "Should this seam collapse until a second real adapter exists?"

Recommended action after approval:
- Inline the adapter into the owning module.
- Keep only the smallest constructor or function interface callers need.

### Mirror Model

Signal:
- A DTO, dataclass, schema, or view model duplicates another model field-for-field.
- Conversion code contains no validation, invariant, ordering, or vocabulary translation.

Same-behavior gate:
- Tests or callers expect both shapes to exist.

Meta-clean question:
- "Which model is canonical, and can the mirror shape disappear?"

Recommended action after approval:
- Move callers to the canonical model.
- Delete conversion-only tests or rewrite them as boundary validation tests.

### Alternate Mode Drift

Signal:
- Flags, modes, strategy switches, feature toggles, environment switches, or compatibility branches preserve two ways to do the same job.
- One path is canonical in practice; the other exists because removing it would change behavior.

Same-behavior gate:
- Some test, CLI, UI path, config, or fixture still selects the non-canonical mode.

Meta-clean question:
- "Can the project choose one canonical behavior and remove the alternate mode?"

Recommended action after approval:
- Update fixtures and docs to the canonical mode.
- Delete non-canonical branches and tests that only prove the old choice.

### Fallback Compatibility Path

Signal:
- Fallback-like code is grounded enough that `$ai-slop-cleaner` may preserve it: version compatibility, external data variance, fail-safe behavior, or migration tolerance.
- It still adds a second execution path that harms locality.

Same-behavior gate:
- Removing it changes how missing, malformed, old, or external inputs behave.

Meta-clean question:
- "Should the boundary fail fast or require migration instead of accepting this fallback?"

Recommended action after approval:
- Replace fallback behavior with explicit validation or migration.
- Preserve error evidence.
- Update tests to assert the new boundary contract.

### Test-Pinned Past

Signal:
- Tests keep a removed design alive by asserting old imports, names, loose errors, duplicated defaults, or transitional behavior.
- Production code exists mostly to satisfy those tests.

Same-behavior gate:
- The test suite defines the old behavior as required.

Meta-clean question:
- "Are these tests describing the desired contract, or only guarding history?"

Recommended action after approval:
- Rewrite tests against the canonical contract before deleting production code.

## Scoring

Score each candidate from 0 to 3 in each dimension:

- Deletion leverage: how much caller knowledge, branching, or code disappears.
- Locality gain: how much change/debug knowledge concentrates.
- Canonical clarity: how obvious the surviving behavior is.
- Migration tractability: how bounded the call-site and test updates are.
- Risk containment: how well users, data, APIs, and workflows are understood.

Recommendation strength:
- **Strong**: total 12+ and no unknown public dependency.
- **Worth exploring**: total 8-11 or one material unknown.
- **Speculative**: total under 8 or multiple unknowns.

Do not overfit the score. Evidence and the same-behavior gate matter more than arithmetic.

## HTML Report Shape

For broad scans, write a self-contained HTML file to:

```text
<tmpdir>/meta-clean-codebase-<timestamp>.html
```

Use the OS temp directory from `$TMPDIR`, `%TEMP%`, or `/tmp`. Do not write the report into the repository unless the user asks.

Recommended sections:

1. Scope and evidence base.
2. Candidate map grouped by ownership area.
3. Candidate cards.
4. Behavior-change ledger.
5. Top recommendation.
6. Open decisions.

Card fields:

```text
Candidate: [short name]
Strength: Strong | Worth exploring | Speculative
Files: [path:line]
Same-behavior gate: [current behavior that blocks deletion]
Why meta-clean: [why preserving that behavior may be wrong]
Canonical behavior: [what remains]
Deletion path: [tests, callers, docs, ADRs]
Risk: [known dependency or unknown]
Decision question: [one exact question]
```

## Markdown Report Shape

Use this for narrow scans or chat responses:

```text
META CLEAN CODEBASE REPORT
==========================

Scope: [paths, branch diff, or subsystem]
Evidence: [commands, files, docs]
Mode: read-only proposal

Top Recommendation:
- [candidate] - [why first]

Candidates:
1. [candidate]
   Files: [path:line]
   Same-behavior gate: [blocker]
   Why meta-clean: [reason]
   Proposed canonical behavior: [survivor]
   Deletion path: [steps]
   Risk: [risk]
   Strength: [Strong | Worth exploring | Speculative]

Behavior-Change Questions:
- [exact approval question]
```

## What Not To Do

- Do not present ordinary dead code as meta cleanup. Dead code belongs to `$ai-slop-cleaner`.
- Do not propose deletion just because a name is ugly.
- Do not ignore ADRs. If a candidate contradicts an ADR, say so and explain why reopening it may be justified.
- Do not hide behavior changes inside "refactor" wording.
- Do not add TODO markers as output. Report deferred findings outside source code.
- Do not keep stale tests green by preserving the stale interface; after approval, migrate the tests to the canonical behavior.
