#!/usr/bin/env bash
set -euo pipefail

usage() {
	echo "Usage:"
	echo "  $0 [--prompt-file PATH] [--timeout-sec N] [--model MODEL] [--profile NAME] [--cd DIR] [--skip-git-repo-check] [--codex-home DIR] [\"prompt\"]"
	echo "  cat prompt.txt | $0 [--timeout-sec N] [--model MODEL] [--profile NAME] [--cd DIR] [--skip-git-repo-check] [--codex-home DIR]"
}

runs_dir="${CODEX_SUBAGENT_RUNS_DIR:-$HOME/.codex/sub_agent_runs}"
mkdir -p "$runs_dir"

run_dir="$(mktemp -d "$runs_dir/$(date -u +%Y%m%dT%H%M%SZ)-XXXXXX")"
prompt_file="$run_dir/prompt.txt"
jsonl_file="$run_dir/run.jsonl"
timeout_sec=""
prompt_file_input=""
prompt_text=""
model="${CODEX_SUBAGENT_MODEL:-gpt-5.3-codex-spark}"
profile="${CODEX_SUBAGENT_PROFILE:-}"
worker_cwd=""
skip_git_repo_check=0
codex_home_override=""

while [[ $# -gt 0 ]]; do
	case "$1" in
	--prompt-file|-f)
		if [[ $# -lt 2 ]]; then
			echo "Missing value for $1" >&2
			usage >&2
			exit 2
		fi
		prompt_file_input="$2"
		shift 2
		;;
	--timeout-sec|-t)
		if [[ $# -lt 2 ]]; then
			echo "Missing value for $1" >&2
			usage >&2
			exit 2
		fi
		timeout_sec="$2"
		if ! [[ "$timeout_sec" =~ ^[0-9]+$ ]]; then
			echo "--timeout-sec must be a non-negative integer" >&2
			exit 2
		fi
		shift 2
		;;
	--model|-m)
		if [[ $# -lt 2 ]]; then
			echo "Missing value for $1" >&2
			usage >&2
			exit 2
		fi
		model="$2"
		if [[ -z "$model" ]]; then
			echo "--model must be non-empty" >&2
			exit 2
		fi
		shift 2
		;;
	--profile|-p)
		if [[ $# -lt 2 ]]; then
			echo "Missing value for $1" >&2
			usage >&2
			exit 2
		fi
		profile="$2"
		if [[ -z "$profile" ]]; then
			echo "--profile must be non-empty" >&2
			exit 2
		fi
		shift 2
		;;
	--cd)
		if [[ $# -lt 2 ]]; then
			echo "Missing value for $1" >&2
			usage >&2
			exit 2
		fi
		worker_cwd="$2"
		if [[ ! -d "$worker_cwd" ]]; then
			echo "--cd must be an existing directory: $worker_cwd" >&2
			exit 2
		fi
		shift 2
		;;
	--skip-git-repo-check)
		skip_git_repo_check=1
		shift
		;;
	--no-skip-git-repo-check)
		skip_git_repo_check=0
		shift
		;;
	--codex-home)
		if [[ $# -lt 2 ]]; then
			echo "Missing value for $1" >&2
			usage >&2
			exit 2
		fi
		codex_home_override="$2"
		mkdir -p "$codex_home_override"
		shift 2
		;;
	--help|-h)
		usage
		exit 0
		;;
	--)
		shift
		prompt_text="$*"
		break
		;;
	*)
		if [[ -n "$prompt_text" ]]; then
			prompt_text="$prompt_text $1"
		else
			prompt_text="$1"
		fi
		shift
		;;
	esac
done

if [[ -n "$prompt_file_input" && -n "$prompt_text" ]]; then
	echo "Use either --prompt-file or a prompt argument, not both." >&2
	exit 2
fi

if [[ -n "$prompt_file_input" ]]; then
	if [[ ! -f "$prompt_file_input" ]]; then
		echo "Prompt file not found: $prompt_file_input" >&2
		exit 2
	fi
	cat "$prompt_file_input" >"$prompt_file"
elif [[ -n "$prompt_text" ]]; then
	printf '%s\n' "$prompt_text" >"$prompt_file"
elif [[ ! -t 0 ]]; then
	cat >"$prompt_file"
else
	usage >&2
	exit 2
fi

if grep -Eq '(^|[^[:alnum:]_])(/tmp/|/var/tmp/)' "$prompt_file"; then
	echo "Warning: prompt references /tmp paths; sandbox may block writes there. Prefer workspace or $runs_dir." >&2
fi

build_codex_cmd() {
	local -n _cmd_ref=$1
	_cmd_ref=(codex exec --json --model "$model")
	if [[ -n "$profile" ]]; then
		_cmd_ref+=(--profile "$profile")
	fi
	if [[ -n "$worker_cwd" ]]; then
		_cmd_ref+=(--cd "$worker_cwd")
	fi
	if [[ "$skip_git_repo_check" -eq 1 ]]; then
		_cmd_ref+=(--skip-git-repo-check)
	fi
	_cmd_ref+=(-)
}

set +e
if [[ -n "$timeout_sec" && "$timeout_sec" -gt 0 ]]; then
	python3 - "$timeout_sec" "$prompt_file" "$jsonl_file" "$model" "$profile" "$worker_cwd" "$skip_git_repo_check" "$codex_home_override" <<'PY'
import os
import subprocess
import sys
import time

timeout_sec = int(sys.argv[1])
prompt_path = sys.argv[2]
jsonl_path = sys.argv[3]
model = sys.argv[4]
profile = sys.argv[5]
worker_cwd = sys.argv[6]
skip_git_repo_check = sys.argv[7] == "1"
codex_home_override = sys.argv[8]
start = time.monotonic()

cmd = ["codex", "exec", "--json", "--model", model]
if profile:
    cmd.extend(["--profile", profile])
if worker_cwd:
    cmd.extend(["--cd", worker_cwd])
if skip_git_repo_check:
    cmd.append("--skip-git-repo-check")
cmd.append("-")

env = os.environ.copy()
if codex_home_override:
    env["CODEX_HOME"] = codex_home_override

with open(prompt_path, "rb") as prompt_stream, open(jsonl_path, "wb") as jsonl_stream:
    proc = subprocess.Popen(
        cmd,
        stdin=prompt_stream,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
    )

    while True:
        line = proc.stdout.readline() if proc.stdout is not None else b""
        if line:
            sys.stdout.buffer.write(line)
            sys.stdout.buffer.flush()
            jsonl_stream.write(line)
            jsonl_stream.flush()

        if proc.poll() is not None:
            if proc.stdout is not None:
                rest = proc.stdout.read()
                if rest:
                    sys.stdout.buffer.write(rest)
                    sys.stdout.buffer.flush()
                    jsonl_stream.write(rest)
                    jsonl_stream.flush()
            sys.exit(proc.returncode)

        if time.monotonic() - start > timeout_sec:
            proc.kill()
            timeout_line = (
                '{"type":"error","error":"sub-agent timeout","timeout_sec":'
                + str(timeout_sec)
                + "}\n"
            ).encode("utf-8")
            sys.stdout.buffer.write(timeout_line)
            sys.stdout.buffer.flush()
            jsonl_stream.write(timeout_line)
            jsonl_stream.flush()
            sys.exit(124)
PY
	status=$?
else
	cmd=()
	build_codex_cmd cmd
	if [[ -n "$codex_home_override" ]]; then
		CODEX_HOME="$codex_home_override" "${cmd[@]}" <"$prompt_file" | tee "$jsonl_file"
	else
		"${cmd[@]}" <"$prompt_file" | tee "$jsonl_file"
	fi
	status=${PIPESTATUS[0]}
fi
set -e

echo "$jsonl_file"
exit "$status"
