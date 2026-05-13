---
name: code-logic-compressibility-analyst
description: Analyzes code logic as observable behavior traces, predicate inventories, path cubes, and pure-region minimization candidates to reduce accidental decision complexity without rewriting code. Use when the user asks for code logic compression, boolean/control-flow minimization, branch merge candidates, predicate redundancy analysis, Quine-McCluskey or Karnaugh-map style reasoning, or safe refactor opportunities without behavior changes.
---

# Code Logic Compressibility Analyst

## Quick start

Given code, a function, a diff, or a target path, produce a behavior-preserving compressibility analysis only. Do not edit code unless the user separately asks for implementation.

## Purpose

Find opportunities to reduce accidental decision complexity while preserving the full observable behavior trace. Treat minimization as a proof obligation, not a rewrite instruction.

## Trigger examples

- "Analyze this function for compressible branches."
- "Find Quine-McCluskey/Karnaugh-map-like simplifications."
- "Can these guards be merged without changing behavior?"

## Primary invariant

Preserve observable behavior trace: return value, exception type/message, mutation, external call, emitted event, log/metric, state transition, side-effect ordering, and externally observable or audit-relevant failure reason.

## Core rules

- Do not rewrite, patch, or apply a refactor unless explicitly requested after the analysis.
- Partition logic before minimizing: pure decision region, effectful execution region, and mixed/unsafe region.
- Minimize only pure, reachable, known regions. Unknown behavior is `?`; never treat `?` as don't-care.
- Group by full observable outcome trace, not only return value.
- Do not remove or reorder side-effectful predicates unless side-effect equivalence and ordering are proven.
- Say "equivalent" only when proven or exhaustively verified; otherwise say "candidate" or "likely behavior-preserving".
- Do not over-compress security, payment, deletion, compliance, audit, or safety-critical logic.

## Workflow

1. Define the observable behavior boundary, including all externally visible values, failures, calls, mutations, logs, metrics, events, and ordering constraints.
2. Partition code into pure decision, effectful execution, and mixed/unsafe regions. Mark mixed/unsafe regions as analysis-only unless isolated.
3. Extract predicates. For each predicate record: ID, expression, domain, source location, evaluation order, `may_throw`, `may_mutate`, `may_call_external`, `requires_prior_guard`, redundant/derived/side-effectful status, and dependency relations.
4. Build path cubes or a decision table. Use `1` true, `0` false, `-` outcome-independent, `{a,b}` enum set, `[m,n]` range, `∅` impossible state, and `?` unknown.
5. Classify regions as reachable, unreachable, don't-care, or unknown. Only mark don't-care when the full observable outcome trace is guaranteed identical.
6. Group paths by full observable outcome trace, including side effects and externally observable failure reasons.
7. Minimize only pure, reachable, known groups using justified rules such as absorption, consensus-like predicate elimination, enum/range merging, dominant guards, and derived-predicate removal.
8. Generate prime-implicant-like rules for each minimized group.
9. For each candidate list generalized condition, outcome trace, covered original paths, excluded counterexamples, required assumptions, confidence, and equivalence level.
10. Compute metrics: `raw_path_count`, `minimized_rule_count`, `predicate_count_raw`, `predicate_count_effective`, `compression_ratio`, `predicate_reduction`, `semantic_risk`, `side_effect_risk`, `auditability_loss`, and `confidence`.
11. Propose refactor candidates only after metrics: branch merge, guard normalization, decision table, rule table, pattern matching, state-machine minimization, or redundant guard removal.
12. Provide a validation plan: golden tests, property-based tests, boundary tests, mutation tests, differential tests, and optional SAT/SMT check for pure predicate logic.
13. End with a risk note and never claim equivalence unless it is proven or exhaustively verified.

## Output format

Return sections in this order:

1. Behavior boundary
2. Region partition
3. Predicate inventory
4. Path cubes / decision table
5. Reachable vs unreachable vs don't-care vs unknown
6. Outcome trace groups
7. Minimized rules
8. Refactor candidates
9. Metrics
10. Validation plan
11. Final risk note
