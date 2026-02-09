---
name: complexity-loc-balancer
description: Orchestrate complexity reduction work while keeping non-test code growth at or below zero. Use when the user asks to lower radon/xenon risk without increasing runtime LOC, or when complexity-only refactors start adding helper bloat and need strict balancing gates.
---

# Complexity LOC Balancer

## Overview

Run a strict balancing loop that improves complexity metrics and prevents net non-test code growth.
Delegate structural reduction execution to `non-test-bloat-reduction` and metric evidence collection to `code-health`.

## Ownership

- Own decision gating between complexity gain and LOC growth risk.
- Own stop/continue decisions when tradeoffs conflict.
- Own cycle-level acceptance contract for balanced progress.

## Delegation

- Delegate executable reduction edits to `non-test-bloat-reduction`.
- Delegate health evidence (`radon`, `xenon`, diff summary) to `code-health`.
- Do not duplicate specialist internals from delegated skills.

## Workflow

1. Capture baseline snapshot.
- Collect:
  - non-test net delta (working and staged)
  - offending block count (`CC > 10`)
  - minimum required CC reduction estimate
  - xenon pass/fail
- Run the standard gate bundle from `references/complexity_gate_bundle.md`.

2. Build reduction candidates.
- Request intent clusters from `non-test-bloat-reduction`.
- Keep only candidates that can preserve behavior and plausibly avoid net LOC growth.

3. Apply bounded edit cycle.
- Run one cycle only:
  - minimal correct change
  - immediate simplification/deletion pass

4. Run balance gate.
- Accept cycle only when all checks pass:
  - offending blocks do not increase
  - minimum required CC reduction does not increase
  - non-test working net delta `<= 0`
  - xenon state does not regress
- If complexity improves but non-test net delta becomes positive, reject cycle and force deletion-only follow-up.

5. Publish cycle verdict.
- Return:
  - `accepted` or `rejected`
  - reason codes from `references/decision_matrix.md`
  - next highest-yield deletion targets

## Hard Rules

- Never classify a cycle as success when non-test working net delta is positive.
- Never claim xenon success unless command output confirms pass.
- Never compensate LOC growth with comment/docstring churn.
- Stop and report `balance_blocked` when two consecutive cycles fail balance gate.

## Resources

- Decision policy: `references/decision_matrix.md`
- Gate commands: `references/complexity_gate_bundle.md`
- Cycle checker: `scripts/quick_validate.py`
