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
	local use_json="${1:-1}"
	cmd=(codex exec --model "$model")
	if [[ "$use_json" -eq 1 ]]; then
		cmd=(codex exec --json --model "$model")
	fi
	if [[ -n "$profile" ]]; then
		cmd+=(--profile "$profile")
	fi
	if [[ -n "$worker_cwd" ]]; then
		cmd+=(--cd "$worker_cwd")
	fi
	if [[ "$skip_git_repo_check" -eq 1 ]]; then
		cmd+=(--skip-git-repo-check)
	fi
	cmd+=(-)
}

run_once() {
	local use_json="$1"
	local append_log="${2:-0}"
	if [[ -n "$timeout_sec" && "$timeout_sec" -gt 0 ]]; then
		python3 "$(dirname "$0")/run_with_timeout.py" \
			"$timeout_sec" \
			"$prompt_file" \
			"$jsonl_file" \
			"$model" \
			"$profile" \
			"$worker_cwd" \
			"$skip_git_repo_check" \
			"$codex_home_override" \
			"$use_json" \
			"$append_log"
		return $?
	fi

	cmd=()
	build_codex_cmd "$use_json"
	if [[ "$append_log" -eq 1 ]]; then
		if [[ -n "$codex_home_override" ]]; then
			CODEX_HOME="$codex_home_override" "${cmd[@]}" <"$prompt_file" | tee -a "$jsonl_file"
		else
			"${cmd[@]}" <"$prompt_file" | tee -a "$jsonl_file"
		fi
		return ${PIPESTATUS[0]}
	fi

	if [[ -n "$codex_home_override" ]]; then
		CODEX_HOME="$codex_home_override" "${cmd[@]}" <"$prompt_file" | tee "$jsonl_file"
	else
		"${cmd[@]}" <"$prompt_file" | tee "$jsonl_file"
	fi
	return ${PIPESTATUS[0]}
}

set +e
run_once 1 0
status=$?
if [[ "$status" -ne 0 ]] && rg -q -F "Error: unknown flag: --json" "$jsonl_file"; then
	printf '%s\n' "Warning: codex rejected --json; rerunning once without --json." | tee -a "$jsonl_file" >&2
	run_once 0 1
	status=$?
fi
set -e

echo "$jsonl_file"
exit "$status"
