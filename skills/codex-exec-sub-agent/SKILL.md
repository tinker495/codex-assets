---
name: codex-exec-sub-agent
description: Delegate a task to a separate Codex process by running `codex exec --json` and logging the full JSONL event stream to a timestamped folder under `~/.codex/sub_agent_runs/`. Use when you want a lightweight "sub-agent" workflow where the main agent provides only a prompt, and the runner script handles run folders, prompt capture, and printing the JSONL path.
---

# Run a sub-agent (Codex exec) and capture JSONL

Use the bundled runner script to avoid manually picking filenames/paths for the JSONL log.

## Runner

- Script: `~/.codex/skills/codex-exec-sub-agent/scripts/run.sh`
- Default runs dir: `~/.codex/sub_agent_runs/` (override with `CODEX_SUBAGENT_RUNS_DIR`)
- Print: the full path to `run.jsonl` as the last line on stdout
- Options:
  - `--prompt-file <path>`: read prompt from file (recommended for long/complex prompts)
  - `--timeout-sec <n>`: hard timeout in seconds (returns exit code `124` on timeout)

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
