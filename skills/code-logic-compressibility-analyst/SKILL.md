---
name: code-logic-compressibility-analyst
description: Analyzes code logic as predicate/path cubes to find behavior-preserving compressibility, using Quine-McCluskey and Karnaugh-map style minimization analogies. Use when the user asks for code logic compression, boolean/control-flow minimization, branch merge candidates, predicate redundancy analysis, or safe refactor opportunities without changing behavior.
---

# Code Logic Compressibility Analyst

## Purpose

Find compressible logic in given code by modeling observable behavior, predicates, and control-flow paths before proposing refactors. This is an analysis workflow: do not edit code unless the user separately asks for implementation.

## Trigger examples

- "Analyze this function for compressible branches."
- "Find Quine-McCluskey/Karnaugh-map-like simplifications."
- "Can these guards be merged without changing behavior?"

## Core rules

- Preserve side effect ordering.
- Do not over-compress security, payment, deletion, or compliance logic.
- Say "equivalent" only when equivalence is proven or fully justified by tests/specs; otherwise say "candidate" or "likely behavior-preserving".
- Unknown behavior is `?`; never treat `?` as don't-care.
- Do not remove or reorder side-effectful predicates unless side-effect equivalence and ordering are proven.

## Workflow

### 1. Define observable behavior boundary

List every boundary that must be preserved: return value, exception type/message/timing when observable, mutation, external call, event/log/metric, state transition, and side effect ordering.

### 2. Extract predicates

For every predicate, record ID, expression, source location, domain, and flags. Domains are `boolean`, `enum`, `range`, `nullable`, `type`, `state`, or `external`. Flags are `redundant`, `derived`, and `side-effectful`. Count raw predicates and effective predicates separately.

### 3. Convert control flow to path cubes

Use this notation: `1` true, `0` false, `-` outcome-independent, `{a,b}` enum set, `[m,n]` range, `∅` impossible state, `?` unknown. Represent each path with predicate values, outcome, side effects, and source span, including fallthrough/default paths.

### 4. Separate unreachable and don't-care regions

Classify regions as reachable, unreachable by invariant/type/range/state constraint, true don't-care because the same observable outcome is guaranteed, or unknown `?`. Keep unknown separate from don't-care.

### 5. Minimize by outcome

Group path cubes with the same observable outcome and apply only justified rules: `(A && B) || (A && !B) -> A`; `A || (A && B) -> A`; merge enum sets with identical outcomes; merge adjacent ranges with identical outcomes; merge states with identical transition/output; remove predicates made redundant by dominant guards; remove derived predicates when source predicates already cover them.

### 6. Produce prime-implicant-like rules

For each generalized rule, include generalized condition, outcome, covered original paths, excluded counterexamples, and confidence (`high`, `medium`, `low`).

### 7. Calculate compressibility metrics

Report `raw_path_count`, `minimized_rule_count`, `predicate_count_raw`, `predicate_count_effective`, `compression_ratio = minimized_rule_count / raw_path_count`, `predicate_reduction = 1 - predicate_count_effective / predicate_count_raw`, overall confidence, and risk.

### 8. Suggest refactor candidates

Prefer simple reviewable candidates: branch merge, guard normalization, decision table, rule table, pattern matching, state machine minimization, or redundant guard removal. For each candidate, state the behavior boundary it must preserve and the risk that could invalidate it.

### 9. Validation plan

Recommend the smallest validation set that can support the claim: golden tests, property-based tests, boundary tests, mutation tests, differential tests, and optional SAT/SMT equivalence check for pure predicate logic.

## Output format

Return sections in this order:

1. Behavior boundary
2. Predicate inventory
3. Path cubes / decision table
4. Unreachable vs don't-care
5. Minimized rules
6. Metrics
7. Refactor candidates
8. Validation plan
9. Final risk note
