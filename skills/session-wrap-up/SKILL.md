---
name: session-wrap-up
description: Close an active coding session by distilling reusable insights, summarizing deferred TODO and follow-up status, reviewing even small usage mistakes or recoverable hiccups for reusable guardrail gaps, deciding whether to keep/update/create/retire skill assets, and delegating concrete skill maintenance work while preserving clean orchestration boundaries. Use when asked to do session wrap-up/retrospective, convert lessons learned into new or updated skills, capture session-end TODO status, decide whether a session implies no-op skill follow-up, or adjust delegation topology across skills.
---

# Session Wrap Up

## Overview

Run a deterministic session-closing flow that turns session outcomes into reusable skill actions. Own synthesis and prioritization. Prefer strengthening installed skills over creating new ones. Delegate skill implementation mechanics to `skill-creator`, use `todo-inventory` when deferred-work evidence matters, and keep topology edits conditional. Do not ignore small but repeatable usage mistakes, validation slips, aborted turns, or recoverable tool hiccups when they reveal a missing guardrail.

```mermaid
flowchart LR
  A["Collect Session Evidence"] --> T["Inventory TODO Status (Optional)"]
  T --> B["Extract Reusable Insights"]
  B --> C["Choose Action: None/Update/Create/Retire"]
  C --> D["Delegate Build Work to skill-creator"]
  D --> E["Update Topology (if edges changed)"]
  E --> F["Publish Session Wrap-Up Report"]
```

## Workflow

1. Collect session evidence.
Capture goals, delivered outputs, repeated friction, failed attempts, small usage mistakes, recoverable hiccups, and proven fixes from the current session.
Prefer concrete artifacts in this order:
- current task/result summary
- changed file paths, command traces, and validation output
- user correction points or repeated prompt steering
- aborted turns, command misuse, validation-format mistakes, or quick recoveries that still exposed a missing guardrail
- local session artifacts (`.omx/notepad.md`, `.omx/state`, draft reports) when present
Do not invent history and do not assume a missing recall skill exists.
When deferred follow-up visibility matters, call `todo-inventory` to capture:
- remaining TODO markers in the relevant repo or module
- TODO markers newly added in the current diff
- skipped files and diff-availability caveats

2. Extract reusable insights.
Classify each candidate into one of:
- trigger gap
- workflow gap
- ownership/delegation boundary gap
- reusable resource gap (script/reference/template)
Treat small but repeatable operator mistakes or tool-usage slips as `workflow gap` candidates when a guardrail, clearer instruction, validator, or helper script would have prevented them.
Drop one-off observations that are unlikely to recur.

3. Decide action type per insight.
Choose `none` when value is non-reusable.
Choose `update-existing-skill` when ownership already exists or when an installed skill is the obvious home.
Choose `create-new-skill` only when repeated value + clear ownership boundary + no installed owner are all true.
Choose retirement/removal guidance only when the asset is superseded or harmful; otherwise keep scope to additive updates.
Do not dismiss a small failure just because recovery was easy; if it exposed a reusable missing guardrail, prefer `update-existing-skill`.
If every candidate resolves to `none`, publish a no-op wrap-up and stop after reporting.

4. Delegate implementation to `skill-creator`.
Provide a compact handoff packet:
- proposed English skill name (hyphen-case, under 64 chars)
- target path (`$CODEX_HOME/skills/<skill-name>`)
- action (`update-existing-skill`, `create-new-skill`, `retire-skill`, or `none`)
- problem statement and reusable evidence
- frontmatter description delta (what to trigger on, what to stop claiming)
- role (`specialist`, `orchestrator`, `utility`, or `meta`)
- ownership statement
- delegation edges (one-hop only)
- required resources (`scripts/`, `references/`, `assets/`)
- interface check (`agents/openai.yaml` refresh needed or not)
- validation scope (`quick_validate.py` + topology consistency when role/edges changed)
- TODO status note (new TODOs added, remaining scoped TODOs, and follow-up reported without inline TODOs)

5. Adjust skill orchestration topology.
Only involve `skill-topology-adjuster` when role map, ownership, or delegation edges changed.
If topology changed, update:
- `skill-topology-adjuster/references/skill_topology.md` role map
- delegation graph
- delegation tree
Reject designs that duplicate specialist internals instead of delegating.
Do not reference non-installed skills in boundaries or handoff notes.

6. Publish a session wrap-up report.
Follow the output contract below and keep recommendations executable in the next session.

7. Emit sync-mode and retirement guidance when asset removal is involved.
If proposed actions remove/retire/rename skill folders or files, include:
- retirement path move first (`~/.codex/skills/<name>` -> `~/.codex/archived-skills/<name>`)
- mirror sync mode requirement (`./scripts/sync_and_push.sh --mirror ...`) so deletions are reflected in mirror/GitHub
- non-removal changes may use default merge sync

Optional (heavy evidence scans): delegate bounded background analysis to `codex-exec-sub-agent` using quoting-safe invocation.

```bash
~/.codex/skills/codex-exec-sub-agent/scripts/run.sh --timeout-sec 600 --prompt-file /full/path/prompt.txt
```

Prefer workspace paths or `~/.codex/sub_agent_runs` for sub-agent output targets; avoid `/tmp`/`/var/tmp` paths when sandbox policies may block writes.

## Decision Rules

- Bias toward `update-existing-skill` over `create-new-skill`.
- Bias toward treating small repeatable usage mistakes as guardrail gaps, not as noise.
- Keep delegation to installed skills only; if the owner is missing, either handle evidence locally or create a bounded proposal to add the owner.
- Allow `none` as a valid final action when the session produced no reusable pattern.
- Keep retirement guidance explicit and reversible; never recommend direct deletion from the mirror repo.
- Keep handoff packets small enough that `skill-creator` can act without re-deriving the session narrative.

## Output Contract (chat)

Default output language: Korean.
Use Korean for section titles, summaries, TODO notes, insight descriptions, delegation notes, and handoff text unless the user explicitly requests another language.
Keep literal workflow/action tokens such as `none`, `update-existing-skill`, `create-new-skill`, `retire-skill`, `merge`, `mirror`, and `no-op wrap-up` in backticks unless the user explicitly asks to localize them.

Use the exact section order below.
Do not merge sections.
If a section has no content, still emit the heading and write `없음`.

Always return, in order:
1. `## 1. 세션 결과 요약`
   - Session result summary (answer-first, 3-5 lines).
   - Mention small-but-reusable usage mistakes or minor hiccups when they influenced the session outcome.
2. `## 2. TODO 상태 요약`
   - TODO status summary:
   - TODOs newly added in the current diff
   - remaining TODOs in scope
   - follow-up items reported without inline TODO markers, if any
3. `## 3. 사소한 장애/사용 미스 검토`
   - List small usage mistakes, aborted turns, validator slips, command misuse, or recoverable hiccups that mattered.
   - For each item, say:
     - what happened
     - why it matters
     - whether it is `one-off` or a reusable `guardrail gap`
   - If none, write `없음`.
4. `## 4. 재사용 가능한 인사이트`
   - Reusable insights list with action type (`none`, `update-existing-skill`, `create-new-skill`, `retire-skill`).
5. `## 5. 위임 계획`
   - Delegation plan (`orchestrator -> specialist`) for each action.
6. `## 6. 토폴로지 변경 요약`
   - Topology delta summary (if no change, say exactly `no topology change`).
7. `## 7. 즉시 다음 작업`
   - Immediate next command/task for handoff (include sync mode: `merge` or `mirror`).
If every action is `none`, still emit all sections, include TODO status and the small-incident review section, and explicitly say `no-op wrap-up`.

## Delegation Boundaries

- `session-wrap-up` owns end-of-session synthesis, prioritization, and orchestration decisions.
- `skill-creator` owns skill initialization/editing/validation procedures.
- `todo-inventory` owns TODO inventory and diff-added TODO evidence gathering.
- `omx-workspace-prune` owns safe `.omx` cleanup and retention policy when wrap-up includes workspace pruning or retirement follow-through.
- Historical session retrieval defaults to direct inspection of available local artifacts and current thread context.
- `codex-exec-sub-agent` is optional execution utility for long-running or fresh-context scans; keep delegation one-hop and bounded by timeout.
- This skill must not duplicate `skill-creator` internals; delegate instead.

## Naming Rules

- Convert Korean task labels to concise English action names.
- Prefer `verb-noun` or `noun-action` hyphen-case names.
- Default translation for this workflow:
  - Korean label: "세션 갈무리"
  - English skill name: `session-wrap-up`

## Reference

- `references/session_wrap_up_checklist.md`
