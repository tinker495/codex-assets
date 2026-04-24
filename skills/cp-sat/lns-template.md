# Large Neighborhood Search (LNS) with CP-SAT

When the full problem is too large to solve to optimality within the time budget, LNS repeatedly (a) fixes most of the current solution, (b) re-solves a small CP-SAT subproblem, and (c) replaces the incumbent if improved. CP-SAT itself runs internal LNS workers, but writing your own outer LNS lets you inject domain knowledge about *which* subset of variables to destroy.

## Core loop

```python
def lns_loop(
    build_model,              # () -> (model, vars)  — constructs a fresh model
    initial_solution,         # dict: var_name -> value
    destroy,                  # (incumbent, iteration) -> set of var_names to destroy
    iterations=100,
    sub_time_limit=5.0,
    global_time_limit=300.0,
):
    import time
    from ortools.sat.python import cp_model
    incumbent = dict(initial_solution)
    best_obj = None
    start = time.time()
    for it in range(iterations):
        if time.time() - start > global_time_limit:
            break
        model, vars_by_name = build_model()
        frozen = [n for n in vars_by_name if n not in destroy(incumbent, it)]
        for name in frozen:
            model.add_hint(vars_by_name[name], incumbent[name])
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = sub_time_limit
        solver.parameters.fix_variables_to_their_hinted_value = True
        # Only fix the frozen variables; unfreeze the destroyed ones
        # Implementation detail: build model with explicit hints for frozen,
        # NO hint for destroyed so they're free to move.
        ...
        status = solver.solve(model)
        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            candidate = {n: solver.value(v) for n, v in vars_by_name.items()}
            obj = solver.objective_value
            if best_obj is None or obj < best_obj:
                incumbent, best_obj = candidate, obj
    return incumbent, best_obj
```

Important subtlety: `fix_variables_to_their_hinted_value = True` freezes *all hinted* variables. If you want only some variables frozen, do not hint the destroyed ones — then set `fix_variables_to_their_hinted_value = True` to freeze the hinted-frozen set while the destroyed variables are solved freely.

Alternative: leave `fix_variables_to_their_hinted_value = False` and add explicit equality constraints for frozen variables:

```python
for name in frozen:
    model.add(vars_by_name[name] == incumbent[name])
```

This is clearer and does not interfere with hints on destroyed variables.

## Concrete: knapsack LNS

```python
from ortools.sat.python import cp_model
import random

def solve_subproblem(weights, values, capacity, frozen_items, free_items,
                     frozen_assignment, time_limit=1.0):
    model = cp_model.CpModel()
    xs = {}
    for i in frozen_items:
        xs[i] = model.new_constant(frozen_assignment[i])
    for i in free_items:
        xs[i] = model.new_bool_var(f"x_{i}")
    model.add(sum(xs[i] * weights[i] for i in xs) <= capacity)
    model.maximize(sum(xs[i] * values[i] for i in xs))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.solve(model)
    return {i: solver.value(xs[i]) for i in xs}, solver.objective_value

def knapsack_lns(weights, values, capacity, initial, iterations=40,
                 destroy_size=5, consider_extra=10, time_limit_per_iter=1.0):
    incumbent = dict(initial)
    best = sum(values[i] for i in incumbent if incumbent[i])
    n = len(weights)
    for it in range(iterations):
        packed = [i for i in range(n) if incumbent[i]]
        unpacked = [i for i in range(n) if not incumbent[i]]
        if not packed:
            break
        destroyed = set(random.sample(packed, min(destroy_size, len(packed))))
        candidates = set(random.sample(
            unpacked, min(consider_extra, len(unpacked))))
        free = destroyed | candidates
        frozen = set(range(n)) - free
        new_assign, obj = solve_subproblem(
            weights, values, capacity,
            frozen_items=frozen, free_items=free,
            frozen_assignment=incumbent,
            time_limit=time_limit_per_iter,
        )
        if obj > best:
            best = obj
            incumbent.update(new_assign)
    return incumbent, best
```

## Destroy strategies (pick one per iteration)

| Name | Rule |
|---|---|
| **Random** | Pick `k` random variables uniformly. Always a sensible default. |
| **Worst-contribution** | Pick variables that contribute most to the objective slack (for knapsack: lowest value/weight ratio currently packed). |
| **Structural** | For TSP: pick a geographic cluster (variables in a rectangle). For VRP: destroy one route entirely. |
| **Constraint-guided** | Pick variables appearing in the most-violated soft constraint; useful after penalty-based repair. |
| **Time-window** | Scheduling: destroy all tasks in a specific time window. |

## Adaptive (ALNS): multi-armed bandit over strategies

```python
class ALNS:
    def __init__(self, strategies):
        self.strategies = strategies
        self.scores = [1.0] * len(strategies)   # smoothed improvement
        self.uses   = [1]   * len(strategies)

    def pick(self):
        import math, random
        total_uses = sum(self.uses)
        # UCB1
        ucb = [s / u + math.sqrt(2 * math.log(total_uses) / u)
               for s, u in zip(self.scores, self.uses)]
        i = max(range(len(ucb)), key=lambda k: ucb[k])
        return i, self.strategies[i]

    def update(self, i, improvement):
        # improvement = max(0, old_obj - new_obj) for minimization
        self.scores[i] = 0.9 * self.scores[i] + 0.1 * improvement
        self.uses[i] += 1
```

Plug into the core loop: pick a strategy, run one LNS iteration, update with the measured improvement.

## Adaptive neighborhood size

If a subproblem times out, shrink. If it solves within a fraction of the limit, grow.

```python
destroy_size = 5
for it in range(iterations):
    ...
    solve_time = solver.wall_time
    if solver.status_name() not in ("OPTIMAL",):
        destroy_size = max(2, int(destroy_size / 1.5))
    elif solve_time < 0.3 * time_limit_per_iter:
        destroy_size = min(n, int(destroy_size * 1.5))
```

## Warm-starting CP-SAT with LNS output

After LNS stops improving, feed the final incumbent back to CP-SAT as hints for a full solve attempt. This often closes the remaining gap:

```python
model = build_full_model()
for name, val in incumbent.items():
    model.add_hint(vars_by_name[name], val)
solver.parameters.max_time_in_seconds = 60
status = solver.solve(model)
```

Do this after verifying the hint is feasible.

## Rules of thumb

- Start with a **fast feasibility** solution (greedy, constructive), not a slow optimality run.
- Destroy size: 5–20% of decision variables per iteration is a good starting range.
- Sub-time-limit: 1–10s. Too short = solver only finds trivial repairs. Too long = few iterations.
- Always keep a **global time limit** — LNS never terminates on its own.
- Track objective per iteration; if flat for N iterations, switch strategy or accept the answer.
- For pure LNS workers inside CP-SAT, set `solver.parameters.use_lns_only = True` and provide a time limit.

## When *not* to use outer LNS

- Problem fits inside CP-SAT's time budget with optimality proof → just solve directly.
- CP-SAT's internal LNS is closing the gap well (check `LNS stats` in log) — adding an outer LNS often duplicates effort.
- You don't have a reasonable initial solution — build one first (constructive heuristic, greedy).
