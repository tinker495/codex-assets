# CP-SAT API Reference

Canonical Python (snake_case) API from `ortools.sat.python.cp_model`. Always check your installed version — names changed a few times (CamelCase legacy still works; snake_case preferred).

```python
from ortools.sat.python import cp_model
model = cp_model.CpModel()
solver = cp_model.CpSolver()
```

## Variables

| API | Purpose |
|---|---|
| `model.new_int_var(lb, ub, name)` | Integer in `[lb, ub]`. |
| `model.new_int_var_from_domain(domain, name)` | Integer with sparse domain. Use `cp_model.Domain.from_values([v1, v2, ...])` or `Domain.from_intervals([[a, b], [c, d]])`. |
| `model.new_bool_var(name)` | Boolean (0/1). Negate via `~b` or `b.Not()`. |
| `model.new_constant(value)` | Integer constant as expression. |
| `model.new_interval_var(start, size, end, name)` | Interval; implicitly adds `start + size == end`. `start`, `size`, `end` are expressions. |
| `model.new_optional_interval_var(start, size, end, is_present, name)` | Interval active only when `is_present` literal is true. |
| `model.new_fixed_size_interval_var(start, size, name)` | Fixed-duration interval (size is int constant). |
| `model.new_optional_fixed_size_interval_var(start, size, is_present, name)` | Optional fixed-duration. |

**Domain tips**: Prefer `new_int_var_from_domain` for sparse domains (e.g. `{10, 20, 30}`) — propagation is far tighter than a wide `new_int_var` plus `add_allowed_assignments`.

## Linear constraints and arithmetic

| API | Purpose |
|---|---|
| `model.add(expr)` | Add linear expression with `<=`, `>=`, `==`. Returns a `Constraint` supporting `.only_enforce_if(...)`. |
| `model.add_linear_constraint(expr, lb, ub)` | `lb <= expr <= ub` in one call. |
| `model.add_linear_expression_in_domain(expr, domain)` | Restrict `expr` to a sparse integer domain. |

Returns `BoundedLinearExpression`; reify conditionally:

```python
model.add(x + y <= 10).only_enforce_if(b)          # if b then x+y <= 10
model.add(x + y > 10).only_enforce_if(b.Not())     # for the converse
```

`only_enforce_if` accepts a single literal or a list (conjunction): `.only_enforce_if([b1, b2])`.

## Boolean logic

| API | Purpose |
|---|---|
| `model.add_bool_and([b1, b2, ...])` | All true. |
| `model.add_bool_or([b1, b2, ...])` | At least one true. |
| `model.add_bool_xor([b1, b2, ...])` | Parity constraint (odd number true). |
| `model.add_implication(b1, b2)` | `b1 → b2`. |
| `model.add_at_most_one([b1, b2, ...])` | ≤ 1 true. Faster than `sum(bs) <= 1`. |
| `model.add_at_least_one([b1, b2, ...])` | ≥ 1 true. Equivalent to `add_bool_or`. |
| `model.add_exactly_one([b1, b2, ...])` | Exactly 1 true. Faster than `sum(bs) == 1`. |

## Cardinality & assignment

| API | Purpose |
|---|---|
| `model.add_all_different([x1, x2, ...])` | Pairwise distinct. Uses a global propagator. **Don't combine with explicit `!=`.** |
| `model.add_inverse(direct, inverse)` | Bijection: `direct[i] == j ⇔ inverse[j] == i`. |
| `model.add_allowed_assignments([vars], [tuples])` | Only listed tuples permitted. Extensional / table constraint. |
| `model.add_forbidden_assignments([vars], [tuples])` | Listed tuples forbidden. |
| `model.add_automaton(vars, start_state, final_states, transitions)` | Sequence must match a DFA. |

**Prefer tables** for irregular feasible sets (hard to linearize). CP-SAT's table propagator is highly tuned.

## Arithmetic relations

All require an auxiliary variable — CP-SAT doesn't accept nonlinear expressions inside `add(...)`.

| API | Meaning |
|---|---|
| `model.add_abs_equality(target, expr)` | `target = |expr|` |
| `model.add_max_equality(target, [e1, e2, ...])` | `target = max(...)` |
| `model.add_min_equality(target, [e1, e2, ...])` | `target = min(...)` |
| `model.add_multiplication_equality(target, [e1, e2, ...])` | Product of expressions. |
| `model.add_division_equality(target, num, denom)` | Integer division (floor). |
| `model.add_modulo_equality(target, expr, mod)` | `target = expr mod mod`. |
| `model.add_element(index, [v1, v2, ...], target)` | `target = values[index]`. Used for lookup/piecewise. |

## Scheduling

| API | Purpose |
|---|---|
| `model.add_no_overlap([intervals])` | No two intervals overlap. |
| `model.add_no_overlap_2d([x_intervals], [y_intervals])` | Rectangle packing. |
| `model.add_cumulative([intervals], [demands], capacity)` | Σ demand over active intervals ≤ capacity. |
| `model.add_reservoir_constraint(times, level_changes, min_level, max_level)` | Running sum of `level_changes` at `times` stays in `[min_level, max_level]`. |
| `model.add_reservoir_constraint_with_active(times, level_changes, actives, min_level, max_level)` | Conditional reservoir (skip event when `actives[i]` is 0). |

Use optional intervals to model "this task may be skipped / assigned to another machine" — the solver reasons about the presence literal natively.

## Routing

```python
model.add_circuit([(tail, head, literal), ...])
# Boolean literals form a Hamiltonian cycle over nodes appearing in arcs.
# Self-loops (node -> node, optional literal) mark a node as skipped.
model.add_multiple_circuit([(tail, head, literal), ...])
# Enforces a set of disjoint circuits, all visiting node 0 (depot).
```

## Objectives

```python
model.minimize(expr)
model.maximize(expr)
```

No direct multi-objective API. Two canonical patterns:
1. **Weighted sum** — `minimize(w1*f1 + w2*f2)`. Weights must reflect a strict priority if lex is desired.
2. **Lexicographic** — solve with `minimize(f1)`, record `f1*`, add `model.add(f1 == f1_star)`, re-solve with `minimize(f2)`.

After solving: `solver.objective_value`, `solver.best_objective_bound`.

## Hints and assumptions

```python
model.add_hint(var, value)
model.clear_hints()

# Assumptions — Boolean literals only, single solve only
model.add_assumption(b1)
model.add_assumptions([b1, b2.Not()])
model.clear_assumptions()
```

After `status = solver.solve(model)` with `status == INFEASIBLE`:
```python
for i in solver.sufficient_assumptions_for_infeasibility():
    print(model.proto.variables[i].name)
```

## Decision strategy (advanced — use sparingly)

```python
model.add_decision_strategy([x], cp_model.CHOOSE_FIRST, cp_model.SELECT_MIN_VALUE)
solver.parameters.search_branching = cp_model.FIXED_SEARCH
```

Variable strategies: `CHOOSE_FIRST`, `CHOOSE_LOWEST_MIN`, `CHOOSE_HIGHEST_MAX`, `CHOOSE_MIN_DOMAIN_SIZE`, `CHOOSE_MAX_DOMAIN_SIZE`.

Domain strategies: `SELECT_MIN_VALUE`, `SELECT_MAX_VALUE`, `SELECT_LOWER_HALF`, `SELECT_UPPER_HALF`, `SELECT_MEDIAN_VALUE`.

The primer's explicit advice: manual strategies rarely beat CP-SAT's learned branching. Try it only when the log shows the default making obviously bad decisions.

## Core solver parameters

All live under `solver.parameters` (a `SatParameters` protobuf).

| Parameter | Default | Effect |
|---|---|---|
| `max_time_in_seconds` | unlimited | Wall-clock cap. |
| `max_deterministic_time` | unlimited | Deterministic time cap (reproducible across machines/runs). |
| `relative_gap_limit` | 0.0 | Stop when `|obj - bound| / |bound| ≤ limit`. |
| `absolute_gap_limit` | 0.0 | Stop when `|obj - bound| ≤ limit`. |
| `num_workers` (alias `num_search_workers`) | all cores inc. hyperthreading | Parallel subsolver count. Try physical-core count. |
| `log_search_progress` | False | Enable detailed log. **On in dev.** |
| `log_to_stdout` | True | Pair with custom `solver.log_callback`. |
| `random_seed` | 1 | Changes tiebreaking — run multiple seeds for benchmarking. |
| `enumerate_all_solutions` | False | Continue searching after optimality for all feasible. |
| `linearization_level` | 1 | 0 = off, 1 = default, 2 = aggressive. Higher = tighter LP bounds, slower per node. |
| `cp_model_presolve` | True | Leave on; huge wins. |
| `search_branching` | AUTOMATIC | Do not set to FIXED_SEARCH without evidence. |
| `fix_variables_to_their_hinted_value` | False | Feasibility-check hints; also works as "repair". |
| `repair_hint` | False | Try to make partial hints feasible. |
| `keep_all_feasible_solutions_in_presolve` | False | Prevents presolve from pruning hinted symmetric solutions. |
| `fill_tightened_domains_in_response` | False | Feasibility version: get tightened domains back on the response. |
| `use_lns_only` | False | Run only LNS incomplete workers (needs a time limit). |
| `stop_after_first_solution` | False | Return as soon as any feasible solution is found. |
| `stop_after_presolve` | False | Exit after presolve — useful for offline inspection. |
| `subsolver_params` / `extra_subsolvers` / `ignore_subsolvers` | — | Fine-tune portfolio. Rarely needed. |

## Solver methods

```python
status = solver.solve(model)  # or solver.solve(model, callback)
solver.value(x)               # int value in the best solution
solver.boolean_value(b)       # bool value
solver.objective_value        # best solution objective
solver.best_objective_bound   # proven bound
solver.wall_time              # seconds
solver.user_time              # CPU seconds
solver.response_stats()       # string summary
solver.status_name()          # e.g. 'OPTIMAL'
solver.sufficient_assumptions_for_infeasibility()
solver.stop_search()          # from a callback thread
```

Status codes: `OPTIMAL` (4), `FEASIBLE` (2), `INFEASIBLE` (3), `MODEL_INVALID` (1), `UNKNOWN` (0). There is no `UNBOUNDED` — CP-SAT requires bounded integer domains.

## Callbacks

```python
class BestSoFar(cp_model.CpSolverSolutionCallback):
    def __init__(self):
        super().__init__()
        self.count = 0
    def on_solution_callback(self):
        self.count += 1
        print(f"[{self.wall_time:.2f}s] obj={self.objective_value} "
              f"bound={self.best_objective_bound}")
        # self.value(var) available here
        if self.objective_value == self.best_objective_bound:
            self.stop_search()

solver.solve(model, BestSoFar())
```

Separate hooks (assigned directly on `solver`, no subclass needed):

```python
solver.log_callback = lambda line: logger.info(line)
solver.best_bound_callback = lambda b: print(f"bound={b}")
```

**Performance**: callbacks force a Python ↔ C++ context switch. Keep them cheap.

## Serialization

In ortools 9.15+, the Python `model.proto` is a C++-backed wrapper that does not expose `SerializeToString()` directly. Use the built-in helper instead:

```python
# Binary proto (ortools ≥ 9.14)
model.export_to_file("model.pb")

# Human-readable text proto (always works via str())
with open("model.pbtxt", "w") as f:
    f.write(str(model.proto))
```

For older versions, the raw protobuf path still works:

```python
# ortools ≤ 9.13 style
from ortools.sat import cp_model_pb2
proto = cp_model_pb2.CpModelProto()
proto.CopyFrom(model.proto)
with open("model.pb", "wb") as f:
    f.write(proto.SerializeToString())
```

Load a saved binary proto back:

```python
from ortools.sat import cp_model_pb2
proto = cp_model_pb2.CpModelProto()
with open("model.pb", "rb") as f:
    proto.ParseFromString(f.read())
# Feed directly to solver:
solver = cp_model.CpSolver()
solver.solve(proto)   # solver.solve accepts a CpModelProto
```
