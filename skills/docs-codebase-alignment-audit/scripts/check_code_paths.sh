#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="${1:-$(pwd)}"
DOCS_ROOT="${2:-$REPO_ROOT/docs}"

if ! command -v rg >/dev/null 2>&1; then
  echo "[ERROR] rg is required"
  exit 2
fi

missing=0
tmp_paths="$(mktemp)"
trap 'rm -f "$tmp_paths"' EXIT
rg -o --no-filename '(src/[A-Za-z0-9_./-]+|tests/[A-Za-z0-9_./-]+)' "$DOCS_ROOT" -g '*.md' | sort -u > "$tmp_paths"

while IFS= read -r p; do
  [ -z "$p" ] && continue
  if [[ ! -e "$REPO_ROOT/$p" ]]; then
    echo "$p"
    missing=1
  fi
done < "$tmp_paths"

if [[ $missing -eq 1 ]]; then
  exit 1
fi
