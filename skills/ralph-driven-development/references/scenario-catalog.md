# Scenario Catalog

Use this file to select the right Ralph-style iteration pattern before writing `prd.json`.

## Invocation Mode

- Run in Codex skill context, not as an external orchestrator script.
- Execute one story per invocation unless user explicitly asks for multiple iterations.
- Use `brief` output as source of truth for next story selection.
- Keep repository-agnostic defaults; load specialization profiles only when they match the repo.
- Persist iteration state in repository artifacts (`prd.json`, `progress.txt`, `docs/done.md`, `docs/logs/agent-run.log`) based on active mode.

## 1) Feature Delivery

- Trigger: "Break this feature into implementable slices."
- Use when: one feature spans DB, backend, and UI.
- Story order: schema -> backend -> UI -> polish.
- Evidence: tests/typecheck and UI verification where applicable.

## 2) Refactor with Safety Rails

- Trigger: "Refactor this module without breaking behavior."
- Use when: internals change but external contracts should stay stable.
- Story style: one structural move per story (extract, rename, isolate dependency).
- Evidence: regression tests for each story.

## 3) Bug Batch Stabilization

- Trigger: "Handle these N bugs in priority order."
- Use when: multiple defects are known and severity is mixed.
- Story style: one reproducible bug per story.
- Evidence: failing test first, then passing test.

## 4) Performance Iterations

- Trigger: "Improve runtime/memory step by step."
- Use when: algorithmic hot paths need measured optimization.
- Story style: baseline -> targeted change -> measurement.
- Evidence: benchmark delta and no regression in correctness tests.

## 5) Pre-PR Hardening

- Trigger: "Get this branch ready for review."
- Use when: feature is mostly done but quality and consistency remain.
- Story style: focused quality slices (typing, lint, flaky tests, docs).
- Evidence: full project checks green and clear progress ledger.

## Anti-Patterns

- Avoid one-story mega tasks ("build full dashboard", "refactor entire API").
- Avoid ambiguous criteria ("works well", "better UX").
- Avoid passing stories with unresolved blockers.

## Trigger Phrases

- "Run Ralph loop on this backlog"
- "Process prd.json one story at a time"
- "Pick next pending story and execute"
- "Continue from progress.txt"
- "반복 실행해"
- "다음 반복 진행"
- "스토리 하나씩 반복 처리"
- "반복 루프 계속"
