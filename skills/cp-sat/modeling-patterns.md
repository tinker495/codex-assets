# Canonical Modeling Patterns

The difference between a fast and a slow CP-SAT model is almost always in the choice of constraint form. This file collects the idiomatic patterns the CP-SAT Primer recommends, with the MIP-style anti-pattern next to the CP-SAT-native replacement.

## 1. Scale floats to integers at the boundary

CP-SAT only reasons about integers. Convert costs / weights / durations by multiplying by the LCM of denominators, or by a fixed scale factor (e.g. 100 for two decimal places).

```python
# DON'T: raw floats
weights = [1.5, 2.3, 0.7]
model.add(sum(x[i] * weights[i] for i in I) <= 5.1)  # rejected

# DO: scale once at the boundary
scale = 10
w_int = [int(round(w * scale)) for w in weights]
cap_int = int(round(5.1 * scale))
model.add(sum(x[i] * w_int[i] for i in I) <= cap_int)
```

## 2. Replace Big-M with reification

Big-M formulations bloat domains and weaken relaxations. CP-SAT's LCG propagator handles reified constraints natively and far more tightly.

```python
# DON'T (MIP style):
M = 10_000
model.add(y >= a - b - M * (1 - z))  # if z then y >= a - b

# DO (CP-SAT native):
model.add(y >= a - b).only_enforce_if(z)
```

Two-sided implication ("z ⇔ y >= a - b"): add both directions.

```python
model.add(y >= a - b).only_enforce_if(z)
model.add(y <  a - b).only_enforce_if(z.Not())
```

## 3. Indicator variable for constraint gate

Wrap each "soft" / investigatable constraint in an indicator so you can later turn it on/off via assumptions or isolate infeasibility.

```python
c_ind = model.new_bool_var("limit_budget")
model.add(sum(x[i] * cost[i] for i in I) <= budget).only_enforce_if(c_ind)
model.add_assumption(c_ind)  # drop by replacing with c_ind.Not()
```

Combined with `solver.sufficient_assumptions_for_infeasibility()` this gives a minimal unsat core.

## 4. Exactly-one / at-most-one over booleans

Do not write `sum(bs) == 1`. The dedicated constraint is faster and yields better propagation.

```python
# DO:
model.add_exactly_one([b1, b2, b3])
model.add_at_most_one([b1, b2, b3])
```

## 5. Product of two booleans

`x * y` where both are booleans — do **not** put it inside `add(...)` directly.

```python
# DO:
xy = model.new_bool_var("x_and_y")
model.add_bool_and([x, y]).only_enforce_if(xy)
model.add_bool_or([x.Not(), y.Not()]).only_enforce_if(xy.Not())
```

Or more generally:

```python
prod = model.new_int_var(lb, ub, "prod")
model.add_multiplication_equality(prod, [x, y])
```

## 6. Absolute value, max, min

```python
abs_d = model.new_int_var(0, max_abs, "abs_d")
model.add_abs_equality(abs_d, x - y)

m = model.new_int_var(lb, ub, "m")
model.add_max_equality(m, [x, y, z])
```

## 7. Irregular feasible sets → table constraint

When the set of allowed tuples is small / irregular and painful to linearize, use an extensional constraint.

```python
# Valid (shift_type, skill, day) triples
allowed = [(0, 2, 1), (1, 2, 3), (1, 3, 0), ...]
model.add_allowed_assignments([shift, skill, day], allowed)
```

CP-SAT's table propagator is highly optimized; tables often beat complex Big-M encodings even for thousands of tuples.

## 8. Lookup / piecewise-constant value

```python
costs = [10, 14, 21, 30]
chosen_cost = model.new_int_var(min(costs), max(costs), "chosen_cost")
model.add_element(index=tier, variables=costs, target=chosen_cost)
```

For piecewise-linear: break the domain into segments, introduce one indicator per segment, reify the linear expression inside each.

## 9. Lexicographic multi-objective

Weighted sums collapse priorities and can miss the true Pareto optimum. For strict priorities, solve sequentially:

```python
model.minimize(f1)
status = solver.solve(model)
f1_star = int(solver.objective_value)

model.add(f1 == f1_star)        # freeze primary
model.clear_objective()         # or rebuild a new model
model.minimize(f2)
solver.solve(model)
```

If the primary objective has slack, use `model.add(f1 <= f1_star + slack)`.

## 10. Scheduling: no-overlap on one machine

```python
starts   = [model.new_int_var(0, horizon, f"s{i}") for i in range(n)]
ends     = [model.new_int_var(0, horizon, f"e{i}") for i in range(n)]
interv   = [model.new_interval_var(starts[i], durations[i], ends[i], f"iv{i}")
            for i in range(n)]
model.add_no_overlap(interv)
model.minimize(max(ends))   # use add_max_equality for proper makespan
```

For a makespan objective:

```python
makespan = model.new_int_var(0, horizon, "makespan")
model.add_max_equality(makespan, ends)
model.minimize(makespan)
```

## 11. Scheduling with optional assignment

Assign each job to one of K machines, machines are independent no-overlap resources.

```python
presence = [[model.new_bool_var(f"p_{j}_{m}") for m in machines] for j in jobs]
optional = [[None]*len(machines) for _ in jobs]
for j in jobs:
    model.add_exactly_one(presence[j])
    for m in machines:
        s = model.new_int_var(0, horizon, f"s_{j}_{m}")
        e = model.new_int_var(0, horizon, f"e_{j}_{m}")
        optional[j][m] = model.new_optional_interval_var(
            s, durations[j][m], e, presence[j][m], f"iv_{j}_{m}")

for m in machines:
    model.add_no_overlap([optional[j][m] for j in jobs])
```

## 12. Cumulative (limited parallel resource)

```python
model.add_cumulative(intervals, demands, capacity)
```

Each `demands[i]` is an expression (often a constant) — the sum of demands of active intervals at any time stays ≤ `capacity`.

## 13. Reservoir (running total bounded)

```python
# At times 0..T, level changes by +1 (refill) or -demand
model.add_reservoir_constraint(
    times=[t_refill_1, t_refill_2, t_drain_1],
    level_changes=[+10, +10, -7],
    min_level=0,
    max_level=15,
)
```

With conditional events:

```python
model.add_reservoir_constraint_with_active(
    times=[t1, t2, t3],
    level_changes=[+10, +10, -7],
    actives=[a1, a2, a3],   # Boolean literals
    min_level=0, max_level=15,
)
```

## 14. TSP via add_circuit

Directed Hamiltonian cycle over nodes `0..n-1`:

```python
arcs = []
for i in range(n):
    for j in range(n):
        if i == j:
            continue
        lit = model.new_bool_var(f"arc_{i}_{j}")
        arcs.append((i, j, lit))
model.add_circuit(arcs)
model.minimize(sum(lit * dist[i][j] for i, j, lit in arcs))
```

For optional nodes (you may skip some), add a self-loop with a boolean:

```python
for i in range(n):
    skip = model.new_bool_var(f"skip_{i}")
    arcs.append((i, i, skip))
```

## 15. VRP via add_multiple_circuit

Each vehicle is a circuit starting and ending at depot (node 0). `add_multiple_circuit` enforces disjoint circuits that collectively cover all non-depot nodes.

```python
arcs = []
for i in range(n):
    for j in range(n):
        if i == j:
            continue
        lit = model.new_bool_var(f"arc_{i}_{j}")
        arcs.append((i, j, lit))
# Self-loops at the depot are used to allow vehicles to stay idle
model.add_multiple_circuit(arcs)
```

Couple with cumulative / capacity constraints to model the full VRP.

## 16. All-different without `!=`

```python
# DO:
model.add_all_different([x1, x2, x3, x4])

# DON'T (disables the global propagator):
for i in range(len(xs)):
    for j in range(i+1, len(xs)):
        model.add(xs[i] != xs[j])
```

## 17. Sparse domains via Domain

```python
from ortools.sat.python.cp_model import Domain
d = Domain.from_values([10, 25, 40, 75])   # only these values allowed
x = model.new_int_var_from_domain(d, "x")

d2 = Domain.from_intervals([[0, 5], [10, 15]])
y = model.new_int_var_from_domain(d2, "y")  # y ∈ [0,5] ∪ [10,15]
```

Tight domains reduce propagation work and often simplify the model.

## 18. Channeling: integer ↔ booleans

To branch on individual value choices of an integer variable, tie each value to a boolean:

```python
x = model.new_int_var(0, n-1, "x")
is_val = [model.new_bool_var(f"x_eq_{v}") for v in range(n)]
model.add_exactly_one(is_val)
for v in range(n):
    model.add(x == v).only_enforce_if(is_val[v])
    model.add(x != v).only_enforce_if(is_val[v].Not())
```

Often lets you attach conditional constraints without reasoning about integer equality.

## 19. Soft constraints with penalty

```python
viol = model.new_bool_var("viol")
model.add(load <= capacity).only_enforce_if(viol.Not())
# No corresponding constraint for viol = true → solver is free to violate
model.minimize(base_cost + 1_000 * viol)
```

Tune penalty relative to cost scale.

## 20. Symmetry breaking

If `k` identical resources exist, fix an ordering to kill permutation symmetry:

```python
# jobs assigned to machines 0..k-1; break symmetry on first job each touches
model.add(first_job[0] <= first_job[1])
model.add(first_job[1] <= first_job[2])
```

CP-SAT's presolve will also detect some symmetries automatically, but manual hints help on structured problems.

## Summary: the Big-M → CP-SAT Rosetta stone

| MIP Big-M / linear | CP-SAT native |
|---|---|
| `y >= a - M*(1-z)` | `model.add(y >= a).only_enforce_if(z)` |
| `sum(bs) <= 1` | `model.add_at_most_one(bs)` |
| `sum(bs) == 1` | `model.add_exactly_one(bs)` |
| `x*y` (booleans) | `add_bool_and` + reification or `add_multiplication_equality` |
| `|x-y| <= c` | aux + `add_abs_equality`, then `add(aux <= c)` |
| Disjunction of two linears | reify each via `.only_enforce_if(b)` + `add_exactly_one([b, b.Not()])` |
| Integer choice from set | `new_int_var_from_domain` or `add_allowed_assignments` |
| Precedence "A before B if both selected" | `add(end_a <= start_b).only_enforce_if([pres_a, pres_b])` |
| Pairwise `!=` | `add_all_different` |
| Piecewise linear cost | `add_element` + segment indicators + reified linears |
