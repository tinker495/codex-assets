# Ultraclean — Orchestration

The main agent owns scope, partitioning, integration, verification, and the stop decision. It may
also act as the single writer when capacity is constrained, but it must not approve its own work.
The independent reviewer pass is the safety gate.

## 0. Detect scope

```
bash <skill>/scripts/ultraclean-scope.sh [full|branch] [--base <ref>]
```
- No mode arg → auto-detected from branch (`main`/`master` → `full`, else `branch`).
- `branch` mode needs a base ref (default `origin/main`). Run `git fetch origin` first if it may be stale.
- Read `MODE`, `BRANCH`, `BASE`, and the dir/file signals from stdout.

## 1. Build the smallest useful disjoint partition set

**Invariant: every in-scope file belongs to exactly one partition.** Overlap = parallel-edit corruption.

**branch mode** — from `TOUCHED DIRS` (counts are **direct files, non-recursive** — "folder level"):
- The review unit is the *folder*, not the changed line. Each partition owns one or more touched folders; its review surface is **every direct file in those folders**, so a cleaner sees the siblings of the changed files, not just the diff. Non-recursive on purpose: a touched parent dir does not swallow its child dirs (they appear as their own `TOUCHED DIRS` rows), which keeps partitions disjoint.
- Group folders under the same module (shared `AGENTS.md`) into one partition for coherent ownership. You may deliberately fold a parent + its child dirs into one module-partition — still disjoint at the file level.
- Keep a coherent folder as one partition when subdivision would add coordination without improving review quality.

**full mode** — from `CANDIDATE MODULE DIRS`:
- Roll leaf dirs up to coherent modules using top-level roots and `AGENTS.md` locations.
- Create disjoint partitions covering the **whole** tracked source tree, balanced by file count.
- Root-level/shared files (configs, top-level scripts) go to exactly one dedicated partition.

### Sizing — scale with scope and capacity
- Target coherent one-pass units of roughly 15–25 source files, but do not split a small or tightly coupled module just to create workers.
- Reserve the leader slot. Wave width must not exceed currently available child slots; batch remaining partitions.
- Reserve a slot for a scavenger only when the scope has multiple partitions or cross-module risk. A later reviewer may reuse a completed read-only slot.

## 2. Execution wave — bounded cleaners plus optional scavenger

Launch only disjoint writes in parallel. Keep cross-partition writes for a later single-writer pass.

**Cleaners** (one per partition, deep + narrow):
```
Codex native executor, edits its partition only:
  prompt = <SUBAGENT-BRIEF.md cleaner brief, PARTITION + GATES + DATE filled>
```
- Each returns an evidence-dense partition report (findings, auto-fixed ledger, report-only deferred findings, verification, partition Health Score).

**Scavenger** (optional, at most one, broad + shallow, **read-only**):
```
Codex native subagent in read-only posture:
  prompt = <SUBAGENT-BRIEF.md scavenger brief, full scope + partition map filled>
```
- Sweeps the **entire** scope at low depth for the cross-cutting risks no single partition can see (see `CHECKLIST.md` → "cross-cutting"). Because it makes **no edits**, it runs concurrently with the writing cleaners without any file-conflict risk.
- Returns a cross-cutting findings list (Iron Law form), each tagged with the partitions it spans and a SAFE/RISKY call (cross-partition fixes are RISKY by definition and must remain report-only unless the post-review writer pass owns them).

When used, the scavenger runs once over the full scope and is collected before consolidation. Do not split it by sub-scope because that recreates the blind spot it exists to remove.

## 3. Review all fixes (writer ≠ reviewer)

After writers and any optional scavenger report, fire independent reviewer(s):
- Assign so **no reviewer reviews a partition it cleaned**. One reviewer is sufficient for most scopes; add review batches only when the diff cannot be reviewed coherently in one pass.
- Reviewer runs the `SUBAGENT-BRIEF.md` reviewer brief over the actual diff (`git diff`), the cleaner reports, and the scavenger findings. Top priority: catch any **behavior change a "cleanup" introduced**; then leftover dead code, missed dedup, surviving needless wrappers, high-risk changes that were auto-fixed instead of kept report-only, missing tests, new TODO/FIXME/slop-clean markers, and cross-partition inconsistency.
- **Required review items:** (1) inspect the diff for newly added `TODO`, `FIXME`, `XXX`, `HACK`, `slop-clean`, or placeholder comments and require removal or a real fix; (2) when a scavenger ran, judge every cross-cutting finding and route it to fix-now or report-only. Both feed the synthesis writer pass below.
- Verdict: `APPROVED`, `APPROVED-WITH-REMOVALS`, or `CHANGES-REQUIRED`. With the comprehensive view (diff + cleaner reports + scavenger findings), the reviewer also lists **pre-report removals** — cross-cutting dead code / duplication / slop it judges should be deleted or fixed *now*, before the report.

### Pre-report writer pass + remediation (MANDATORY, bounded)
**Always run this step — never skip it because the verdict looks clean.** Synthesize the review pass output into ONE concrete fix-list and apply it as code: newly added TODO/FIXME/slop-clean marker removals, fixable deferred findings, the approved scavenger findings, the pre-report removals, and any `CHANGES-REQUIRED` follow-ups.
- Assign one writer, which may be the leader or an earlier cleaner but never the reviewer. Keep cross-partition edits single-threaded, behavior-preserving, and protected by a regression lock.
- Re-verify the gates and run a quick confirming re-review of the new diff.
- Cap at **2 cycles**. If still unresolved, stop and report the open items rather than looping (ultrawork stop condition).
- Only if the synthesized fix-list is **honestly empty** is this pass a no-op — and the report must say so explicitly, never skip it silently.

Only after this settles does step 4 write the report — so the synthesized, reviewer-validated fixes land **before** the report, not as source-level TODOs.

## 4. Final verification + consolidate + report

**Verify (lightweight, ultrawork):** run the detected full gates once — lint + typecheck + affected
tests (this repo: `make lint`, scoped `make test PYTEST_ARGS="…"`, `make docs-check`; else
`package.json` scripts, etc.). Confirm: gates green, no new errors, reviewer `APPROVED`.

**Consolidate** per-partition reports + scavenger findings + reviewer verdict using the Health Score
formula in `CHECKLIST.md`. Report sections:
- Overall Health Score (+ trend if `.brooks-lint-history.json` exists)
- Per-partition summary (findings, fixes, partition score)
- **Auto-fixed ledger** (file → change)
- **Post-review applied fixes** (from the mandatory synthesis writer pass — deferred findings promoted to fixes + approved scavenger fixes + removals; state "none — empty fix-list" if it was a no-op)
- **Deferred findings ledger** (file:line or symbol -> severity + description + why not safely fixed now) — report-only; do not add source comments
- **Scavenger cross-cutting findings** (spanning partitions)
- Verification matrix (gate → PASS/FAIL)
- Residual risks + recommended fix order

**Write to** the first that applies: `report/ultraclean-<YYYY-MM-DD>.md` (if `report/` exists) →
`.omc/reports/ultraclean-<YYYY-MM-DD>.md` (if `.omc/` exists) → else print inline. Stamp the date
with `date +%F`.

## Failure handling

- Not a git tree / no base ref → abort with the script's message (ask the user for `--base`).
- A partition's quality gate fails → that cleaner backs out the offending change (deletion-first edits revert cleanly), keeps the rest, and reports the failure; it does **not** force the change through.
- Generated / vendored / lock / minified files → skipped (see `CHECKLIST.md`), noted in the report.
- Trivial scope (for example docs-only or one small module) → keep one coherent writer scope plus independent review, or report that there is nothing meaningful to clean.
