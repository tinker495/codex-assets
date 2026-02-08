# Intent Abstraction Rubric

## Purpose
Use this rubric to decide whether multiple implementations are true domain variants that should remain separate, or accidental fragmentation that should be compressed.

## Core Claim
Treat "slightly different code paths with the same domain intention" as one conceptual unit until proven otherwise.

## Three Abstraction Gates

1. Behavioral gate
- Verify that merged logic preserves required outputs, side effects, and error boundaries for known valid inputs.
- Reject merge only when a real externally visible behavior difference is required.

2. Conceptual gate
- Verify that the merged unit names and represents a stable domain concept.
- Require that at least one domain-level invariant can be stated on the merged abstraction.
- Reject abstractions that are only "common code containers" with no domain meaning.

3. Physical gate
- Verify real physical compression: fewer branches, fewer duplicate maps, fewer forwarding wrappers, fewer normalization sites.
- Require net non-test LOC reduction or measurable complexity reduction.
- Reject changes that only move code without reducing maintenance surface.

## Intent Equivalence Tests

Mark implementations as intent-equivalent when most conditions hold:
- same preconditions after normalization
- same decision criteria under different symbol names
- same output schema or same canonical intermediate model
- same fallback/error semantics
- differences are transport-level (method path, key alias, container type), not business-rule-level

## Divergence Tests

Keep implementations separate only when at least one condition holds:
- distinct domain invariant per implementation
- legal/regulatory/contractual behavior differences
- materially different lifecycle timing or consistency guarantees
- incompatible output contract that cannot be represented by a single abstraction boundary

## Anti-Patterns to Remove

- alias explosion: many method names for one rule
- key-path drift: multiple key access paths to identical semantic field
- wrapper ladders: chains of one-line forwarders
- duplicated mapping constants across modules
- branch cloning where only local variable names differ

## Compression-Oriented Refactor Sequence

1. Canonicalize input shape.
2. Extract domain decision kernel.
3. Reattach transport-specific adapters only at edges.
4. Delete legacy duplicate paths.
5. Recompute non-test delta and re-run validation.

## Decision Log Template

Track every cluster with this compact log:

- `intent_id`:
- `current_variants`:
- `shared_domain_rule`:
- `behavioral_gate`: pass/fail + note
- `conceptual_gate`: pass/fail + invariant
- `physical_gate`: pass/fail + projected LOC delta
- `decision`: merge/keep-separate/delete
- `risk`:
