---
name: ultraclean
description: >-
  Parallel multi-agent codebase cleanup engine. Partitions the work across 3+ frontier (non-spark/non-mini) subagents that
  each diagnose with brooks-review decay risks and apply ai-slop-cleaner deletion-first fixes
  (safe = auto-fix, risky = report-only deferred finding; never create TODO/slop-clean markers),
  plus one shallow whole-scope "scavenger" that catches
  cross-partition slop, closed by a separate reviewer pass and a consolidated report. Use when the
  user asks for $ultraclean / "ultraclean", wants to clean / deslop / anti-slop an entire codebase or a branch's
  changes vs origin/main, or asks for a parallel anti-slop sweep. full mode (default on main)
  partitions the whole codebase; branch mode (default off main) reviews every file in the folders
  the diff touches, not just the changed lines.
---

# Ultraclean

Composite cleanup engine = **ultrawork** (parallel partitioned execution) × **ai-slop-cleaner**
(deletion-first, regression-safe writer) × **brooks-review** (decay-risk diagnosis). Runs fully
autonomously; the separate reviewer pass — not a human checkpoint — is the safety gate.

The objective is the cleanest safely verified repository state, not a list of cleanup wishes. Risk
is not a reason to create source-level TODO slop. Risk means: lock behavior, narrow the edit, route
it to a single-threaded writer pass, or leave the code unchanged and report the unresolved finding
outside the source tree.

## Modes (auto-detected from branch; override with an explicit arg)

| Mode | Default when | Scope |
|------|--------------|-------|
| `full` | on `main` / `master` | Entire codebase, partitioned by module/directory units |
| `branch` | on any other branch | Diff vs `origin/main`, **expanded to every file in each touched folder** — not just changed lines |

`ultraclean full` / `ultraclean branch` forces a mode. `ultraclean branch --base origin/develop` sets the base ref.

## Pipeline — partition → (parallel cleaners ∥ 1 scavenger) → review → report

0. **Scope** — `scripts/ultraclean-scope.sh` detects mode and emits raw git signals (changed files, touched dirs, candidate module dirs).
1. **Partition** — split the scope into **N ≥ 3 disjoint** units (every in-scope file owned by exactly one unit). Honor `AGENTS.md` module boundaries.
2. **Parallel wave** — fire together in one batch:
   - **N deep cleaners** (frontier subagent) — each diagnoses its partition, auto-fixes SAFE findings, records RISKY findings in its report only, verifies scoped gates, reports. *Deep but narrow.*
   - **1 shallow scavenger** (frontier subagent, **read-only**) — sweeps the **entire** scope for cross-partition slop the boundary-blind cleaners structurally cannot see: cross-module duplication, naming drift, dependency disorder, global dead code, inter-partition inconsistency. *Broad but shallow.* No edits ⇒ no write race with the cleaners.
3. **Review all fixes** — ≥1 *independent* frontier reviewer (a partition's cleaner ≠ its reviewer) does a comprehensive review of the produced diff + cleaner reports + scavenger findings. **Two review items are mandatory, not optional: (a) TODO prohibition audit** — reject any newly added `TODO`, `FIXME`, or `slop-clean` source marker and promote fixable deferred findings into the writer pass; **(b) scavenger report review** — judge and route each cross-cutting finding (fix now vs report-only deferred finding). The reviewer synthesizes both into one fix-list, and a fresh single-threaded writer pass **always** applies it before the report (then re-verifies) — synthesizing the review results into code changes is a required step, not a conditional one; only a genuinely empty list is a no-op (bounded retries).
4. **Report** — consolidate: Health Score, per-partition summary, auto-fixed ledger, report-only deferred findings, scavenger cross-cutting findings, verification matrix, residual risks, recommended fix order.

See `ORCHESTRATION.md` (process detail), `SUBAGENT-BRIEF.md` (cleaner / scavenger / reviewer briefs), `CHECKLIST.md` (decay risks + slop taxonomy + SAFE/RISKY gate + Health Score).

## Hard rules

- **Behavior-preserving only.** An observable output change from a *cleanup* is a defect — back it out, don't guard it. Lock behavior with scoped regression tests before editing.
- **No TODO slop.** Never create new `TODO`, `FIXME`, `XXX`, `HACK`, `slop-clean`, or placeholder comments as cleanup output. Existing markers are cleanup targets; fix/delete them when safe, otherwise leave existing code unchanged and report the finding with evidence.
- **Disjoint partitions; cleaners edit only their own files.** Cross-partition / structural changes are always RISKY -> report-only deferred finding or post-review writer pass, never auto-fixed mid-wave.
- **Scavenger is read-only and whole-scope.** It produces findings, never edits.
- **Writer ≠ reviewer.** No subagent approves its own work.
- **Cleaner fleet scales with scope** — `N = max(3, ⌈in-scope source files / ~20⌉)`, always ≥ 3 (subdivide the largest unit if natural units < 3). Concurrency tracks scope; one whole-scope scavenger (lens-split only for very large scopes, never by sub-scope).
- **Codex native subagents, frontier tier only.** All lanes use Codex native subagents at mainstream/frontier tier — never spark, mini, nano, or low-tier fast-lane models. If native subagents are unavailable, run the same lanes sequentially, still keeping writer ≠ reviewer.
- **Read `AGENTS.md` ancestors first** for every file a subagent touches; auto-detect gates (`make lint` / `make test`, `package.json` scripts, …).
- **Deletion over addition; no new dependencies; one smell-pass at a time.** The cut bar is the ponytail ladder (YAGNI → reuse → stdlib → native → installed dep → one line); "clean" = low decay risk **and** `net: -lines/-deps`. See `CHECKLIST.md`.
