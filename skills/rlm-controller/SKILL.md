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
- Keep worker prompts stable at the prefix and append chunk payloads at the end.

## Operational Noise Guardrails
- Use search-as-discovery and path preflight before direct reads: `rg --files`/`rg -n` -> `test -f`/`test -d` -> execute.
- Before git fallback commands, verify repo context with `git rev-parse --is-inside-work-tree`.
- If `timeout` is unavailable, rerun without timeout wrapper (or use `gtimeout`).
- If `jq` is unavailable or parsing fails (`jq: parse error`), rerun without `jq` and parse plain text.
- Retry identical failing commands at most once, then switch to fallback mode.

## Delegation Contract

- Delegate chunk execution and retry orchestration to `$rlm-batch-runner`.
- Handoff only reduced evidence and unresolved gaps back to controller reduce logic.

## Token Budget Baseline (Required)

Before large runs, sample one worker call and inspect `turn.completed.usage`.

```bash
codex exec --json "noop" \
  | jq -r 'select(.type=="turn.completed") | .usage'
```

If `jq` is unavailable or fails, use plain-text fallback:

```bash
codex exec --json "noop"
```

Interpretation:

- `output_tokens` high but final text short: reasoning token overhead is dominant.
- `input_tokens` high and similar across calls: repeated fixed prefix/context is dominant.
- `cached_input_tokens` high: caching is active; it reduces cost/latency, not token count.

## Worker Isolation Profile (Required)

Run workers with an isolated `CODEX_HOME` and a dedicated profile to minimize repeated
project instructions.

```toml
# /tmp/codex_worker_home/config.toml
[profiles.rlm-worker]
model = "gpt-5.3-codex-spark"
model_reasoning_effort = "minimal"
model_reasoning_summary = "none"
model_verbosity = "low"
web_search = "disabled"
tool_output_token_limit = 1500
project_doc_max_bytes = 0
project_root_markers = []
history.persistence = "none"
hide_agent_reasoning = true
```

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
4. Prefilter chunks in Python (regex/BM25/vector) and keep only top-k evidence candidates.
5. Build `jobs.jsonl` with one job per chunk or targeted chunk-group.
6. Pack multiple short chunks per job when possible to amortize fixed prompt overhead.
7. Run batch execution via:
   - `python3 ~/.codex/skills/rlm-batch-runner/scripts/rlm_batch.py --jobs <jobs.jsonl> --run-dir <session_dir>`
8. Reduce results: merge evidence, resolve conflicts, and list unresolved gaps.
9. If gaps remain, run targeted follow-up jobs (max 2 additional passes).
10. Emit `out/answer.json` conforming to `schemas/final.schema.json`.

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
  --model gpt-5.3-codex-spark \
  --sandbox workspace-write \
  --output-schema ~/.codex/skills/rlm-controller/schemas/final.schema.json \
  -o out/answer.json \
  "Use $rlm-controller. Task file: tasks/TASK.md. Input root: inputs/."
```

## Cost-Optimized Worker Invocation

Use the batch runner with isolated worker context and git-repo check disabled for chunk jobs.

```bash
python3 ~/.codex/skills/rlm-batch-runner/scripts/rlm_batch.py \
  --jobs sessions/<run_id>/jobs.jsonl \
  --run-dir sessions/<run_id> \
  --model gpt-5.3-codex-spark \
  --profile rlm-worker \
  --codex-home /tmp/codex_worker_home \
  --worker-cwd /tmp/rlm_worker \
  --skip-git-repo-check \
  --parallel 8 \
  --timeout-sec 600 \
  --retries 2
```
