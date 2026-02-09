#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

INPUT=""
CAPTION=""
OUTPUT=""
ITERATIONS="3"
OUTPUT_RESOLUTION="1k"
IMAGE_PROFILE="pro"
IMAGE_PROFILE_EXPLICIT="false"
EXTRA_ARGS=()

usage() {
  cat <<USAGE
Usage: $(basename "$0") --input <method.txt> --caption "<caption>" --output <target.png> [--iterations N] [--output-resolution 1k|2k|4k] [--image-profile flash|pro] [-- <extra args>]

Stable output wrapper for PaperBanana generate.
- Runs generate command.
- If PaperBanana ignores --output and writes to auto run path, resolves final output from logs.
- Copies resolved file to --output deterministically.

Image model profiles (default: pro):
- flash: gemini-2.5-flash-image (or google/gemini-2.5-flash-image for openrouter_imagen)
- pro:   gemini-3-pro-image-preview (or google/gemini-3-pro-image-preview for openrouter_imagen)

Resolution profiles (default: 1k):
- 1k, 2k, 4k
USAGE
}

has_image_model_arg() {
  local arg
  for arg in "${EXTRA_ARGS[@]-}"; do
    if [[ -z "$arg" ]]; then
      continue
    fi
    if [[ "$arg" == "--image-model" || "$arg" == --image-model=* ]]; then
      return 0
    fi
  done
  return 1
}

resolve_image_provider() {
  local provider="google_imagen"
  local args=("${EXTRA_ARGS[@]-}")
  local idx=0
  local arg=""
  local args_len="${#args[@]}"

  while [[ $idx -lt $args_len ]]; do
    arg="${args[$idx]}"
    if [[ -z "$arg" ]]; then
      idx=$((idx + 1))
      continue
    fi
    if [[ "$arg" == "--image-provider" ]]; then
      if [[ $((idx + 1)) -lt $args_len ]]; then
        provider="${args[$((idx + 1))]}"
      fi
      idx=$((idx + 2))
      continue
    fi
    if [[ "$arg" == --image-provider=* ]]; then
      provider="${arg#--image-provider=}"
    fi
    idx=$((idx + 1))
  done

  echo "$provider"
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
    --output-resolution|--resolution)
      OUTPUT_RESOLUTION="${2:-}"
      shift 2
      ;;
    --image-profile)
      IMAGE_PROFILE="${2:-}"
      IMAGE_PROFILE_EXPLICIT="true"
      shift 2
      ;;
    --flash)
      IMAGE_PROFILE="flash"
      IMAGE_PROFILE_EXPLICIT="true"
      shift
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

if has_image_model_arg; then
  if [[ "$IMAGE_PROFILE_EXPLICIT" == "true" ]]; then
    echo "paperbanana-cli: choose either --image-profile or --image-model, not both" >&2
    exit 2
  fi
  # Default profile must not override explicit image-model from extra args.
  IMAGE_PROFILE=""
fi

OUTPUT_RESOLUTION="$(echo "$OUTPUT_RESOLUTION" | tr '[:upper:]' '[:lower:]')"
case "$OUTPUT_RESOLUTION" in
  1k|2k|4k)
    ;;
  *)
    echo "paperbanana-cli: unsupported --output-resolution '$OUTPUT_RESOLUTION' (use: 1k|2k|4k)" >&2
    exit 2
    ;;
esac

IMAGE_MODEL_OVERRIDE=""
IMAGE_PROVIDER_OVERRIDE="$(resolve_image_provider)"
if [[ -n "$IMAGE_PROFILE" ]]; then
  case "$IMAGE_PROFILE" in
    flash)
      if [[ "$IMAGE_PROVIDER_OVERRIDE" == "openrouter_imagen" ]]; then
        IMAGE_MODEL_OVERRIDE="google/gemini-2.5-flash-image"
      else
        IMAGE_MODEL_OVERRIDE="gemini-2.5-flash-image"
      fi
      ;;
    pro)
      if [[ "$IMAGE_PROVIDER_OVERRIDE" == "openrouter_imagen" ]]; then
        IMAGE_MODEL_OVERRIDE="google/gemini-3-pro-image-preview"
      else
        IMAGE_MODEL_OVERRIDE="gemini-3-pro-image-preview"
      fi
      ;;
    *)
      echo "paperbanana-cli: unsupported --image-profile '$IMAGE_PROFILE' (use: flash|pro)" >&2
      exit 2
      ;;
  esac
fi

CMD=(
  bash "$SCRIPT_DIR/run_paperbanana.sh" generate
  --input "$INPUT"
  --caption "$CAPTION"
  --iterations "$ITERATIONS"
  --output-resolution "$OUTPUT_RESOLUTION"
  --output "$OUTPUT"
)
if [[ -n "$IMAGE_MODEL_OVERRIDE" ]]; then
  CMD+=(--image-model "$IMAGE_MODEL_OVERRIDE")
fi
if [[ -n "${EXTRA_ARGS[*]-}" ]]; then
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
