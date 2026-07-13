---
name: meta-clean-codebase
description: Finds meta-level deletion candidates that behavior-preserving cleanup cannot remove because today's behavior still exposes the old module, interface, path, mode, or compatibility shape. Use when the user asks for Meta Clean Codebase, meta clean, behavior-changing cleanup proposals, deletion candidates blocked by same-behavior constraints, or architecture cleanup beyond ai-slop-cleaner.
---

# Meta Clean Codebase

Identify modules that should probably disappear even though a strict same-behavior cleanup pass cannot delete them yet.

This skill sits between `$improve-codebase-architecture` and `$ai-slop-cleaner`: it uses architecture vocabulary to explain why a module is shallow or harmful, then produces a behavior-change proposal that a later cleanup pass can execute once the user authorizes the contract change.

## Core Rule

Default to read-only proposal mode.

Do not edit production code while using this skill unless the user explicitly authorizes a specific behavior change. The point is to surface places where "preserve identical behavior" is the blocker, not to smuggle behavior changes into a cleanup diff.

## Vocabulary

Use the `$improve-codebase-architecture` terms: **Module**, **Interface**, **Implementation**, **Depth**, **Shallow**, **Seam**, **Adapter**, **Leverage**, and **Locality**.

Use **same-behavior gate** for the blocker: current tests, callers, compatibility promises, or UI flows still require the old behavior, so `$ai-slop-cleaner` cannot safely remove it.

Use **meta deletion candidate** for a module that may be better removed after the project chooses a smaller canonical behavior.

## Workflow

1. Read contracts:
   - Read root `AGENTS.md`, then local `AGENTS.md` files before inspecting a subtree.
   - Read `CONTEXT.md` and relevant `docs/adr/` entries when they exist.
   - If another cleanup or architecture report exists, treat it as evidence, not authority.
2. Establish the same-behavior gate:
   - Identify the behavior, compatibility surface, tests, or callers that keep the module alive.
   - Separate current facts from proposed product or architecture choices.
3. Search for meta deletion candidates:
   - Legacy aliases, compatibility shims, alternate modes, duplicate paths, pass-through adapters, one-adapter seams, mirror models, stale config flags, fallback-like branches, and tests that pin deleted intent.
   - Prefer concrete file and line evidence over broad naming criticism.
4. Apply the deletion test:
   - If deleting the module only removes compatibility, duplicated vocabulary, or hypothetical extension points, it is a candidate.
   - If deleting it pushes real domain complexity into several callers, it is not a meta deletion candidate.
5. Classify recommendation strength:
   - **Strong**: the project already has a canonical replacement and the old interface only preserves stale behavior.
   - **Worth exploring**: the module looks shallow, but public compatibility, migration cost, or missing tests need a decision.
   - **Speculative**: the smell is real, but evidence is thin or the module may still carry hidden domain value.
6. Produce a report:
   - Prefer a self-contained HTML report in the OS temp directory for broad scans.
   - For narrow scans, a concise Markdown report is enough.
   - End with the single top recommendation and the exact behavior-change question the user must answer.

## Output Contract

For each candidate, include:

- **Files**: concrete paths and lines.
- **Same-behavior gate**: what currently prevents safe deletion.
- **Why meta-clean**: why preserving that behavior may be the wrong goal.
- **Proposed canonical behavior**: what behavior, interface, mode, or compatibility promise remains.
- **Deletion path**: tests to migrate, callers to change, docs or ADRs to update.
- **Risk**: users, data, contracts, or workflows that may depend on the removed behavior.
- **Recommendation strength**: `Strong`, `Worth exploring`, or `Speculative`.

## Handoff To Cleanup

Once the user approves a specific behavior change:

1. Write or update a behavior lock for the canonical behavior.
2. Co-migrate tests that pin the removed interface.
3. Run `$ai-slop-cleaner` on the approved scope.
4. Verify with targeted tests, lint, typecheck, and any relevant docs or architecture checks.

See [REFERENCE.md](REFERENCE.md) for candidate taxonomy, scoring, and report templates.
