---
name: no-deep-flag-review
description: "Review code for architecture violations where UI/presentation/execution mode flags (string, boolean, enum) are passed deep into domain, aggregator, or renderer internals. Use when performing PR review, architecture review, or refactoring guidance for the 'No Deep Flag Passing & Strategy Injection' principle, especially when repeated mode-based branching appears below system entry points."
---

# No Deep Flag Review

## Overview

Enforce one-time branching at the system boundary. Keep lower layers mode-agnostic by injecting behavior (callable, strategy object, delegate) instead of passing raw control flags.

## Review Scope

- Identify primitive control flags that represent UI/presentation/execution mode.
- Trace whether those flags propagate into lower-layer functions.
- Detect repeated branching by the same flag in non-entry layers.
- Verify boundary-only branching and strategy injection.

## Review Workflow

1. Map boundaries
   - Identify entrypoints (API handlers, widget callers, controller layer).
   - Identify lower layers (domain, aggregate, renderer internals).
2. Locate candidate flags
   - Find parameters like `mode`, `variant`, `viewType`, `isX`, enum-like mode values.
3. Trace propagation depth
   - Follow each flag through call chains.
   - Record where flag-based branch first appears and how often it repeats.
4. Classify findings
   - Mark violation when lower-layer logic branches on presentation/execution mode.
   - Escalate severity when the same flag is branched in multiple deep files/functions.
5. Propose minimal fix direction
   - Keep a single branch at the boundary.
   - Select strategy/delegate once at boundary.
   - Inject behavior to lower layers; lower layers invoke behavior only.

## Violation Criteria

- Non-entry layer contains `if/elif/switch` based on mode-like control flags.
- Same mode flag is branched in 2 or more lower-layer functions.
- Domain/aggregate logic references UI-oriented mode terms (`CARD_VIEW`, `TABLE_VIEW`, etc.).
- Function accepts mode-like flag solely to choose one of multiple calculations/render paths.

## Non-Violation Criteria

- Branching occurs only at boundary and immediately resolves to injected behavior.
- Conditional is unrelated to presentation/execution mode (validation, permission, null guard).
- Temporary adapter is isolated at boundary and includes explicit removal plan.

## Refactor Direction Template

- Boundary:
  - `if mode == A: strategy = ...; elif mode == B: strategy = ...`
- Lower layer:
  - Remove `mode` parameter.
  - Accept `strategy`/`delegate`/`callable`.
  - Replace branch with a single delegated call.

## Quick Search Patterns

- `rg -n "if .*mode|elif .*mode|switch\\s*\\(.*mode|case .*MODE" <target_paths>`
- `rg -n "(mode|variant|view|is_[a-z_]+)\\s*[:=]" <target_paths>`

## Reporting Format

- Report findings ordered by severity: `High`, `Medium`, `Low`.
- Provide one finding per item with:
  - `Location` (file and line)
  - `Violation` (how deep flag passing occurs)
  - `Why it matters` (shotgun-surgery/OCP risk)
  - `Minimal fix direction` (boundary branch + strategy injection)
  - `Mode-addition impact` (what breaks when adding new mode)

If no violation is found, state: `No deep flag passing violation found.` and include residual uncertainty.

## Guardrails

- Do not recommend broad rewrites when local strategy injection resolves the issue.
- Preserve behavior for current modes; require equivalence checks when refactor is proposed.
- Avoid speculative abstractions unless at least two call sites share the same strategy interface.
