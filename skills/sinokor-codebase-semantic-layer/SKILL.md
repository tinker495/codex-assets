---
name: sinokor-codebase-semantic-layer
description: Use when answering Data Analytics or code-health questions about the snk2501o Sinokor stowage optimization repository, including repo risk, SPP benchmark evidence, TUI planning diagnostics, and source-backed onboarding context.
---

# Sinokor Codebase Semantic Layer

Use this skill to answer repository analytics questions with the source-backed context in `references/semantic-layer.md`.

## Start Here

1. Read `references/semantic-layer.md`.
2. Use the listed canonical docs, local source paths, git-history metrics, validation commands, and caveats.
3. Check freshness before answering time-sensitive repo, branch, benchmark, or contributor questions.
4. When source coverage is weak or stale, say so and verify against the cited local sources.

## References

- `references/semantic-layer.md`: canonical repo analytics context, metrics, source routes, query patterns, gotchas, and open questions.
- `references/source-inventory.md`: sources checked, coverage level, permissions, rejected candidates, and update boundaries.
- `references/evidence.md`: detailed provenance for facts captured during setup.

## Answering Rules

- Treat this skill as source-selection guidance, not as a substitute for live repo reads.
- Re-run git-history, benchmark, or test commands when a user asks for current results.
- Preserve the repo's stage boundaries: PreMPP, MPP, SPP, and PostSPP have separate contracts.
- Label stale, inferred, partial, or conflicted evidence.
