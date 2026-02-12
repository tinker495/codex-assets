---
name: rlm-subagent
description: Analyze a single chunk for evidence extraction and structured scoring. Use when a controller dispatches chunk-level jobs and needs strict JSON output with citations, uncertainty capture, and no speculative claims.
---

# RLM Subagent

## Operating Rules

- Read only the chunk file path provided by the controller.
- Do not explore unrelated files or the full repository.
- Do not guess; mark uncertainty explicitly.
- Return structured JSON only.

## Required Output Shape

- Output must conform to `schemas/subagent.schema.json`.
- Required fields: `chunk_id`, `relevant`, `summary`, `confidence`, `evidence`.
- `evidence[].loc` must use `path:start-end`.
- Keep `summary` concise and factual.
- Always include `gaps` and `errors` arrays (`[]` when empty).

## Decision Rules

1. Set `relevant=false` if the chunk does not materially support the question.
2. Keep `evidence` empty when no direct support exists.
3. Use lower `confidence` when evidence is weak, ambiguous, or incomplete.
4. Put parsing/format or instruction issues in `errors`.

## Example Invocation

```bash
codex exec \
  --sandbox read-only \
  --output-schema ~/.codex/skills/rlm-subagent/schemas/subagent.schema.json \
  -o sessions/<run_id>/subresults/<job_id>.json \
  "Use $rlm-subagent. Question: ... Chunk: sessions/<run_id>/chunks/c-001.txt"
```
