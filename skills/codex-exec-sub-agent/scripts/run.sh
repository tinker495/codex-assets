#!/usr/bin/env bash
set -euo pipefail

runs_dir="${CODEX_SUBAGENT_RUNS_DIR:-$HOME/.codex/sub_agent_runs}"
mkdir -p "$runs_dir"

run_dir="$(mktemp -d "$runs_dir/$(date -u +%Y%m%dT%H%M%SZ)-XXXXXX")"
prompt_file="$run_dir/prompt.txt"
jsonl_file="$run_dir/run.jsonl"

if [[ $# -gt 0 ]]; then
	printf '%s\n' "$*" >"$prompt_file"
elif [[ ! -t 0 ]]; then
	cat >"$prompt_file"
else
	echo "Usage: $0 \"prompt\"  or  cat prompt.txt | $0" >&2
	exit 2
fi

codex exec --json - <"$prompt_file" | tee "$jsonl_file"
echo "$jsonl_file"
