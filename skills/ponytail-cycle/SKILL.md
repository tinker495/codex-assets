---
name: ponytail-cycle
description: "Run the SNK placement repository's named tests-to-src Ponytail Cycle: clean baseline, partitioned audits, adversarial proof, semantic commits, rebase, and Korean PR publication. Use for this full cycle, not ordinary cleanup or a read-only audit."
metadata:
  short-description: Run the tests-to-src Ponytail cleanup cycle
---

# Ponytail Cycle

Run the repository-specific two-round cleanup in `tests -> src` order. Rank findings by **maintenance context removed**: lines a maintainer no longer reads and file hops they no longer follow. Diff size is only a publication threshold and tie-breaker.

## Operating contract

1. Load `$ponytail:ponytail` at `full` level.
2. Work only in `makinarocks/snk2501o-sinokor-placement-optimization` or one of its worktrees.
3. Read the current root and target-directory `AGENTS.md` files plus `docs/guides/testing.md` before auditing. The repository files are the SSOT when this skill drifts.
4. Use native subagents for bounded audit, edit, and verifier lanes. The leader owns partition coverage, shared-file serialization, integration, commits, rebase, publication, and final evidence.
5. Keep one finding ledger with: ID, category, files/symbols, context reduction, evidence, surviving test `file::name` or tautology proof, edit owner, targeted result, adversarial result, mutation proof when used, disposition, and rejection reason.

Hard boundaries:

- Preserve assertions at equal strength: same input class, observable contract, and failure sensitivity.
- Preserve every `real_data` marker. Add no skip/xfail and weaken no assertion or threshold. A baseline skip proven invalid may be removed only by repairing the test path/fixture and running the formerly skipped test GREEN.
- Leave pinned benchmark gate data and `src/stowage/config/` untouched.
- Report src bugs without fixing them. Fix stale mocks against the real contract; do not add production defenses for test drift.
- Reject any src cleanup that changes production output. A diagnostic/evidence-export or TUI-debug shape may change only when the accepted finding names that surface and proves production decisions are unchanged.
- Treat lexical zero-use evidence as a lead, not contract proof. Check AGENTS/ADR owners, imports, indirect construction, framework hooks, string patch targets, and external seams.

## Stop conditions

- Dirty preflight: stop immediately without stashing, resetting, or modifying files.
- An existing open Ponytail Cycle PR creates a different base/head choice: report its topology and stacking recommendation before creating a new branch.
- A candidate changes production behavior, enters a forbidden path, or is a src bug: reject it and continue with safe findings.
- High-confidence accepted findings total less than about 100 removed or inlined physical lines across tests and related src, excluding moves and format-only churn: leave no cleanup commit, push, or PR; report `Lean already. Ship.`

Decide the threshold after the full Phase 3 counterexample pass so tests and related src count together. Commit 1 may therefore be temporary. For a lean verdict, first require a clean worktree and prove every commit after the captured Phase 0 base belongs to this cycle; then return only the task branch to that exact base and end without publishing. Apply the same rollback rule if later adversarial rejection drops the realized total below the threshold.

## Phase 0 - Preflight

1. Capture the starting branch and HEAD. Require empty output from both `git status --short` and `git diff --cached --name-only`; otherwise stop and report the exact paths.
2. Query open PRs whose head starts with `claude/ponytail-cycle-`. If one may be the same lineage, compare head/base/diff and stop with a reuse-or-stack recommendation when choosing would change the publication topology.
3. Run `git fetch origin main`, capture its resolved commit as the immutable cycle base, and create `claude/ponytail-cycle-<YYYYMMDD>` directly from that commit; add a numeric suffix only for a same-day name collision.
4. Run `uv sync --extra torch-macos`. If it changes tracked files, stop and report rather than absorbing environment drift.
5. Run the full baseline with `uv run pytest -q -ra`. Preserve the complete result plus failed, skipped, and xfailed node IDs and reasons. Inspect every skip condition and its resolved data path; classify each skip as valid or invalid rather than accepting its reason string as proof.
6. Record the baseline as the regression comparator. Existing failures may continue only unchanged; the cycle may introduce no new failure, skip, xfail, or worsened failure. An invalid baseline skip becomes a test finding and may disappear only after its test actually runs GREEN.

Phase 0 is complete only when the new branch is clean, the environment is synchronized, and every baseline failure, skip, and xfail has a node-level explanation and classification.

## Phase 1 - Read-only `tests/` audit

Build the tracked test universe from Git, partition all tracked Python test files into balanced 10-15k physical-LOC lanes, and reconcile the returned file lists against the universe so no file is omitted or duplicated. Read adjacent data/snapshots when a test's meaning depends on them.

Each read-only lane must fully read its files and hunt for:

1. duplicate or subset coverage, naming one surviving owner test;
2. implementation pins: smoke-output strings, signature `TypeError`, dataclass mechanics, and other non-contract shape locks;
3. removal guards that only watch a deleted identifier/path stay deleted;
4. single-use helpers and avoidable file hops;
5. hand-built stdlib or pytest substitutes;
6. excessive parametrization that obscures one contract;
7. tests placed under the wrong owner/category.

Each lane returns:

- every finding in ledger form, ranked by context reduction;
- a helper/fixture inventory with definition, scope, and exact use count;
- every contract it found pinned twice or more;
- an explicit list of assigned files read.

The leader then verifies helper counts across the whole test universe and cross-compares lanes for double/triple-pinned contracts. A duplicate finding is invalid until it names the surviving `file::test_name`; a tautology finding must explain why the assertion cannot fail on the exercised path.

## Phase 2 - Apply tests and disprove deletions

Partition accepted edits into file-disjoint units. Assign each path to exactly one editor; serialize changes to shared fixtures, factories, and `conftest.py`. Each editor records a reversible patch for all owned paths, including staged move destinations, before verification. Parallel editors stop at a global write barrier. In the shared worktree, run unit tests and mutation checks serially after that barrier; parallel test execution requires isolated worktrees.

For each unit:

1. Edit only owned files.
2. For every deletion, record the surviving `file::test_name` or tautology proof. Fold a unique assertion into the survivor at equal strength.
3. Preserve `real_data` markers and every valid baseline skip. Add no skip/xfail; map any repaired invalid baseline skip to a GREEN executed test in the ledger.
4. Run `uv run pytest <owned-files> -q` and record the result.
5. If a file is moved or split, stage the destination immediately so the move cannot degrade into an unnoticed deletion.

After the editor is green, a different verifier tries to disprove that the survivor pins the same contract. The verifier is read-only except for the isolated mutation protocol below. The verifier must inspect the actual rendered widget before deleting a bare-digit/count assertion; never use macOS `git grep '\b'` as absence evidence.

When the verifier says a deleted assertion may carry a unique contract, mutation proof is mandatory; without it, reject the deletion. Run the proof while all conflicting editors are idle or in an isolated worktree:

1. Mutate the covered input/behavior so the survivor should fail.
2. Run the exact survivor and record RED.
3. Restore the mutation exactly.
4. Run the survivor again and record GREEN.
5. Confirm no mutation residue remains before releasing the unit.

Retain only verifier-approved units in the combined working diff. Apply the recorded inverse patch to the exact owned paths of every rejected unit and verify that no residue remains. Then run:

Format only changed Python files, then run:

```bash
uv run ruff format --check .
uv run ruff check .
uv run pytest -q -ra
```

Compare failure, skip, and xfail outcomes node-for-node with the baseline, accounting for every intentionally deleted/moved test and repaired invalid skip through the finding ledger. Commit only the verified tests change as:

```text
refactor(tests): <context removed>
```

## Phase 3 - Read-only related `src` audit

Derive the scope from commit 1: every removed, moved, or changed test import, call, constructor, fixture target, and `monkeypatch.setattr` string. Follow those production owners and their callers only far enough to prove ownership and indirect use; do not expand into a repo-wide src cleanup.

Hunt for:

1. public APIs, parameters, and setters now consumed only by tests;
2. injection seams whose non-default implementations exist only in tests;
3. one-to-one delegation hops and single-consumer cross-package functions;
4. dead defaults and unreachable defenses such as obsolete `getattr` fallbacks;
5. surviving test helpers whose use count fell after commit 1;
6. ghost identifiers formerly protected only by removal guards.

Attach a counterexample verifier to every finding. The verifier must check production callers, re-exports, plugin/framework discovery, indirect constructors, string references, docs/ADR/AGENTS ownership, and external seams. A constant named by AGENTS as an SSOT stays named even with one lexical use. Static caller count alone never proves a single implementation.

Rank only findings that survive the counterexample pass, again by context reduction rather than patch size.

Now total the accepted tests and src reductions. If the combined result is below the threshold, verify the worktree is clean and commit 1 is the only task-owned delta after the immutable cycle base, return the task branch to that base, and report `Lean already. Ship.` without push or PR.

## Phase 4 - Apply src and co-migrate

Create file-disjoint edit units from accepted findings. Reuse Phase 2's exact ownership, reversible-patch, global write-barrier, serial shared-worktree test, and rejected-unit rollback protocol. Keep any model/dataclass change spanning units as one final serial unit.

For each unit:

1. Preserve production behavior and outputs.
2. Co-migrate every affected test to the canonical production path in the same change.
3. When removing a delegation hop, migrate `monkeypatch.setattr(module, "name", ...)` to the name imported by the actual consuming module.
4. Run targeted tests for every changed src/test seam.
5. Give the unit to a different verifier for a counterexample pass before integration.

After all units, format changed Python files, rerun Ruff and `uv run pytest -q -ra`, compare against the baseline plus ledgered test changes, and require no new/worse failure, skip, or xfail. When a src diff remains, commit it as:

```text
refactor: <context removed>
```

Do not create an empty second commit; report that no src candidate survived instead.

## Phase 5 - Rebase, verify, and publish

1. Fetch `origin/main` again. If it moved, create an isolated clean worktree at the refreshed base, run `uv sync --extra torch-macos` there, require that sync leaves tracked files clean, then run `uv run pytest -q -ra`. Record that result as the post-rebase comparator and remove the temporary worktree; then rebase the created commit or commits onto it. Resolve conflicts by preserving main's new coverage, keeping our proven duplicate deletions, and accepting main's deletions. If a conflict or upstream change touches an audited surface, rerun its targeted test and adversarial verification.
2. Run the final Ruff checks and `uv run pytest -q -ra`. Compare failures, skips, and xfails against the Phase 0 baseline when main did not move, otherwise against the isolated refreshed-base result, accounting for ledgered test removals and invalid-skip repairs.
3. Push the cycle branch. Use `$pr-workflow` to create or update the PR; the cycle request itself supplies publish authority, subject to platform approval gates.
4. Recheck for an open earlier cycle PR. Update the same head when appropriate; otherwise report the exact stacking decision instead of silently creating a duplicate lineage.
5. Verify the published branch/PR and report CI state separately from local gate success.

The Korean PR body must include:

- a commit-by-commit summary table;
- baseline, targeted, mutation, adversarial, Ruff, and final full-gate evidence;
- the production and diagnostic behavior-change surface (`없음` when none);
- focused review points;
- rejected findings under `재제안 금지`, with the counterevidence that rejected each one.

## Final report

Report branch, created commit hashes, files/context hops removed, deletion LOC, baseline versus final failures/skips/xfails, targeted and mutation evidence, rebase/push/PR state, behavior-change surface, remaining risk, and the `재제안 금지` list. For a below-threshold run, report only the evidence-backed lean verdict and rejected candidates; leave no cleanup commit or PR.
