# Tuning, Log Reading, Hints, and Callbacks

This file covers everything you do *around* the model: parameters, log interpretation, warm-starting, debugging infeasibility, and callbacks.

## 1. Essential parameters (set these first)

```python
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 60        # Always set in production
solver.parameters.log_search_progress = True      # On in development
solver.parameters.relative_gap_limit = 0.01       # 1% gap is usually enough
# solver.parameters.num_workers = 8               # Default uses all logical cores
```

Guidelines:
- **`max_time_in_seconds`**: start generous (300s), tighten once the model is stable.
- **`relative_gap_limit`**: 0.01–0.05 is a massive speedup on hard problems.
- **`num_workers`**: try `physical_cores`, `physical_cores * 2`, and `1`. Pick the winner empirically; more is not always better.
- **`random_seed`**: try 3–5 different seeds when benchmarking. CP-SAT is deterministic for a fixed seed + workers.

## 2. Reading the log — a walkthrough

Enable `log_search_progress = True` and read top-to-bottom.

### Header

```
Starting CP-SAT solver v9.10.4067
Parameters: max_time_in_seconds: 60 log_search_progress: true relative_gap_limit: 0.01
Setting number of workers to 16
```

Confirms version + effective parameters. If workers is less than expected, the system capped you.

### Initial model

```
#Variables: 450 (#bools: 276 #ints: 6 in objective)
  - 342 Booleans in [0,1]
  - 12 in [0][10][20][30][40][50][60][70][80][90][100]
#kLinear2: 1'811
#kNoOverlap: 2
```

- `#kLinear2` = linear constraint on 2 vars; `#kLinear3`, `#kLinearN` for higher arity. Many `#kLinear3`+ suggests you may be able to rewrite with `add_element`/tables.
- Domain notation `[0][10][20]...` = sparse domain. Use `new_int_var_from_domain` to communicate this.

### Presolve

```
Starting presolve at 0.00s
  6.60e-03s  0.00e+00d  [PresolveToFixPoint] #num_loops=4
  1.10e-02s  9.68e-03d  [Probe] #probed=1'738 #new_bounds=12 #new_binary_clauses=1'111
```

Columns: wall seconds, deterministic time units, rule. Large `#new_bounds` / `#new_binary_clauses` values = presolve is earning its keep. Slow presolve + few simplifications = consider `max_presolve_iterations = 3` or check if you can simplify the model yourself.

### Presolved model

```
Presolved optimization model '': (model_fingerprint: 0xb4e599720afb8c14)
#Variables: 405 (#bools: 261 #ints: 6 in objective)
#kLinear1: 854 (#enforced: 854)
```

Compare to initial. Significant variable reduction = presolve helped. Tiny reduction on a large initial model = try to tighten the model yourself (sparse domains, table constraints, redundant variables).

### Search events

Format: `EVENT  time  best:VAL  next:[LB,UB]  strategy(details)`

```
#1       0.06s best:-0    next:[1,7125]    fj_short_default(batch:1)
#2       0.07s best:1050  next:[1051,7125] fj_long_default(batch:1 #lin_moves:1'471)
#Bound   0.09s best:1050  next:[1051,1650] default_lp
#Model   0.13s var:404/405 constraints:1435/1468
```

- `#N` = N-th new best feasible solution.
- `#Bound` = tightened proven bound (search range narrows).
- `#Model` = variables/constraints fixed dynamically.

Interpretation:
- Many `#N`, few `#Bound` → feasibility easy, optimality hard. Symptoms of weak LP relaxation; try `linearization_level = 2` or add cutting constraints.
- Few `#N`, rapid `#Bound` → optimality proof is fast, feasibility is hard. Provide a hint.
- Both stall near the end of the time limit → your bound came from a specific subsolver; look at the subsolver summary to see which.

### Subsolver ranking

```
Solutions (7)             Num   Rank
                'no_lp':    3  [1,7]
        'quick_restart':    1  [3,3]

Objective bounds                     Num
             'objective_lb_search':    2
       'objective_lb_search_no_lp':    4
```

Tells you which subsolvers are productive on *your* problem. `no_lp` dominating means the LP relaxation is not helping — you could reduce `linearization_level` or remove LP workers in tight loops. `objective_lb_search` dominating bound discovery = your problem has hard lower-bound structure.

### LNS stats

```
LNS stats                Improv/Calls  Closed  Difficulty  TimeLimit
'routing_path_lns':          41/65     48%        0.10       0.10
'rins/rens':                 23/66     39%        0.03       0.10
```

Read as: this LNS neighborhood improved the incumbent 41 times in 65 calls. Low improvement rate on all LNS strategies is a sign the incumbent is near-optimal or stuck in a local structure.

### Final summary

```
CpSolverResponse summary:
status: FEASIBLE
objective: 1450
best_bound: 1515
gap_integral: 1292.47
walltime: 30.45
conflicts: 0
branches: 370
propagations: 13193
```

- `gap_integral` = ∫(gap over time). Lower = faster convergence; use it as a single KPI when benchmarking.
- `conflicts` / `branches` / `propagations` — sanity check. Zero conflicts on a hard-looking model often means LP alone closed it (great); extreme branches + zero conflicts usually means the model is too loose.

## 3. Hints (warm starts)

Hints bias initial search toward a known or guessed solution. Correct complete hints are the biggest free speedup you get.

```python
model.add_hint(x, 3)
model.add_hint(y, 7)
```

### Feasibility-check your hints

```python
solver.parameters.fix_variables_to_their_hinted_value = True
status = solver.solve(model)
assert status in (cp_model.OPTIMAL, cp_model.FEASIBLE), "hints infeasible"
solver.parameters.fix_variables_to_their_hinted_value = False
```

### Complete partial hints

Partial hints are slow to extend during search. Complete them upfront:

```python
def complete_hint(model, time_limit=5.0):
    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = time_limit
    s.parameters.fix_variables_to_their_hinted_value = True
    if s.solve(model) not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return False
    model.clear_hints()
    for i, v in enumerate(model.proto.variables):
        var = model.get_int_var_from_proto_index(i)
        model.add_hint(var, s.value(var))
    return True
```

### If presolve invalidates hints

Presolve can break symmetric hinted solutions. Guard with:

```python
solver.parameters.keep_all_feasible_solutions_in_presolve = True
```

Warning: may slow presolve. Measure the trade-off.

### Repair hints

```python
solver.parameters.repair_hint = True
```

Asks CP-SAT to treat hints as a *starting point* rather than as hard guidance — useful when your heuristic produces near-feasible but slightly broken hints.

## 4. Debugging infeasibility with assumptions

Wrap each suspect constraint with an indicator and add it as an assumption:

```python
ind = {}
for name, build_constraint in constraints_by_name.items():
    b = model.new_bool_var(f"ind_{name}")
    ind[name] = b
    build_constraint(model).only_enforce_if(b)

model.add_assumptions(list(ind.values()))
status = solver.solve(model)
if status == cp_model.INFEASIBLE:
    core = solver.sufficient_assumptions_for_infeasibility()
    for var_idx in core:
        print("Conflict:", model.proto.variables[var_idx].name)
```

The core is a *minimal* infeasible subset of assumption literals.

## 5. Callbacks — solution, bound, log

### Solution callback

```python
class PrintProgress(cp_model.CpSolverSolutionCallback):
    def __init__(self, start):
        super().__init__()
        self.start = start
    def on_solution_callback(self):
        elapsed = self.wall_time - self.start
        print(f"t={elapsed:7.2f}s  obj={self.objective_value}  "
              f"bound={self.best_objective_bound}")
        if self.objective_value == self.best_objective_bound:
            self.stop_search()

solver.solve(model, PrintProgress(0.0))
```

Inside the callback, `self.value(var)` works. Do not build complex Python data structures; the callback runs on the solver thread.

### Bound callback

Fires when the proven bound improves (unlike solution callbacks, which fire when a new feasible solution is found).

```python
def bound_cb(b):
    print(f"bound improved to {b}")
solver.best_bound_callback = bound_cb
```

### Log callback

Stream solver logs into your own logger instead of stdout:

```python
solver.parameters.log_to_stdout = False
solver.log_callback = lambda line: logger.info(line)
```

## 6. Enumerating solutions

```python
solver.parameters.enumerate_all_solutions = True

class Collect(cp_model.CpSolverSolutionCallback):
    def __init__(self, vars): super().__init__(); self.vars = vars; self.found = []
    def on_solution_callback(self):
        self.found.append([self.value(v) for v in self.vars])

cb = Collect([x, y, z])
solver.solve(model, cb)
print(len(cb.found), "solutions")
```

For satisfaction problems (no objective), this enumerates all feasible solutions. For optimization + `enumerate_all_solutions`, CP-SAT enumerates everything it finds; combine with objective gating if you only want all optima.

## 7. Diagnostic patterns

### "Which variable did the solver never pin?"

```python
solver.parameters.fill_tightened_domains_in_response = True
# Solve as a feasibility check (no objective or very loose one)
solver.solve(model)
for i, td in enumerate(solver.response_proto.tightened_variables):
    if len(td.domain) != 2 or td.domain[0] != td.domain[1]:
        print(i, "still open:", list(td.domain))
```

Great for spotting variables that propagation failed to bound; often a sign of a missing constraint.

### "Presolve report — what did CP-SAT simplify?"

Search the log for `rule '` lines; they summarize each presolve rule's count. Anomalously zero counts on a rule you expect to fire often = the model doesn't match the pattern that rule targets.

### "Where did time go?"

Per-subsolver statistics at the end of the log show wall time and deterministic time per subsolver. If one subsolver monopolizes time without contributing, you can disable it:

```python
solver.parameters.ignore_subsolvers.append("max_lp")
```

Use sparingly. Reserve this for post-benchmark tuning, not first-pass modeling.

## 8. Performance checklist before tuning parameters

Before you tweak a single parameter, verify:

- [ ] `log_search_progress = True` is on.
- [ ] Variables have meaningful names.
- [ ] No `sum(bs) == 1` — rewrite as `add_exactly_one`.
- [ ] No `x * y` inside `add(...)` — use `add_multiplication_equality`.
- [ ] No Big-M — replace with `only_enforce_if`.
- [ ] No `!=` alongside `add_all_different`.
- [ ] Sparse domains use `new_int_var_from_domain`.
- [ ] Hints are complete and feasibility-checked.
- [ ] Objective is integer; float costs scaled up at the boundary.

Only after this, touch `num_workers`, `linearization_level`, `subsolvers`.

## 9. Version-sensitive APIs (ortools 9.14+)

A few APIs have recently changed names or semantics. If any of these break, check your installed version with `python -c "import ortools; print(ortools.__version__)"`.

| API | Note |
|---|---|
| `solver.status_name()` | Broken in some 9.15.x builds (internal `status()` call raises). Safer pattern: map the returned enum yourself: `{cp_model.OPTIMAL: "OPTIMAL", cp_model.FEASIBLE: "FEASIBLE", cp_model.INFEASIBLE: "INFEASIBLE", cp_model.UNKNOWN: "UNKNOWN", cp_model.MODEL_INVALID: "MODEL_INVALID"}[status]`. |
| `model.proto.SerializeToString()` | Removed in 9.15. Use `model.export_to_file("model.pb")` or `str(model.proto)` for text proto. |
| `solver.solve(model, callback)` | Preferred. Older `SearchForAllSolutionsWithSolutionCallback` is deprecated. |
| `add_max_equality(target, exprs)` | Takes a list of expressions in current API. Older CamelCase `AddMaxEquality(target, *args)` accepted varargs. |
| `add_element(index, values, target)` | Keyword order in old versions was `(variables=..., index=..., target=...)`. Stick with positional (index, values, target). |
| `cp_model.OPTIMAL` et al. | In 9.15+ these are `CpSolverStatus` enum members, not ints. Equality comparison with the returned status still works. |

When in doubt, introspect: `print([m for m in dir(solver) if not m.startswith('_')])`.

## 10. Stateless solving — "incremental" pattern

CP-SAT doesn't reuse learned clauses across calls. Two options for incremental problems:

1. **Rebuild** the model each step with the new constraints. Fast enough for most use cases; the portfolio solver amortizes work.
2. **Assumptions**: add all potentially-active constraints once with `only_enforce_if(indicator)`, then vary the assumption set between calls. Works for Boolean gating only.
