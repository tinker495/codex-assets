# Commit Clustering Heuristics

Use this rubric when the user supplies a target commit count `N` and the branch must be rewritten into exactly `N` logical commits.

## Primary signals

Prioritize these signals in order:
1. user-visible intent or behavior change
2. dependency direction between modules
3. architectural boundary (`domain`, `adapter`, `ui`, `tooling`, `tests`, `docs`)
4. risk isolation for large refactors or data-shape changes
5. file locality

A directory boundary is only a hint. A single intent may legitimately cross multiple directories.

## Preferred cluster shapes

Prefer clusters that another engineer can review or revert independently:
- schema or dataclass reshapes
- core behavior changes
- adapter or integration wiring
- UI or presentation updates
- tests proving one specific runtime change
- docs or follow-up cleanup that is independently meaningful

## Merge-down rule when natural clusters exceed N

If natural clusters exceed `N`:
- merge the closest related clusters by dependency and reviewer context
- keep high-risk refactors isolated as long as possible
- merge docs/tests into the owning runtime change before merging unrelated runtime work together

Bad merge:
- mix parser rewrite and unrelated TUI polish only because both touch many files

Good merge:
- combine domain model cleanup with the calculator update that depends on it

## Split-up rule when natural clusters are fewer than N

If natural clusters are fewer than `N`:
- split by sub-intent inside the same area
- split by hunk with `git add -p` when one file spans multiple real intents
- split tests from runtime only when the tests are a meaningful standalone checkpoint

Do not split only to create cosmetic micro-commits such as:
- one commit per file with no independent intent
- one commit for formatting that is not reviewable on its own
- one commit for generated output without its source change

## Ordering rule

Create commits in dependency order. Prefer this sequence when it matches the change set:
1. foundational data shape or schema changes
2. core logic or domain behavior
3. adapters, loaders, or integrations
4. UI or presentation adjustments
5. tests, docs, or cleanup tied to the rewritten behavior

If the branch is mostly refactor work, order commits so each step leaves the program in a runnable and understandable state.

## Hunk-splitting checklist

Use `git add -p` only after answering yes to both:
- does this file contain more than one real intent?
- would separate commits improve review or rollback quality?

After hunk splitting:
- inspect staged diff with `git diff --cached`
- inspect remaining diff with `git diff`
- confirm no hunk was duplicated or dropped

## Commit message guidance

Write short intent-first subjects.

Good examples:
- `Normalize vessel summary parsing`
- `Split bay overlay validation from render flow`
- `Cover re-stacked planner flow with regression tests`

Avoid:
- `misc cleanup`
- `changes`
- `part 1`
- `WIP`
