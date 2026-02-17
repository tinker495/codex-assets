---
name: rlm-batch-runner
description: Execute `jobs.jsonl` workloads for RLM chunk scanning with parallel Codex subagent calls, retry logic, timeout handling, and schema validation. Use when controller workflows need resilient fan-out/fan-in execution and normalized result/log artifacts under a run directory.
---

# RLM Batch Runner

Use the bundled script to dispatch chunk jobs in parallel and validate outputs.

## Operational Noise Guardrails
- Run discovery before direct path reads: `rg --files`/`rg -n` -> `test -f`/`test -d` -> command execution.
- Avoid here-doc syntax (`<<EOF`) in this workflow; use `python -c` or single-line commands for fixture creation.
- If `timeout` is unavailable, rerun without timeout wrapper (or use `gtimeout` when available).
- If `jq` parsing fails (`jq: parse error`), rerun without JSON parser dependency and continue in plain-text mode.
- Retry identical failing commands at most once before fallback.

## Delegation Boundary

- This utility executes fan-out batches and writes normalized artifacts.
- Delegate chunk-level reasoning to `$rlm-subagent` workers via the runner script.

## Script

- Path: `~/.codex/skills/rlm-batch-runner/scripts/rlm_batch.py`
- Input: `jobs.jsonl`
- Outputs:
  - `subresults/*.json`
  - `logs/*.jsonl`
  - `summary.json` (includes token usage totals)

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

Optional per-run controls are passed as CLI flags, not job fields.

## Command

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

## Token Controls

- Prefer `--model gpt-5.3-codex-spark` as the default subagent model.
- Use `--profile rlm-worker` for low reasoning effort worker config.
- Use `--codex-home` to isolate worker state and avoid loading unrelated AGENTS chains.
- Use `--worker-cwd` + `--skip-git-repo-check` to run workers outside repository context.
- Keep prompts deterministic: static instructions first, chunk payload last.

## Model Regression Checks

Use these commands to verify `--model` handling in `rlm_batch.py`.

### 1) Empty model must fail fast

```bash
mkdir -p .codex_tmp/rlm-regression
: > .codex_tmp/rlm-regression/jobs.empty.jsonl
python3 ~/.codex/skills/rlm-batch-runner/scripts/rlm_batch.py \
  --jobs .codex_tmp/rlm-regression/jobs.empty.jsonl \
  --run-dir .codex_tmp/rlm-regression/run-empty-model \
  --model ""
```

Expected: exit non-zero with `--model must be a non-empty string`.

### 2) Explicit model must be forwarded to runner

```bash
mkdir -p .codex_tmp/rlm-regression
python3 -c "import json,pathlib; p=pathlib.Path('.codex_tmp/rlm-regression'); p.mkdir(parents=True, exist_ok=True); (p/'chunk.txt').write_text('chunk\\n', encoding='utf-8'); (p/'schema.json').write_text('{}\\n', encoding='utf-8'); job={'job_id':'j-001','chunk_id':'c-001','chunk_path':str(p/'chunk.txt'),'question':'q','output_path':'subresults/j-001.json','schema_path':str(p/'schema.json'),'sandbox':'read-only','timeout_sec':30}; (p/'jobs.one.jsonl').write_text(json.dumps(job)+'\\n', encoding='utf-8')"
python3 -c "import pathlib; p=pathlib.Path('.codex_tmp/rlm-regression'); script='#!/usr/bin/env bash\\nset -euo pipefail\\nexpected=\"gpt-5.3-codex-spark\"\\nmodel=\"\"\\nwhile [[ $# -gt 0 ]]; do\\n  case \"$1\" in\\n    --model) model=\"$2\"; shift 2 ;;\n    --timeout-sec|--prompt-file) shift 2 ;;\n    *) shift ;;\n  esac\\ndone\\nif [[ \"$model\" != \"$expected\" ]]; then\\n  echo \"unexpected model: $model\" >&2\\n  exit 13\\nfi\\nrun_dir=\"$(mktemp -d)\"\\njsonl=\"$run_dir/run.jsonl\"\\nprintf %s \"{\\\"item\\\":{\\\"type\\\":\\\"agent_message\\\",\\\"text\\\":\\\"{\\\\\\\"chunk_id\\\\\\\":\\\\\\\"c-001\\\\\\\",\\\\\\\"relevant\\\\\\\":true,\\\\\\\"summary\\\\\\\":\\\\\\\"ok\\\\\\\",\\\\\\\"confidence\\\\\\\":0.7,\\\\\\\"evidence\\\\\\\":[{\\\\\\\"loc\\\\\\\":\\\\\\\"x.md:1-1\\\\\\\",\\\\\\\"quote\\\\\\\":\\\\\\\"q\\\\\\\",\\\\\\\"note\\\\\\\":\\\\\\\"n\\\\\\\"}],\\\\\\\"gaps\\\\\\\":[],\\\\\\\"errors\\\\\\\":[]}\\\"}}\" > \"$jsonl\"\\nprintf \"\\n\" >> \"$jsonl\"\\necho \"$jsonl\"\\n'; (p/'mock-runner.sh').write_text(script, encoding='utf-8')"
chmod +x .codex_tmp/rlm-regression/mock-runner.sh
python3 ~/.codex/skills/rlm-batch-runner/scripts/rlm_batch.py \
  --jobs .codex_tmp/rlm-regression/jobs.one.jsonl \
  --run-dir .codex_tmp/rlm-regression/run-model-forward \
  --runner-script .codex_tmp/rlm-regression/mock-runner.sh \
  --model gpt-5.3-codex-spark \
  --parallel 1 \
  --retries 0
```

Expected: exit `0` and `jobs_succeeded=1`.

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
- Extract per-job `turn.completed.usage` from JSONL and aggregate:
  - `input_tokens`
  - `cached_input_tokens`
  - `output_tokens`
