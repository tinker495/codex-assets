#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INTERVAL_MINUTES="${INTERVAL_MINUTES:-30}"

if ! [[ "$INTERVAL_MINUTES" =~ ^[0-9]+$ ]] || [[ "$INTERVAL_MINUTES" -lt 1 ]]; then
  echo "INTERVAL_MINUTES must be a positive integer" >&2
  exit 1
fi

while true; do
  "$ROOT_DIR/scripts/sync_and_push.sh" "$@" || true
  sleep "$((INTERVAL_MINUTES * 60))"
done
