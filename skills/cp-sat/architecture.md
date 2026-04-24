# Production Architecture for CP-SAT Solvers

From the CP-SAT Primer's "Coding Patterns", "Test-Driven Development", "Optimization API", and "Benchmarking" chapters. This file covers how to turn a working CP-SAT notebook into something you can deploy, test, and benchmark.

## 1. Four-layer solver class

Split responsibilities into four files:

```
my_solver/
  models.py       # Pydantic input/output schemas
  solver.py       # CP-SAT model construction + solve
  db.py           # Persistence (Redis, SQL, etc.)
  service.py      # FastAPI endpoints
```

### models.py — Pydantic schemas

Validate at the boundary so the solver only ever sees clean data.

```python
# Python 3.10+ for PEP 604 `int | None` syntax.
# On Python 3.9, either add `from __future__ import annotations` AND `pip install
# eval_type_backport`, OR replace `int | None` with `Optional[int]` from typing.
from pydantic import BaseModel, Field

class DirectedEdge(BaseModel):
    source: int = Field(..., ge=0)
    target: int = Field(..., ge=0)
    weight: int = Field(..., ge=0)

class TspInstance(BaseModel):
    num_nodes: int = Field(..., gt=0)
    edges: list[DirectedEdge]

class OptimizationParameters(BaseModel):
    timeout: int = Field(default=60, gt=0)
    relative_gap_limit: float = Field(default=0.01, ge=0.0)
    num_workers: int | None = Field(default=None, ge=1)

class TspSolution(BaseModel):
    node_order: list[int] | None = None
    cost: int | None = None
    lower_bound: int | None = None
    status: str
```

Use `default_factory` for optional fields so you can extend the schema without breaking older clients.

### solver.py — encapsulate model building

```python
from ortools.sat.python import cp_model
from typing import Callable

class TspSolver:
    def __init__(self, instance: TspInstance, params: OptimizationParameters):
        self.instance = instance
        self.params = params
        self.model = cp_model.CpModel()
        self.arc_vars = {
            (e.source, e.target): self.model.new_bool_var(
                f"arc_{e.source}_{e.target}")
            for e in instance.edges
        }
        self._build_constraints()
        self._build_objective()

    def _build_constraints(self):
        arcs = [(s, t, v) for (s, t), v in self.arc_vars.items()]
        self.model.add_circuit(arcs)

    def _build_objective(self):
        weights = {(e.source, e.target): e.weight for e in self.instance.edges}
        self.model.minimize(
            sum(self.arc_vars[k] * weights[k] for k in self.arc_vars))

    def solve(self, log_callback: Callable[[str], None] | None = None) -> TspSolution:
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = self.params.timeout
        solver.parameters.relative_gap_limit = self.params.relative_gap_limit
        if self.params.num_workers is not None:
            solver.parameters.num_workers = self.params.num_workers
        if log_callback is not None:
            solver.parameters.log_search_progress = True
            solver.parameters.log_to_stdout = False
            solver.log_callback = log_callback
        status = solver.solve(self.model)
        return self._extract(solver, status)

    def _extract(self, solver, status) -> TspSolution:
        status_name = solver.status_name()
        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            return TspSolution(status=status_name)
        # Reconstruct the tour from chosen arcs
        next_of = {s: t for (s, t), v in self.arc_vars.items()
                   if solver.value(v) == 1}
        order, cur = [0], 0
        while True:
            cur = next_of[cur]
            if cur == 0: break
            order.append(cur)
        return TspSolution(
            node_order=order,
            cost=int(solver.objective_value),
            lower_bound=int(solver.best_objective_bound),
            status=status_name,
        )
```

Notes:
- Store decision variables as dicts keyed by meaningful tuples; you need them in `_extract`.
- Keep `solve()` pure — given identical input, identical output (modulo solver nondeterminism).
- Expose `log_callback` so the caller (API, CLI, Jupyter) can route logs anywhere.

### db.py — persistence proxy

One class owning all DB interactions. Swappable for tests.

```python
import redis, json
from uuid import UUID

class TspJobDb:
    def __init__(self, client: redis.Redis, ttl_seconds: int = 24 * 3600):
        self.client = client
        self.ttl = ttl_seconds

    def register(self, job_id: UUID, request: dict) -> None:
        self.client.setex(f"req:{job_id}", self.ttl, json.dumps(request))
        self.client.setex(f"status:{job_id}", self.ttl, "Pending")

    def set_status(self, job_id: UUID, status: str) -> None:
        self.client.setex(f"status:{job_id}", self.ttl, status)

    def set_solution(self, job_id: UUID, solution: dict) -> None:
        self.client.setex(f"sol:{job_id}", self.ttl, json.dumps(solution))
```

### service.py — FastAPI + RQ

```python
from fastapi import FastAPI, Depends
from rq import Queue
import redis
from uuid import uuid4

app = FastAPI(title="TSP Optimization API")

def get_db():
    return TspJobDb(redis.Redis(host="redis", port=6379, db=0))

def get_queue():
    return Queue(connection=redis.Redis(host="redis", port=6379, db=1))

@app.post("/tsp/submit")
def submit(req: TspInstance,
           db: TspJobDb = Depends(get_db),
           q: Queue = Depends(get_queue)):
    job_id = uuid4()
    db.register(job_id, req.model_dump())
    q.enqueue(run_job, str(job_id))
    return {"job_id": str(job_id), "status": "Pending"}

@app.get("/tsp/status/{job_id}")
def status(job_id: str, db: TspJobDb = Depends(get_db)):
    return {"status": db.get_status(job_id)}

def run_job(job_id: str):
    db = get_db()
    db.set_status(job_id, "Running")
    req = TspInstance(**db.get_request(job_id))
    sol = TspSolver(req, OptimizationParameters()).solve()
    db.set_solution(job_id, sol.model_dump())
    db.set_status(job_id, "Completed")
```

Key points:
- Worker pulls the *request* from Redis, not from arguments — avoids large payloads in the queue.
- Workers and API process are separate containers.
- `TTL` on Redis keys auto-cleans stale jobs.

## 2. Test-driven development for solvers

CP-SAT solvers have a clean test hierarchy. Write each tier before moving on.

### Tier 1: sanity on tiny known-optimal instances

Hand-compute optimal values for 2–5 trivial instances and check the solver hits them.

```python
def test_tsp_triangle():
    inst = TspInstance(num_nodes=3, edges=[
        DirectedEdge(source=0, target=1, weight=1),
        DirectedEdge(source=1, target=2, weight=2),
        DirectedEdge(source=2, target=0, weight=3),
        DirectedEdge(source=0, target=2, weight=3),
        DirectedEdge(source=2, target=1, weight=2),
        DirectedEdge(source=1, target=0, weight=1),
    ])
    sol = TspSolver(inst, OptimizationParameters(timeout=5)).solve()
    assert sol.status == "OPTIMAL"
    assert sol.cost == 6
```

### Tier 2: invariant tests

Solutions must satisfy the constraints — verify independently of the solver's claim.

```python
def verify_tour(inst: TspInstance, sol: TspSolution) -> None:
    assert sol.node_order is not None
    assert set(sol.node_order) == set(range(inst.num_nodes))
    assert len(sol.node_order) == inst.num_nodes
    weights = {(e.source, e.target): e.weight for e in inst.edges}
    computed = sum(weights[(sol.node_order[i],
                            sol.node_order[(i+1) % len(sol.node_order)])]
                   for i in range(len(sol.node_order)))
    assert computed == sol.cost
```

Run this verifier inside every higher-level test.

### Tier 3: bound sanity

```python
assert sol.lower_bound <= sol.cost
if sol.status == "OPTIMAL":
    assert sol.lower_bound == sol.cost
```

### Tier 4: regression pins

Store `(instance, expected_cost, timeout)` triples. Re-run on every model change; a regression is any worse cost on the same instance/time budget.

```python
REGRESSION = [
    ("instances/random_50_a.json", 1450, 10),
    ("instances/random_50_b.json", 1112, 10),
]

@pytest.mark.parametrize("path,expected,tl", REGRESSION)
def test_regression(path, expected, tl):
    inst = TspInstance.model_validate_json(open(path).read())
    sol = TspSolver(inst, OptimizationParameters(timeout=tl)).solve()
    assert sol.cost <= expected   # improvements are welcome
```

### Tier 5: property-based

Generate random instances, assert the solution is valid and cost ≥ a trivial lower bound (e.g., sum of each node's cheapest outgoing edge).

## 3. Benchmarking

### What to measure

| Metric | Use when |
|---|---|
| **Mean runtime** | All instances solved to optimality. |
| **Cactus plot** (x=time, y=#instances solved) | Mix of solved and timed-out. |
| **Performance profile** (Dolan & Moré) | Solution quality comparison with unknown optimum. |
| **Primal integral** / `gap_integral` | Speed-of-convergence. |
| **PAR10** (unsolved counted as 10× timeout) | Single scalar ranking across solved + unsolved. |

Always plot at least one visualization + show a table of raw numbers. Aggregates hide failure modes.

### Folder layout

```
evaluations/
  2026-04-17_tsp_linearization_lvl/
    README.md               # hypothesis, setup, findings
    PRIVATE_DATA/           # full raw logs (may contain secrets)
    PUBLIC_DATA/            # curated, shareable CSVs
    _utils/                 # shared helpers (ok to duplicate across studies)
    00_generate_instances.py
    01_run_experiments.py
    02_plot.py
```

Rules:
- `README.md` even if rough — future-you forgets.
- Persist instances as files, not random seeds.
- Experiments must be resumable: check "already done" before running each trial, write results incrementally.
- Run with `slurm`, `slurminade`, or similar — the solver's determinism + multi-run seeding is easy to parallelize.

### Exploratory vs workhorse studies

- **Exploratory**: notebook, lightweight, goal is "what's a realistic problem size and roughly which parameters matter". Do not over-engineer.
- **Workhorse**: structured, reproducible, publishable. Starts from a hypothesis. Do **not** reuse exploratory data — regenerate from scratch so the protocol is consistent.

### Avoid these benchmarking pitfalls

1. **Tuning on <10 instances** — you'll overfit and disable strategies that matter on problems you never tested.
2. **Discarding timeouts** — biases toward easy instances. Use cactus plots / PAR instead.
3. **Confusing seed noise with signal** — run ≥3 seeds per (instance, config) and report variance.
4. **Anonymized "realistic" datasets** — often have had their statistics scrambled; don't assume realism.
5. **Benchmarking without `log_search_progress`** — the log is your best debugging signal when a config performs unexpectedly.
6. **Python model-build bottleneck** — if your model takes longer to build than CP-SAT takes to solve, profile with `scalene`. Common cause: nested loops creating `O(n^3+)` variables.

### Reporting

Include:
- Cactus plot (always)
- Per-config mean ± std of gap_integral
- Table of raw per-instance results for the top instances
- Discussion of *threats to validity* (seed count, instance diversity, hardware)

## 4. Solver cookbook — deployment checklist

Before shipping:

- [ ] Pydantic schemas validate every input field.
- [ ] `TspSolver.solve()` accepts a `log_callback` for log routing.
- [ ] `max_time_in_seconds` is always set from config, never unlimited.
- [ ] API returns status (`Pending`/`Running`/`Completed`/`Failed`) separately from the solution.
- [ ] Long jobs go through a task queue (RQ/Celery), not the request thread.
- [ ] Redis keys have a TTL.
- [ ] Tier 1–3 tests in CI.
- [ ] At least one regression test per problem variant.
- [ ] Benchmark folder with README, generate / run / plot scripts.
- [ ] Performance characteristics documented: typical time to solve, gap at time limit, instance size regime.

## 5. Common architectural anti-patterns

| Anti-pattern | Why bad | Fix |
|---|---|---|
| Solver called synchronously from HTTP handler | Request times out for hard instances | Queue + worker |
| Model built from raw dicts | Silent bad input kills solver | Pydantic validation |
| Tests run on production-size instances | Slow feedback loop | Tiny instances for tier 1–2 |
| Single "god function" builds model | Hard to test, hard to extend | Solver class with `_build_*` methods |
| No log piping | Can't diagnose production slowdowns | `log_callback` routed to logger |
| Results stored in-memory | Lost on worker restart | Persist to Redis/SQL |
| Random-seed-only instance persistence | Reproducibility rots with codebase | Write instances to disk |
| Aggregate-only benchmark reports | Failure modes hidden | Always include cactus plot + raw table |
