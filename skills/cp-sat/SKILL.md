---
name: cp-sat
description: Use when building, tuning, or debugging Google OR-Tools CP-SAT models — combinatorial optimization, scheduling (no-overlap/cumulative/reservoir), routing (TSP/VRP via circuit), packing (2D/3D), assignment, or constraint satisfaction; triggers on imports from `ortools.sat.python`, use of `cp_model.CpModel`/`CpSolver`, or deciding between CP-SAT and MIP/SAT/SMT solvers
---

# Writing CP-SAT Solvers

## Overview

CP-SAT (Google OR-Tools) is a **portfolio solver** built on **Lazy Clause Generation (LCG)** — a CP+SAT hybrid integrating CDCL clause learning, LP relaxation, and specialized propagators. It excels on problems with heavy logical structure that defeat Simplex-based MIP solvers, and often competes with Gurobi on mixed problems.

**Core principle: model in CP-SAT's native idioms.** Translating MIP Big-M formulations verbatim is the #1 anti-pattern — use `only_enforce_if`, interval variables, circuits, and table constraints instead.

## When to Use

Use CP-SAT when:
- Combinatorial optimization with complex logical / disjunctive constraints
- Scheduling — `add_no_overlap`, `add_cumulative`, reservoir
- Routing — TSP / VRP via `add_circuit` / `add_multiple_circuit`
- Assignment, matching, 2D/3D packing
- Integer-only decision variables (CP-SAT has **no continuous variables**)
- Problems that MIP solvers struggle on due to logical structure

Use a different solver when:
- Continuous variables dominate → **Gurobi LP / HiGHS**
- Large-scale pure MIP with tight LP relaxation → **Gurobi, SCIP, HiGHS**
- Million-variable pure Boolean SAT → **PySAT, Kissat**
- Rich theories (bit-vectors, arrays, quantifiers) → **Z3 (SMT)**
- Smooth nonlinear / convex programming → **IPOPT, SciPy, cvxpy**

## Critical Mental Model

1. **Integers only.** Scale floats by LCM of denominators at the boundary; keep core logic integer.
2. **Logic is cheap.** Prefer `only_enforce_if`, `add_allowed_assignments`, reified constraints over linearization.
3. **Portfolio solver.** Many strategies run in parallel; improve the *model* rather than picking one strategy.
4. **Stateless.** No incremental solving with clause reuse. For iterative problems, rebuild or use assumptions.
5. **Presolve is powerful.** Always enable `log_search_progress=True` in development and *read* the log.
6. **Bounds matter.** Prove optimality via lower/upper bound; `relative_gap_limit` lets you stop early when the gap is acceptable.

## Workflow

1. **Model** using canonical forms → see `modeling-patterns.md`.
2. **Run with logs**: `solver.parameters.log_search_progress = True` every development iteration.
3. **Read the log** — compare initial vs presolved model, check which subsolver wins, note LNS stats → see `tuning-and-log.md`.
4. **Fix the model first.** No parameter tuning saves a bad model.
5. **Then tune parameters** — time limit, gap limits, `num_workers`. Avoid speculative strategy tweaks.
6. **Scale up with LNS** if the instance is huge → see `lns-template.md`.
7. **Wrap for production** — solver class, data validation, benchmarks → see `architecture.md`.

## Quick Reference

| Need | API keys | File |
|---|---|---|
| Variables / constraints / objectives | `new_int_var`, `new_bool_var`, `new_int_var_from_domain`, `add`, `only_enforce_if`, `add_all_different`, `add_exactly_one`, `add_element`, `add_circuit`, `new_interval_var`, `add_no_overlap`, `add_cumulative` | api-reference.md |
| Canonical model patterns | Big-M replacement, lex objectives, piecewise linear, reservoir, scheduling, routing | modeling-patterns.md |
| Solver params & log reading | `max_time_in_seconds`, `num_workers`, `relative_gap_limit`, `log_search_progress`, presolve summary, subsolver ranking | tuning-and-log.md |
| Hints & infeasibility debugging | `add_hint`, `fix_variables_to_their_hinted_value`, `only_enforce_if(indicator)` + `sufficient_assumptions_for_infeasibility` | tuning-and-log.md |
| Callbacks | `CpSolverSolutionCallback`, `best_bound_callback`, `log_callback` | tuning-and-log.md |
| LNS heuristic | destroy + repair via hints, ALNS | lns-template.md |
| Production architecture | data/model/solver/solution layers, FastAPI + RQ + Redis, TDD, benchmarking | architecture.md |

## Critical DO / DON'T

### DO
- Enable `log_search_progress=True` in development.
- Use `only_enforce_if` for conditional constraints (never Big-M).
- **Complete** hints (fill every variable) before solving.
- Verify hints with `fix_variables_to_their_hinted_value=True`.
- Name variables meaningfully — they appear in the log.
- Use `add_exactly_one` / `add_at_most_one` instead of `sum(...) == 1`.
- Use `add_allowed_assignments` / `add_forbidden_assignments` for irregular feasible sets.
- Use interval variables + `add_no_overlap` / `add_cumulative` for scheduling.
- Lexicographic objectives: solve, fix with `add` on objective, re-solve secondary.
- Set `relative_gap_limit` (e.g. 0.01–0.05) for hard problems where exact optimality is not required.

### DON'T
- Port MIP Big-M verbatim — re-model with reification.
- Multiply variables directly (`x * y` inside `add(...)`) — use `add_multiplication_equality`.
- Mix `add_all_different` with explicit `!=` constraints — disables the global propagator.
- Set `search_branching = FIXED_SEARCH` speculatively; manual strategies rarely win.
- Disable `cp_model_presolve` without measuring first.
- Run heavy logic in `on_solution_callback` — Python context switches dominate runtime.
- Leave hints partial — extending them wastes solve time.
- Assume more `num_workers` is always faster — test physical-core count too.
- Tune solver on <10 benchmark instances (no-free-lunch; you'll overfit).
- Store only random seeds for benchmark instances — persist the actual instance files.

## Rationalization Table

| Thought | Reality |
|---|---|
| "Big-M works in MIP, it should work here." | CP-SAT can't exploit Big-M the way Simplex does. LCG uses reification directly. |
| "I'll disable presolve to save time." | Presolve typically pays back many times over. Measure via log first. |
| "FIXED_SEARCH with my strategy will beat AUTOMATIC." | Primer author tested this; it rarely wins. Fix the *model* instead. |
| "Hints barely matter." | Correct *complete* hints can cut wall time by orders of magnitude. |
| "More workers is always faster." | Memory bandwidth + worker interference. Physical-core count often wins. |
| "I can approximate continuous vars with fine-grained integers." | Technically yes, but LP solvers will destroy you. Reformulate or switch solver. |
| "Callback is just a print." | Every Python context switch costs. Minimize callback frequency and work. |
| "The solver is slow, let me tweak parameters." | Usually the *model* is slow. Read the log first. |

## Red Flags — STOP and Rethink

- Writing `big_M * (1 - bool_var)` anywhere → use `.only_enforce_if(bool_var)`
- `x * y` inside `model.add(...)` → use `add_multiplication_equality(target, [x, y])`
- `add_all_different(xs)` alongside `model.add(xs[i] != xs[j])` → drop the `!=`, rely on the global
- `search_branching = FIXED_SEARCH` with no evidence → revert to AUTOMATIC
- No `log_search_progress=True` during development → turn it on
- Partial hints → apply `complete_hint` pattern (see tuning-and-log.md)
- Fiddling with `subsolver_params` before reading the log → read the log first

## Environment notes

- **Python**: 3.10+ recommended. The `int | None` union syntax used in the skill's architecture examples requires 3.10+ unless you add `from __future__ import annotations` and `pip install eval_type_backport` (Pydantic runtime check).
- **ortools**: pin a specific version in your `requirements.txt`. The CP-SAT Python API renames things between minor versions. A few 9.15-era quirks (e.g. `solver.status_name()` bug, `model.proto.SerializeToString()` removal) are documented in `tuning-and-log.md` §9.

## Further Reading

- `api-reference.md` — full API cheatsheet (variables, constraints, parameters, callbacks)
- `modeling-patterns.md` — canonical modeling patterns with idiomatic code
- `tuning-and-log.md` — solver parameters, log reading, hints, callbacks, assumptions, version-sensitive APIs
- `lns-template.md` — destroy/repair LNS template, adaptive selection
- `architecture.md` — production solver class, FastAPI+RQ service, TDD, benchmarking
