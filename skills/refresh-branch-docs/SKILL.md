---
name: refresh-branch-docs
description: Execute branch-scoped, end-to-end documentation refresh after code changes. Use when users ask to comprehensively rewrite/update docs and AGENTS based on current branch diff, onboarding context, repo-local docs as SSOT, and code evidence, including refreshes to design/plan/quality docs that preserve agent legibility. Prefer this for broad behavior/narrative synchronization; use docs-codebase-alignment-audit for narrow integrity audit/fix tasks.
---

# Refresh Branch Docs

## Mission
Refresh internal docs so they match current branch behavior without losing map-first navigation quality.
Default to incremental delta refresh; use full refresh only when explicitly requested or when drift is widespread.
Collect evidence first, then rewrite docs with explicit anchors.
Prefer repo-local, versioned artifacts over external summaries. If important operating context only exists outside the repository, encode it into the refreshed docs or linked references.

```mermaid
flowchart LR
  A["Branch Onboarding"] --> B["Impact Mapping"]
  B --> C["Code Evidence"]
  C --> D["Doc Rewrite"]
  D --> E["Mechanical Validation"]
  E --> F["Delivery Brief"]
```

## Harness Alignment Goals

1. Keep `AGENTS.md` map-first, not encyclopedia-first.
2. Keep As-Is/To-Be SSOT boundaries explicit (`docs/_meta/docs-contract.md`).
3. Preserve progressive disclosure (`AGENTS.md` -> `docs/index.md` -> leaf docs).
4. Enforce docs integrity with machine checks (`docs-check` or equivalent).
5. Separate blocking fixes from doc-gardening backlog.
6. Anchor evaluation/performance docs to code-defined metric SSOT and explicit baselines.
7. Preserve agent legibility: make critical context discoverable from repository-local, versioned artifacts instead of chat-only or handoff-only prose.
8. Refresh first-class plans, quality grades, reliability/security notes, or tech-debt trackers when branch changes invalidate them.

## Workflow (required order)

1. Collect branch onboarding context first.
Run `branch-onboarding-brief` before editing docs and reuse its outputs.
Capture changed files, net LOC, and high-churn non-test modules from onboarding output.

2. Read map and boundary docs first.
Read `AGENTS.md`, `docs/index.md`, and `docs/_meta/docs-contract.md` before drafting edits.
If local AGENTS are active, inventory `src/**/AGENTS.md` and keep chain consistency.
If the repository keeps top-level design/plan/quality/reliability/security docs, read the relevant ones before rewriting leaf docs.

3. Choose refresh mode.
- Default: incremental refresh (delta-based) for touched areas.
- Use full refresh only if:
  - the user explicitly asks for comprehensive/full rewrite
  - symbol rename spans many docs
  - architecture shift invalidates existing doc boundaries

4. Build the documentation impact set.
Use the branch fork point as the default branch-diff boundary. The upstream base is only used to resolve that fork point; omit `--base` to let the helper detect `origin/HEAD`, then `main`/`master`.
Run:

```bash
python /Users/mrx-ksjung/.codex/skills/refresh-branch-docs/scripts/collect_doc_refresh_context.py --format md
```

Use `references/doc_update_matrix.md` to validate and expand candidate docs.
Always prioritize:
- docs already touched on branch
- docs mapped from high-churn non-test code paths
- API/spec docs that mention changed symbols
- map/contract docs (`AGENTS.md`, `docs/index.md`, `docs/_meta/docs-contract.md`) when doc navigation or boundaries changed
- design, execution-plan, quality, reliability, security, or tech-debt docs that index or grade the changed area

5. Run required evidence collection.
Delegate discovery and structural code extraction to `probe-deep-search`, then use `rg -n` for exact anchors.
Use `references/doc_refresh_localization_queries.md` only as doc-refresh-specific seed/query guidance.
Require evidence for each doc claim:
- one call-path or dependency anchor from `probe extract` plus adjacent call-site search, or from `rpg-loop-reasoning` when cross-module flow remains unclear
- one symbol/usage anchor from `rg -n`
- one test/spec anchor when available
- one repo-local artifact anchor when the claim depends on a plan, quality grade, or operating policy

6. Rewrite internal docs with evidence.
For each target doc:
- replace stale behavior descriptions
- align names/signatures with current symbols
- update data shape tables and invariants
- update constraint/objective sections when rule semantics changed
- verify evaluation/performance metric definitions from code before rewriting metric narratives
- state the metric SSOT positively and name the comparison baseline pair explicitly
- keep internal heuristic counters distinct from evaluation/performance SSOT unless the evaluator emits them
- keep root AGENTS concise and pointer-oriented when touched
- update plan/quality/reliability/security or tech-debt docs when changed behavior invalidates their status, guidance, or backlog entries
- encode durable external guidance into repository-local docs or references instead of leaving it only in the delivery brief
- Do: when a statement is no longer current or in scope, delete it outright and rewrite the surrounding doc cleanly.
- Don't Do: leave tombstone prose like "this was removed/deleted" unless the doc is explicitly a changelog, migration guide, or retirement record.

Avoid speculative text. If uncertain, mark it as unresolved and list missing evidence.

7. Validate doc consistency and mechanical guards.
Run quick drift checks:

```bash
rg -n "TODO|TBD|FIXME|\\bdeprecated\\b" docs
rg -n "<old_symbol>" docs
rg -n "<new_symbol>" docs
```

Run docs integrity gates:
- Preferred: `make docs-check` (if target exists).
- Fallback: run `scripts/check_code_paths.sh`, `scripts/check_make_targets.sh`, `scripts/check_md_links.py` directly.

Optionally run focused tests for changed behavior and report only tests that were actually executed.
If the same documentation failure keeps reappearing in review feedback or validation output, recommend promoting that rule into tooling, linters, structural tests, or reusable scripts instead of adding more prose.

8. Produce final delivery brief.
Report:
- updated docs list
- evidence links (file path + symbol)
- unresolved ambiguities
- follow-up items
- refresh mode used (incremental or full) and why
- whether upstream orchestration context (for example from `rpg-loop-reasoning`) was reused
- harness alignment status:
  - map-first AGENTS
  - SSOT boundary clarity
  - progressive disclosure integrity
  - agent legibility / repo-local artifact coverage
  - mechanical validation status
  - promote-to-tooling follow-ups (if any)
  - doc-gardening backlog (if any)

## Output Contract (chat)
- Put the documentation refresh result first.
- Include evidence list with file paths and symbols.
- Separate confirmed updates and unresolved items.
- Ask exactly one question only when blocked.

## Delegation Boundaries

- `branch-onboarding-brief` owns branch diff collection and onboarding synthesis.
- `rpg-loop-reasoning` may supply upstream dual-view localization context; this skill remains the owner of doc impact mapping, evidence gathering, doc rewrites, and doc consistency validation.

## Resources
- `scripts/collect_doc_refresh_context.py`: map branch diff to candidate docs.
- `../_shared/references/docs_harness_checklist.md`: shared harness checklist for map/SSOT/progressive-disclosure/docs-check.
- `references/doc_update_matrix.md`: code-path to doc mapping matrix.
- `references/doc_refresh_localization_queries.md`: reusable `probe`/`rg` query sets for doc refresh.
