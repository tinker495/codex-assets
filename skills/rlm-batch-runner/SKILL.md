---
name: rlm-batch-runner
description: Execute `jobs.jsonl` workloads for RLM chunk scanning with parallel Codex subagent calls, retry logic, timeout handling, and schema validation. Use when controller workflows need resilient fan-out/fan-in execution and normalized result/log artifacts under a run directory.
---

# RLM Batch Runner

Use the bundled script to dispatch chunk jobs in parallel and validate outputs.

## Script

- Path: `~/.codex/skills/rlm-batch-runner/scripts/rlm_batch.py`
- Input: `jobs.jsonl`
- Outputs:
  - `subresults/*.json`
  - `logs/*.jsonl`
  - `summary.json`

## Job Record Contract

Each JSONL line must include:

- `job_id`
- `chunk_id`
- `chunk_path`
- `question`
- `output_path`
- `schema_path`
- `sandbox` (`read-only` only)
- `timeout_sec`

## Command

```bash
python3 ~/.codex/skills/rlm-batch-runner/scripts/rlm_batch.py \
  --jobs sessions/<run_id>/jobs.jsonl \
  --run-dir sessions/<run_id> \
  --parallel 8 \
  --timeout-sec 600 \
  --retries 2
```

## Exit Codes

- `0`: all jobs succeeded
- `2`: partial success
- `3`: all jobs failed

## Behavior

- Run jobs concurrently with isolated retries per job.
- Preserve per-attempt JSONL logs under `logs/`.
- Normalize outputs before validation:
  - add missing `gaps`/`errors` as `[]`
  - add missing `evidence[].note` default text
  - clamp overlong text fields (`summary`, `evidence.loc`, `evidence.quote`, `evidence.note`) to schema limits
- Validate each output JSON against required subagent constraints.
- Continue processing when individual jobs fail; summarize failures in `summary.json`.
