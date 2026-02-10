#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="${1:-$(pwd)}"
DOCS_ROOT="${2:-$REPO_ROOT/docs}"
MAKEFILE_PATH="$REPO_ROOT/Makefile"

if ! command -v rg >/dev/null 2>&1; then
  echo "[ERROR] rg is required"
  exit 2
fi

if [[ ! -f "$MAKEFILE_PATH" ]]; then
  echo "[ERROR] Makefile not found: $MAKEFILE_PATH"
  exit 2
fi

tmp_docs="$(mktemp)"
tmp_make="$(mktemp)"
trap 'rm -f "$tmp_docs" "$tmp_make"' EXIT

rg -o --no-filename 'make\s+[A-Za-z0-9_.-]+' "$DOCS_ROOT" -g '*.md' | awk '{print $2}' | sort -u > "$tmp_docs"
rg --no-filename '^([A-Za-z0-9_.-]+):' "$MAKEFILE_PATH" | sed 's/:.*//' | sort -u > "$tmp_make"

comm -23 "$tmp_docs" "$tmp_make"

# Re-run to capture exit code by content size.
if [[ -n "$(comm -23 "$tmp_docs" "$tmp_make")" ]]; then
  exit 1
fi
