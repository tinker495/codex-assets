#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

INPUT=""
CAPTION=""
OUTPUT=""
ITERATIONS="3"
EXTRA_ARGS=()

usage() {
  cat <<USAGE
Usage: $(basename "$0") --input <method.txt> --caption "<caption>" --output <target.png> [--iterations N] [-- <extra args>]

Stable output wrapper for PaperBanana generate.
- Runs generate command.
- If PaperBanana ignores --output and writes to auto run path, resolves final output from logs.
- Copies resolved file to --output deterministically.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --input|-i)
      INPUT="${2:-}"
      shift 2
      ;;
    --caption|-c)
      CAPTION="${2:-}"
      shift 2
      ;;
    --output|-o)
      OUTPUT="${2:-}"
      shift 2
      ;;
    --iterations|-n)
      ITERATIONS="${2:-}"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    --)
      shift
      EXTRA_ARGS+=("$@")
      break
      ;;
    *)
      EXTRA_ARGS+=("$1")
      shift
      ;;
  esac
done

if [[ -z "$INPUT" || -z "$CAPTION" || -z "$OUTPUT" ]]; then
  usage >&2
  exit 2
fi

mkdir -p "$(dirname "$OUTPUT")"

LOG_FILE="$(mktemp -t paperbanana-generate-XXXXXX.log)"
trap 'rm -f "$LOG_FILE"' EXIT

CMD=(bash "$SCRIPT_DIR/run_paperbanana.sh" generate --input "$INPUT" --caption "$CAPTION" --iterations "$ITERATIONS" --output "$OUTPUT")
if [[ ${#EXTRA_ARGS[@]} -gt 0 ]]; then
  CMD+=("${EXTRA_ARGS[@]}")
fi

if ! "${CMD[@]}" 2>&1 | tee "$LOG_FILE"; then
  echo "paperbanana-cli: generate failed" >&2
  exit 1
fi

if [[ -f "$OUTPUT" ]]; then
  echo "$OUTPUT"
  exit 0
fi

PARSED_OUTPUT="$(grep -Eo 'output=[^ ]+' "$LOG_FILE" | tail -1 | sed 's/^output=//' || true)"

if [[ -z "$PARSED_OUTPUT" ]]; then
  echo "paperbanana-cli: unable to resolve generated output path from logs" >&2
  exit 1
fi

if [[ ! -f "$PARSED_OUTPUT" ]]; then
  echo "paperbanana-cli: resolved output does not exist: $PARSED_OUTPUT" >&2
  exit 1
fi

cp "$PARSED_OUTPUT" "$OUTPUT"
echo "$OUTPUT"
