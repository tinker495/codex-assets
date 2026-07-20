---
name: ultraclean
description: >-
  Adaptive codebase cleanup engine for full repositories or branch-expanded scope. Partitions work when useful,
  diagnoses decay risks, and applies deletion-first behavior-preserving fixes
  (safe = auto-fix, risky = report-only deferred finding; never create TODO/slop-clean markers),
  optionally adds a shallow whole-scope scavenger for cross-partition slop,
  and closes with an independent reviewer pass and consolidated report. Use when the
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

## Pipeline — scope → adaptive writers and optional scavenger → review → report

0. **Scope** — `scripts/ultraclean-scope.sh` detects mode and emits raw git signals (changed files, touched dirs, candidate module dirs).
1. **Partition** — split the scope into the smallest useful set of disjoint ownership units. A narrow scope may stay single-owner; every in-scope file still belongs to exactly one unit. Honor `AGENTS.md` module boundaries.
2. **Execution wave** — use available native subagent slots without oversubscription. Run disjoint cleaners in parallel when that materially helps. Add one read-only whole-scope scavenger only for multi-partition or cross-module scope; otherwise the independent reviewer owns the broad check.
3. **Review all fixes** — at least one independent reviewer checks the produced diff and reports. The reviewer must audit behavior preservation, new `TODO` or placeholder markers, cross-boundary duplication, and every scavenger finding when a scavenger ran. A single writer applies the synthesized fix-list, then the reviewer or another independent verifier rechecks it. An empty list is an explicit no-op.
4. **Report** — consolidate: Health Score, per-partition summary, auto-fixed ledger, report-only deferred findings, scavenger cross-cutting findings, verification matrix, residual risks, recommended fix order.

See `ORCHESTRATION.md` (process detail), `SUBAGENT-BRIEF.md` (cleaner / scavenger / reviewer briefs), `CHECKLIST.md` (decay risks + slop taxonomy + SAFE/RISKY gate + Health Score).

## Hard rules

- **Behavior-preserving only.** An observable output change from a *cleanup* is a defect — back it out, don't guard it. Lock behavior with scoped regression tests before editing.
- **No TODO slop.** Never create new `TODO`, `FIXME`, `XXX`, `HACK`, `slop-clean`, or placeholder comments as cleanup output. Existing markers are cleanup targets; fix/delete them when safe, otherwise leave existing code unchanged and report the finding with evidence.
- **Disjoint partitions; cleaners edit only their own files.** Cross-partition / structural changes are always RISKY -> report-only deferred finding or post-review writer pass, never auto-fixed mid-wave.
- **Scavenger is read-only and whole-scope.** It produces findings, never edits.
- **Writer ≠ reviewer.** No subagent approves its own work.
- **Concurrency follows real capacity.** Reserve the leader slot, cap each wave to available child slots, and batch remaining partitions. Never create artificial partitions just to reach a worker count.
- **Role-fit over model hardcoding.** Use installed executor roles for bounded writers and reviewer or critic roles for independent review when routing is available; otherwise inherit native defaults. If subagents are unavailable, run a single writer pass and use the strongest independent verification surface available.
- **Read `AGENTS.md` ancestors first** for every file a subagent touches; auto-detect gates (`make lint` / `make test`, `package.json` scripts, …).
- **Deletion over addition; no new dependencies; one smell-pass at a time.** The cut bar is the ponytail ladder (YAGNI → reuse → stdlib → native → installed dep → one line); "clean" = low decay risk **and** `net: -lines/-deps`. See `CHECKLIST.md`.
- **Intent gates before structural consolidation.** Merge variants only when behavioral, conceptual, and physical compression gates pass. Do not force a line quota; stop when no safe evidence-backed reduction remains.
