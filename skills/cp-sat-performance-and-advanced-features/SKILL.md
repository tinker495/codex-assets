---
name: cp-sat-performance-and-advanced-features
description: Use when speeding up, hardening, or scaling an existing Google OR-Tools CP-SAT model after baseline correctness is already established. Trigger on CP-SAT log forensics, worker or subsolver tuning, repeated-solve workflows, warm starts, assumptions or unsat-core debugging, multi-phase objectives, advanced native constraint choices, and domain-specific LNS or repair strategies.
---

# CP-SAT Performance And Advanced Features

Distilled from *The CP-SAT Primer* advanced guidance by Dominik Krupke and contributors.
Attribution preserved under CC BY 4.0.

## Objective

Own the advanced OR-Tools CP-SAT optimization stage after a correct baseline already exists.
Use this skill to classify performance bottlenecks, choose stronger native formulations, exploit repeated-solve structure, and tune workers or subsolvers only when logs justify it.

If basic correctness, schema design, or core modeling is still unstable, fall back to `cp-sat-primer-engineer` first.

## Activation Gate

Use this skill only when most of the following are already true:

- the baseline model is already feasible and validated,
- a solver-independent validator exists,
- CP-SAT logs can be enabled and collected,
- there is at least one reproducible benchmark instance,
- the task is now about speed, bounds, scaling, hints, assumptions, LNS, or advanced primitives rather than first-pass modeling.

Typical triggers:

- "Why is this CP-SAT model still slow?"
- "Analyze this CP-SAT log."
- "Why do 32 workers lose to 8?"
- "Why do hints not help?"
- "How should I scale repeated solves?"
- "Should this use intervals, circuit, automaton, reservoir, or another stronger primitive?"
- "How do I add LNS or repair search?"

## Required Output

For substantial requests, return:

1. Bottleneck classification
2. Evidence from logs and code
3. Top interventions ordered by ROI
4. Exact model or code changes
5. Benchmark plan with acceptance criteria
6. Risk and rollback notes

If logs are missing, instrument first instead of tuning blindly.

## First Pass

### 1. Separate Build Time From Solve Time

Always measure both:

- Python model-construction time
- solver wall time

Do not blame CP-SAT for a slow generator.

### 2. Turn On Minimum Instrumentation

During diagnosis, default to:

- `log_search_progress = True`
- a finite time limit
- captured raw logs
- objective and best-bound reporting
- benchmark instance identity
- OR-Tools version, Python version, hardware, worker count, and parameter block

### 3. Classify the Bottleneck

Ask in this order:

1. Is build time the real bottleneck?
2. Does presolve dominate?
3. Is the problem first-feasible latency?
4. Is the problem proof or bound quality?
5. Are worker count or subsolvers helping or hurting?
6. Is this really a repeated short-solve workflow?

## Optimization Order

Apply improvements in this order:

1. Remove generator mistakes and duplicated work
2. Tighten bounds and domains
3. Replace weak formulations with stronger native primitives
4. Add safe symmetry breaking or redundant strengthening constraints
5. Exploit repeated-solve structure with hints, assumptions, or phase-based optimization
6. Only then tune workers, subsolvers, and search parameters

Never justify a tuning change with a tiny cherry-picked benchmark set.

## Advanced Capabilities

### Stronger Native Structures

Prefer stronger modeling choices when the structure exists:

- intervals and cumulative constraints for scheduling,
- circuit-style constraints for sequence or routing-like structure,
- automaton or table constraints for pattern-heavy logic,
- reservoir or other native globals when they match the domain,
- auxiliary-linking reformulations for nonlinear intent.

### Log Forensics

Use logs to determine whether time is going into:

- presolve cleanup,
- first solution search,
- bound improvement,
- LP-related subsolvers,
- generic LNS,
- unproductive worker contention.

Do not change parallelism or subsolvers without log evidence.

### Repeated Solves

When the model is solved many times with small deltas:

- retain benchmark discipline,
- reuse prior incumbents as hints,
- tighten domains from prior results when justified,
- split lexicographic goals into phases,
- consider assumptions for scenario toggles,
- consider a domain-specific repair loop instead of full cold starts.

### Hints, Assumptions, And Unsat Debugging

- Use hints only after validating that the hinted structure is relevant and mostly feasible.
- Use assumptions when scenario flags or explainable infeasibility matter.
- Use unsat-core style debugging to isolate conflicting optional assumptions, not as a substitute for basic model validation.

### LNS And Repair Search

When full exact search stalls but good incumbents exist:

- define neighborhoods around meaningful business structure,
- freeze most of the incumbent and reopen targeted slices,
- benchmark neighborhood design instead of assuming generic LNS is enough,
- keep rollback paths if repair quality regresses.

## Benchmark Discipline

- Export the model when comparing machines, versions, or parameter sets.
- Compare fixed versions and fixed benchmark sets.
- Report status, objective, best bound, wall time, and raw-log path.
- Accept a change only if it wins on the representative benchmark distribution, not just one easy instance.

## Resource

Read [advanced_playbook.md](references/advanced_playbook.md) when you need the longer checklist, instrumentation example, and advanced tuning guidance derived from the provided draft.

## Resources (optional)

### references/

- `references/advanced_playbook.md`: condensed advanced guide for instrumentation, bottleneck triage, hints, assumptions, worker tuning, and LNS workflow.
