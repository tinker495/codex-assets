---
name: refresh-branch-docs
description: Refresh repository-internal documentation end-to-end based on current branch changes. Use when asked to comprehensively update docs after refactors or feature work, especially when updates must be grounded in branch diff evidence, branch onboarding context, and grepai deep analysis.
---

# Refresh Branch Docs

## Overview
Refresh internal docs so they match current branch behavior instead of stale assumptions. Default to incremental delta refresh, and use full refresh only when explicitly requested or when drift is widespread. Collect evidence first, then rewrite docs with explicit source anchors.

```mermaid
flowchart LR
  A["Branch Onboarding"] --> B["Impact Mapping"]
  B --> C["Grepai Deep Analysis"]
  C --> D["Doc Rewrite"]
  D --> E["Validation and Brief"]
```

## Workflow

1. Collect branch onboarding context first.
Run `branch-onboarding-brief` before editing docs and reuse its outputs.
Capture changed files, net LOC, and high-churn non-test modules from onboarding output.

2. Choose refresh mode.
- Default: incremental refresh (delta-based) for touched areas.
- Use full refresh only if:
  - the user explicitly asks for comprehensive/full rewrite
  - symbol rename spans many docs
  - architecture shift invalidates existing doc boundaries

3. Build the documentation impact set.
Run:

```bash
python /Users/mrx-ksjung/.codex/skills/refresh-branch-docs/scripts/collect_doc_refresh_context.py --base main --format md
```

Use `references/doc_update_matrix.md` to validate and expand candidate docs.
Always prioritize:
- docs already touched on branch
- docs mapped from high-churn non-test code paths
- API/spec docs that mention changed symbols

4. Run required deep analysis.
Delegate protocol execution to `grepai-deep-analysis`.
Use `references/grepai_doc_refresh_queries.md` only as doc-refresh-specific seed/query guidance.
Require evidence for each doc claim:
- one call-path anchor from `grepai trace`
- one symbol/usage anchor from `rg -n`
- one test/spec anchor when available

5. Rewrite internal docs with evidence.
For each target doc:
- replace stale behavior descriptions
- align names/signatures with current symbols
- update data shape tables and invariants
- update constraint/objective sections when rule semantics changed

Avoid speculative text. If uncertain, mark it as unresolved and list missing evidence.

6. Validate doc consistency.
Run quick checks:

```bash
rg -n "TODO|TBD|FIXME|\\bdeprecated\\b" docs
rg -n "<old_symbol>" docs
rg -n "<new_symbol>" docs
```

Optionally run focused tests for changed behavior and report only tests that were actually executed.

7. Produce final delivery brief.
Report:
- updated docs list
- evidence links (file path + symbol)
- unresolved ambiguities
- follow-up items
- refresh mode used (incremental or full) and why
- whether upstream orchestration context (for example from `rpg-loop-reasoning`) was reused

## Output Contract (chat)
- Put the documentation refresh result first.
- Include an ASCII process map:

```text
[Onboard] -> [Map Docs] -> [Deep Analyze] -> [Rewrite] -> [Validate]
```

- Include evidence list with file paths and symbols.
- Separate confirmed updates and unresolved items.
- Ask exactly one question only when blocked.

## Delegation Boundaries

- `branch-onboarding-brief` owns branch diff collection and onboarding synthesis.
- `grepai-deep-analysis` owns noise control, pass sequencing, and evidence-gating protocol.
- `rpg-loop-reasoning` may supply upstream dual-view localization context; this skill remains the owner of doc impact mapping, doc rewrites, and doc consistency validation.

## Resources
- `scripts/collect_doc_refresh_context.py`: map branch diff to candidate docs.
- `references/doc_update_matrix.md`: code-path to doc mapping matrix.
- `references/grepai_doc_refresh_queries.md`: reusable grepai query sets for doc refresh.
