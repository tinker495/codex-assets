---
name: rlm-controller
description: Orchestrate large-context tasks with chunk-and-reduce execution using Codex subagents. Use when input is too large for a single prompt (long documents, multi-file evidence synthesis, or dataset-backed Q&A) and the workflow needs sessionized chunk planning, parallel subagent scans, and evidence-grounded final JSON output.
---

# RLM Controller

## Operating Rules

- Keep large inputs on disk; pass file paths, not raw payloads.
- Use `sessions/<run_id>/` as the working root for each run.
- Use `$rlm-batch-runner` for all chunk-level execution.
- Ingest only subagent JSON outputs and short summaries into context.
- Enforce evidence-first outputs: unresolved claims must become `gaps` entries.

## Session Layout

```text
sessions/<run_id>/
  inputs/
  chunks/
  jobs.jsonl
  subresults/
  logs/
  reduce/
out/
  answer.json
```

## Procedure

1. Generate `run_id` and create the session tree.
2. Normalize inputs into chunk files under `chunks/` and create a chunk manifest.
3. Convert task goals into explicit evidence questions.
4. Build `jobs.jsonl` with one job per chunk or targeted chunk-group.
5. Run batch execution via:
   - `python3 ~/.codex/skills/rlm-batch-runner/scripts/rlm_batch.py --jobs <jobs.jsonl> --run-dir <session_dir>`
6. Reduce results: merge evidence, resolve conflicts, and list unresolved gaps.
7. If gaps remain, run targeted follow-up jobs (max 2 additional passes).
8. Emit `out/answer.json` conforming to `schemas/final.schema.json`.

## Output Policy

- Every key claim must map to at least one citation source.
- If citation support is missing, add a concrete item in `gaps` instead of inventing support.
- Keep `confidence` calibrated to evidence completeness.
- Always include `artifacts` in the final JSON (`[]` when none).

## Final Validation Gate (Required)

Run a final contract check before reporting completion.

- If `citations` is empty, `gaps` must contain at least one concrete reason.
- If `content` claims citation coverage but `citations` is empty, treat it as failed reduce output and regenerate.
- Do not return a success summary until `out/answer.json` passes these checks.

```bash
jq -e '
  (.citations | type == "array") and
  (.gaps | type == "array") and
  ((.citations | length) > 0 or (.gaps | length) > 0)
' out/answer.json
```

## Standard Invocation

```bash
codex exec \
  --sandbox workspace-write \
  --output-schema ~/.codex/skills/rlm-controller/schemas/final.schema.json \
  -o out/answer.json \
  "Use $rlm-controller. Task file: tasks/TASK.md. Input root: inputs/."
```
