# Advanced CP-SAT Playbook

Distilled from the provided advanced CP-SAT companion draft.
Attribution preserved from *The CP-SAT Primer* by Dominik Krupke and contributors under CC BY 4.0.

## Use This Reference When

- baseline correctness is already established,
- logs are available or need to be instrumented,
- the task is about runtime, bound quality, repeated solves, or scaling,
- you need a stronger advanced primitive or search workflow.

If correctness is still unclear, return to `cp-sat-primer-engineer` first.

## Minimum Instrumentation

Track both build time and solve time.
For every serious experiment, record:

- OR-Tools version
- Python version
- hardware or CPU
- worker count
- time limit
- parameter block
- benchmark instance id
- solver status
- objective value
- best bound
- wall time
- raw log path

Default diagnosis setup:

```python
from ortools.sat.python import cp_model
import time

build_t0 = time.perf_counter()
model = cp_model.CpModel()
# ... build variables and constraints ...
build_t1 = time.perf_counter()

solver = cp_model.CpSolver()
solver.parameters.log_search_progress = True
solver.parameters.max_time_in_seconds = 60
solver.log_callback = print
solver.parameters.log_to_stdout = False

solve_t0 = time.perf_counter()
status = solver.solve(model)
solve_t1 = time.perf_counter()

print({
    "build_seconds": build_t1 - build_t0,
    "solve_seconds": solve_t1 - solve_t0,
    "status": solver.status_name(status),
    "objective": getattr(solver, "objective_value", None),
    "best_bound": getattr(solver, "best_objective_bound", None),
})
```

## Triage Order

Ask these questions in order:

1. Is the bottleneck Python-side model construction?
2. Does presolve dominate runtime?
3. Is first-feasible latency the real issue?
4. Is proving quality or improving the bound the real issue?
5. Are LP-related subsolvers helping?
6. Is generic CP-SAT LNS already doing the useful work?
7. Is the real workflow a repeated short solve instead of a single proof-heavy solve?

## Bottleneck Matrix

### Build-Time Bottleneck

Symptoms:

- long delay before solver start,
- huge nested Python loops,
- dense all-pairs preprocessing,
- obvious superlinear generator work.

Actions:

- profile the generator,
- precompute only relevant pairs or arcs,
- create auxiliaries lazily,
- remove duplicate constraints,
- replace dense structures with sparse incidence sets.

### Presolve Bottleneck

Symptoms:

- presolve consumes most of runtime,
- logs show heavy cleanup or probing,
- the model contains many redundant variables or duplicate constraints.

Actions:

- simplify the generator,
- remove redundant auxiliaries yourself,
- tighten domains earlier,
- only then test lower presolve effort.

### First-Feasible Bottleneck

Symptoms:

- long time with no incumbent,
- proof-oriented work dominates before any solution appears.

Actions:

- provide a feasible hint,
- simplify the objective into phases,
- reduce worker count if contention hurts latency,
- add symmetry breaking,
- use repair search or LNS.

### Bound-Proof Bottleneck

Symptoms:

- incumbents arrive but the bound barely moves,
- proof effort dominates after a decent solution exists.

Actions:

- strengthen the formulation,
- add redundant but tightening constraints,
- tighten variable bounds,
- test whether LP-heavy subsolvers help,
- consider decomposition or phase-based objectives.

## Stronger Primitive Selection

Prefer native structure over weak hand-written formulations:

- intervals plus `add_no_overlap` or `add_cumulative` for scheduling,
- circuit-style constraints for sequence structure,
- automaton for regular-language sequence rules,
- reservoir when a cumulative flow-like stock process fits,
- table constraints for small exact relation maps.

Do not keep a weak Boolean-linear encoding when CP-SAT already offers the stronger primitive.

## Repeated Solve Workflows

When the model is solved many times:

- reuse incumbents as hints,
- preserve benchmark reproducibility,
- tighten domains from prior solutions when logically justified,
- break multi-objective optimization into phases,
- consider assumptions for toggled scenarios,
- consider repair neighborhoods instead of repeated cold starts.

## Hints And Assumptions

Hints:

- help when they are close to a feasible high-quality incumbent,
- can hurt if stale or structurally inconsistent,
- should be benchmarked, not assumed beneficial.

Assumptions:

- help isolate optional scenario toggles,
- help with explainable infeasibility workflows,
- are useful for unsat-core style debugging when optional conditions conflict.

## Worker And Subsolver Tuning

Do not chase worker count heuristics blindly.
More workers can lose to fewer workers because of contention or portfolio mismatch.

Before tuning workers or subsolvers:

- confirm the bottleneck from logs,
- keep the benchmark set fixed,
- compare objective, bound, and wall time together,
- separate improvements to first-feasible time from improvements to proof quality.

## LNS Guidance

Use LNS when:

- exact full search stalls,
- you already have a decent incumbent,
- the domain has meaningful neighborhoods.

Design neighborhoods around business structure, for example:

- selected tasks,
- time windows,
- route fragments,
- machine groups,
- assignment blocks.

Freeze most of the incumbent and reopen the chosen neighborhood.
Benchmark neighborhood quality and repair time instead of assuming generic LNS is sufficient.

## Benchmark Acceptance Rules

- export the exact model when environment differences matter,
- pin versions,
- use representative easy, medium, and hard instances,
- reject changes that only win on cherry-picked tiny cases,
- always report risk and rollback notes with tuning changes.
