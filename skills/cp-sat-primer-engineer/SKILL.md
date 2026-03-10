---
name: cp-sat-primer-engineer
description: Use when modeling, debugging, benchmarking, or productionizing Google OR-Tools CP-SAT optimization problems such as scheduling, assignment, packing, routing-adjacent discrete planning, and combinatorial resource allocation.
---

# CP-SAT Primer Engineer

Distilled from *The CP-SAT Primer* by Dominik Krupke and contributors.
Attribution preserved under CC BY 4.0.

## Objective

Own the OR-Tools CP-SAT workflow for discrete optimization tasks.
Decide whether CP-SAT is the right tool, translate business rules into a correct integer model, debug infeasibility or slow solves, and deliver maintainable production-oriented code.

Prefer Python unless the user explicitly asks for another language.

## When to Use

Use this skill when the task involves one or more of the following:

- assignment or matching,
- scheduling or staff rostering,
- packing or configuration,
- bounded-integer resource allocation,
- sequence constraints,
- logical or reified rules,
- combinatorial optimization with many binary or bounded integer decisions,
- debugging or improving an existing OR-Tools CP-SAT model,
- productionizing a CP-SAT-backed API, benchmark, or solve workflow.

Typical fit signals:

- the problem is mostly about selecting a feasible or best combination,
- decisions are discrete rather than naturally continuous,
- the model needs logic, intervals, circuits, cumulative constraints, tables, or automata,
- the main pain is modeling correctness, infeasibility, or search performance.

## When Not to Use First

Prefer another tool, or at least present the alternative explicitly, when:

- the model is mostly linear with many continuous variables,
- floating-point coefficients are essential,
- dual values are required,
- incremental solver-state reuse is central,
- the task is pure TSP, VRP, network flow, SAT, or SMT.

Default alternatives:

- LP/MIP/MathOpt when the problem is mostly linear and continuous,
- OR-Tools Routing for classical routing workflows,
- dedicated flow solvers for pure network flow,
- SAT/SMT for pure verification or logic search.

Do not replace optimization with ML or LLM heuristics by default.

## Required Intake Before Coding

When the user gives a vague business problem, do not jump straight into code.
First derive and confirm:

1. Input schema
2. Decision variables
3. Hard constraints
4. Soft constraints or penalties
5. Objective hierarchy
6. Output contract

If any of these are ambiguous, surface the ambiguity explicitly before implementing.

## Standard Workflow

### 1. Fit Assessment

Classify the task as one of:

- CP-SAT fits well
- CP-SAT fits, but alternatives should be noted
- CP-SAT is not the primary recommendation

### 2. Define Typed Schemas

Create explicit schemas for:

- instance data,
- solver configuration,
- solution output.

Prefer `dataclasses` or `pydantic`.

### 3. Write a Solver-Independent Validator

Define plain-Python validation that can verify:

- feasibility,
- objective value,
- business invariants.

Use this validator for tests and for checking returned solutions.

### 4. Choose Variables With Tight Bounds

For each variable, state:

- what it means,
- its domain,
- why the bounds are tight enough,
- whether it is core or auxiliary.

Avoid lazy domains like `0..1_000_000_000` unless justified.

### 5. Add Hard Constraints First

Group constraints by business meaning.
Prefer strong global constraints over many weak linear fragments when a native CP-SAT constraint matches the intent.

### 6. Add Objectives Deliberately

Use:

- no objective for pure feasibility,
- a single linear objective when the business goal is singular,
- sequential solves for lexicographic goals,
- weighted sums only when the tradeoff is genuinely intended and interpretable.

Do not invent an objective when the task is satisfaction-only.

### 7. Solve With Instrumentation

During development, default to:

- finite time limits,
- `log_search_progress = True`,
- status reporting,
- objective and best-bound reporting.

### 8. Validate the Returned Solution

Run the solver-independent validator on every produced solution before claiming success.

### 9. Optimize the Model Before Tuning Parameters

First improve:

- bounds,
- formulations,
- symmetry breaking,
- auxiliary-variable count,
- Python-side model build efficiency,
- decomposition or neighborhood design.

Parameter tuning is secondary.

## Modeling Rules

### Variables

- Use `BoolVar` for 0/1 choices and `IntVar` for bounded integer quantities.
- Keep bounds tight and justified.
- Do not treat general integers as truthy flags.
- Use custom domains only when they meaningfully shrink search or encode real structure.
- If parity or step size is the only reason for a sparse domain, prefer substitution such as `x = 2 * x_prime`.

### Objectives

- CP-SAT optimizes linear expressions.
- For nonlinear intent, introduce auxiliary variables and linking constraints.
- For lexicographic objectives, solve sequentially and pin the earlier result to an exact value or tolerance before optimizing the next objective.
- Keep hard requirements as constraints unless they are intentionally soft.

### Constraints

- CP-SAT is integer-only. Scale fractional quantities explicitly.
- Avoid floating-point coefficients in constraints.
- Normalize equations so the integer model is exact rather than approximately correct.
- Prefer semantic constraints such as `add_all_different`, `add_exactly_one`, and `add_at_most_one` over ad hoc weaker formulations.

### Logical Modeling

Use Boolean constructs directly:

- `add_bool_or`
- `add_bool_and`
- `add_bool_xor`
- `add_implication`
- `add_exactly_one`
- `add_at_most_one`

Remember:

- `A -> B` is modeled as implication or `not A or B`,
- `add_bool_xor` means odd parity, not "exactly one" for 3+ terms.

### Reification

Use `only_enforce_if` for true conditional constraints.
Do not wrap large parts of the model in reification unless the condition is logically necessary.
If a condition merely selects among cases, compare whether a tighter formulation exists.

### Scheduling Structures

For interval-based problems, prefer interval variables with:

- `add_no_overlap`,
- `add_no_overlap_2d`,
- `add_cumulative`,
- optional intervals when tasks may or may not exist.

Use these instead of manually reproducing the same semantics with many pairwise inequalities.

## Debugging Checklist

When the model is infeasible:

1. Re-check data normalization and scaling.
2. Verify every bound against business reality.
3. Reduce to a minimal failing instance.
4. Temporarily relax suspected constraints one family at a time.
5. Validate whether the intended business rules are mutually consistent.

When the model is slow:

1. Tighten bounds.
2. Strengthen the formulation.
3. Remove unnecessary auxiliary variables.
4. Break symmetry where safe.
5. Improve Python-side construction hot spots.
6. Only then tune solver parameters, decision strategies, hints, or LNS.

When reporting solver results:

- say `OPTIMAL` only for the `OPTIMAL` status,
- if the result is `FEASIBLE`, also report objective value, best bound, and stopping condition,
- include the optimality gap when it is available or derivable.

## Production Guidance

- Keep input, config, and output contracts explicit and typed.
- Return solver status, objective, best bound, and any validation summary.
- Benchmark on representative instance sets rather than a single toy case.
- Add reproducibility controls when repeated comparisons matter.
- Use warm starts, hints, decomposition, or LNS only after the baseline model is correct and validated.
- When API or version behavior is uncertain, check official OR-Tools documentation before relying on a detail.

For post-correctness tuning, log forensics, repeated-solve optimization, or advanced LNS and worker strategies, use `cp-sat-performance-and-advanced-features`.

## Expected Deliverables

For substantial requests, produce:

- a fit assessment,
- typed schemas,
- the model implementation,
- a solver-independent validator,
- at least one small reproducible test instance,
- a brief explanation of the chosen formulation and its main risks.
