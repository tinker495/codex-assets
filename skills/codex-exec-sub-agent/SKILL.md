---
name: codex-exec-sub-agent
description: Delegate a task to a separate Codex process by running `codex exec --json` and logging the full JSONL event stream to a timestamped folder under `~/.codex/sub_agent_runs/`. Use when you want a lightweight "sub-agent" workflow where the main agent provides only a prompt, and the runner script handles run folders, prompt capture, and printing the JSONL path.
---

# Run a sub-agent (Codex exec) and capture JSONL

Use the bundled runner script to avoid manually picking filenames/paths for the JSONL log.

## Runner

- Script: `~/.codex/skills/codex-exec-sub-agent/scripts/run.sh`
- Default runs dir: `~/.codex/sub_agent_runs/` (override with `CODEX_SUBAGENT_RUNS_DIR`)
- Default model: `gpt-5.3-codex-spark` (override with `CODEX_SUBAGENT_MODEL`)
- Print: the full path to `run.jsonl` as the last line on stdout
- Options:
  - `--prompt-file <path>`: read prompt from file (recommended for long/complex prompts)
  - `--timeout-sec <n>`: hard timeout in seconds (returns exit code `124` on timeout)
  - `--model <id>`: override model per run
  - `--profile <name>`: apply Codex profile (for worker-specific low-token config)
  - `--cd <dir>`: run `codex exec` from a specific directory
  - `--skip-git-repo-check`: bypass git repo requirement (useful for temp worker dirs)
  - `--codex-home <dir>`: run with isolated `CODEX_HOME`

## How to call

Important: when asking a main agent to run this, set that main agent timeout to at least about 10 minutes. Otherwise the parent can time out while nested `codex exec` is still running.

Pass the prompt via stdin (recommended for long prompts):

```bash
cat prompt.txt | ~/.codex/skills/codex-exec-sub-agent/scripts/run.sh
```

Pass prompt file path explicitly (best for shell-quoting safety):

```bash
~/.codex/skills/codex-exec-sub-agent/scripts/run.sh --prompt-file /full/path/prompt.txt
```

Or pass it as an argument (fine for short prompts):

```bash
~/.codex/skills/codex-exec-sub-agent/scripts/run.sh "Do X, then write results to /full/path/output.md"
```

Apply timeout when you want deterministic failure instead of hanging:

```bash
~/.codex/skills/codex-exec-sub-agent/scripts/run.sh --timeout-sec 600 --prompt-file /full/path/prompt.txt
```

Override model only when needed:

```bash
~/.codex/skills/codex-exec-sub-agent/scripts/run.sh --model gpt-5.3-codex-spark --prompt-file /full/path/prompt.txt
```

Apply worker profile and isolated context for token efficiency:

```bash
~/.codex/skills/codex-exec-sub-agent/scripts/run.sh \
  --model gpt-5.3-codex-spark \
  --profile rlm-worker \
  --codex-home /tmp/codex_worker_home \
  --cd /tmp/rlm_worker \
  --skip-git-repo-check \
  --prompt-file /full/path/prompt.txt
```

## Model Smoke Tests

Run these checks after changing runner options or model policy.

```bash
mkdir -p .codex_tmp/subagent-smoke
printf '%s\n' "Reply exactly: OK" > .codex_tmp/subagent-smoke/prompt.txt

# 1) Default model path (no --model, no CODEX_SUBAGENT_MODEL)
env -u CODEX_SUBAGENT_MODEL \
  ~/.codex/skills/codex-exec-sub-agent/scripts/run.sh \
  --timeout-sec 90 \
  --prompt-file "$PWD/.codex_tmp/subagent-smoke/prompt.txt"

# 2) Explicit override path
~/.codex/skills/codex-exec-sub-agent/scripts/run.sh \
  --model gpt-5.3-codex-spark \
  --timeout-sec 90 \
  --prompt-file "$PWD/.codex_tmp/subagent-smoke/prompt.txt"
```

Expected: both commands exit `0` and print a `run.jsonl` path as the last line.

## Shell-Safe Skill Invocation

When your prompt text includes a skill token like `$rlm-controller`, do not pass it unescaped in a double-quoted shell string. Otherwise shell expansion can remove the token.

Use one of these safe patterns:

```bash
# Preferred: prompt file
printf '%s\n' "Use \$rlm-controller. Reduce-only mode." > /tmp/prompt.txt
~/.codex/skills/codex-exec-sub-agent/scripts/run.sh --prompt-file /tmp/prompt.txt

# Or escape $ in inline strings
~/.codex/skills/codex-exec-sub-agent/scripts/run.sh "Use \$rlm-controller. Reduce-only mode."
```

## Operational Noise Controls

- Search-as-discovery first: inspect `run.jsonl` for `error`, `failed`, and `unknown flag` before opening broad logs.
- Apply path filtering: restrict `rg` to the current run directory (`~/.codex/sub_agent_runs/<timestamp>/`) before wider search.
- Use trace-plus-rg evidence gating: only widen scan scope when concrete error lines exist in `run.jsonl`.
- If Codex rejects `--json` (`Error: unknown flag: --json`), rerun once without `--json` and keep appending to the same `run.jsonl`.
- Avoid here-doc shell syntax for prompt creation and helper commands; use `printf`, `python -c`, or `--prompt-file`.

## How to write the prompt

Treat the sub-agent prompt as a mini-brief:

- Be explicit about the outcome: define what done looks like.
- Limit scope: include what to do and what to ignore.
- Set output rules: format, length, tone, and structure.
- Prefer deterministic artifacts: if you want file edits, specify full paths.
- Avoid shell-fragile inline quoting for multi-line prompts; use `--prompt-file` or stdin.

## Notes

- Prefer full paths for files the sub-agent should create or update.
- Avoid `/tmp`/`/var/tmp` output paths when sandbox policies may block writes; prefer workspace paths or `~/.codex/sub_agent_runs`.
- Use the JSONL log for inspection/debugging; treat file outputs requested in the prompt as the real deliverable.
- The runner always prints the JSONL path last, even on failures/timeouts, so callers can inspect logs reliably.

## Write-Failure Fallback (Required)

If a sub-agent is asked to write a report/artifact file and write fails (`read-only file system`, `operation not permitted`, `permission denied`), do not drop the result.

Required fallback behavior:

1. Emit the full report inline in the final response.
2. Include the intended output path and the concrete write error.
3. Include completion status plus key evidence (commands/checks run).
4. Preserve and return the JSONL path as the authoritative execution trace.

Callers should treat this inline report as a valid fallback deliverable when file writes are blocked.
