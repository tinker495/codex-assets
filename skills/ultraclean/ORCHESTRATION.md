# Ultraclean — Orchestration

The main agent is the **orchestrator**. It never edits source itself: it detects scope, builds
partitions, dispatches Codex native subagents, runs the reviewer gate, and consolidates. Fully
autonomous (no human checkpoint) — the reviewer pass is the safety gate. If Codex native subagents
are unavailable, run the same lanes sequentially and keep the reviewer pass separate from writer work.

## 0. Detect scope

```
bash <skill>/scripts/ultraclean-scope.sh [full|branch] [--base <ref>]
```
- No mode arg → auto-detected from branch (`main`/`master` → `full`, else `branch`).
- `branch` mode needs a base ref (default `origin/main`). Run `git fetch origin` first if it may be stale.
- Read `MODE`, `BRANCH`, `BASE`, and the dir/file signals from stdout.

## 1. Build N ≥ 3 disjoint partitions

**Invariant: every in-scope file belongs to exactly one partition.** Overlap = parallel-edit corruption.

**branch mode** — from `TOUCHED DIRS` (counts are **direct files, non-recursive** — "folder level"):
- The review unit is the *folder*, not the changed line. Each partition owns one or more touched folders; its review surface is **every direct file in those folders**, so a cleaner sees the siblings of the changed files, not just the diff. Non-recursive on purpose: a touched parent dir does not swallow its child dirs (they appear as their own `TOUCHED DIRS` rows), which keeps partitions disjoint.
- Group folders under the same module (shared `AGENTS.md`) into one partition for coherent ownership. You may deliberately fold a parent + its child dirs into one module-partition — still disjoint at the file level.
- If touched folders < 3, subdivide the largest folder's file list into 3 disjoint groups.

**full mode** — from `CANDIDATE MODULE DIRS`:
- Roll leaf dirs up to coherent modules using top-level roots and `AGENTS.md` locations.
- Create disjoint partitions covering the **whole** tracked source tree, balanced by file count.
- Root-level/shared files (configs, top-level scripts) go to exactly one dedicated partition.

### Sizing — scale with scope
- **Partitions** `N = max(3, ⌈in-scope source files / ~20⌉)` — bigger scope → more partitions, each still one-pass-sized (~15–25 files).
- **Concurrency scales with scope** (no fixed cap): dispatch all N at once when small; for large N, batch into waves whose width tracks scope and host capacity — widen for big repos, narrow if the host is constrained — until every partition is done.

## 2. Parallel wave — N cleaners ∥ 1 scavenger

Fire the whole wave in **one batch** (parallel subagents).

**Cleaners** (one per partition, deep + narrow):
```
Codex native subagent (frontier tier — never spark/mini/nano), edits its partition only:
  prompt = <SUBAGENT-BRIEF.md cleaner brief, PARTITION + GATES + DATE filled>
```
- All frontier tier (non-spark/non-mini). ≥ 3.
- Each returns an evidence-dense partition report (findings, auto-fixed ledger, report-only deferred findings, verification, partition Health Score).

**Scavenger** (exactly one, broad + shallow, **read-only**):
```
Codex native subagent in read-only posture (frontier tier):
  prompt = <SUBAGENT-BRIEF.md scavenger brief, full scope + partition map filled>
```
- Sweeps the **entire** scope at low depth for the cross-cutting risks no single partition can see (see `CHECKLIST.md` → "cross-cutting"). Because it makes **no edits**, it runs concurrently with the writing cleaners without any file-conflict risk.
- Returns a cross-cutting findings list (Iron Law form), each tagged with the partitions it spans and a SAFE/RISKY call (cross-partition fixes are RISKY by definition and must remain report-only unless the post-review writer pass owns them).

The scavenger runs **once over the full scope** (not per wave); launch it in the first wave and collect it before consolidation. For very large scopes it may split by cross-cutting **lens** — duplication/naming · dependency direction · global reachability — where **each lens still sweeps the entire scope**; never split the scavenger by sub-scope (that recreates the blind spot it exists to remove).

## 3. Review all fixes (writer ≠ reviewer)

After cleaners + scavenger report, fire independent reviewer(s):
- Assign so **no reviewer reviews a partition it cleaned**. ≤ 6 partitions → one reviewer over the whole produced diff; more → `ceil(N/4)` reviewers over disjoint review-batches they did not author.
- Reviewer runs the `SUBAGENT-BRIEF.md` reviewer brief over the actual diff (`git diff`), the cleaner reports, and the scavenger findings. Top priority: catch any **behavior change a "cleanup" introduced**; then leftover dead code, missed dedup, surviving needless wrappers, high-risk changes that were auto-fixed instead of kept report-only, missing tests, new TODO/FIXME/slop-clean markers, and cross-partition inconsistency.
- **Two review items are mandatory, not optional:** (1) **TODO prohibition audit** — inspect the diff for newly added `TODO`, `FIXME`, `XXX`, `HACK`, `slop-clean`, or placeholder comments and require removal or a real fix; (2) **Scavenger report review** — judge *every* scavenger cross-cutting finding for validity and route each (fix now vs report-only deferred finding). Both feed the mandatory synthesis writer pass below.
- Verdict: `APPROVED`, `APPROVED-WITH-REMOVALS`, or `CHANGES-REQUIRED`. With the comprehensive view (diff + cleaner reports + scavenger findings), the reviewer also lists **pre-report removals** — cross-cutting dead code / duplication / slop it judges should be deleted or fixed *now*, before the report.

### Pre-report writer pass + remediation (MANDATORY, bounded)
**Always run this step — never skip it because the verdict looks clean.** Synthesize the review pass output into ONE concrete fix-list and apply it as code: newly added TODO/FIXME/slop-clean marker removals, fixable deferred findings, the approved scavenger findings, the pre-report removals, and any `CHANGES-REQUIRED` follow-ups.
- Dispatch a **fresh** writer pass (Codex native subagent, frontier tier) scoped to that synthesized list — **single-threaded** for cross-partition edits (no parallel write race), behavior-preserving with a regression lock, never the reviewer or original cleaner editing-then-self-approving.
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
- Trivial scope (e.g., docs-only branch) → still run ≥ 3 light partitions + the scavenger, or report that there is nothing meaningful to clean.
