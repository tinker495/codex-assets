#!/usr/bin/env bash
set -euo pipefail

# Global fallback for running PaperBanana from any workspace.
PAPERBANANA_HOME="${PAPERBANANA_HOME:-/Users/mrx-ksjung/project/paperbanana}"

if command -v paperbanana >/dev/null 2>&1; then
  exec paperbanana "$@"
fi

if command -v uv >/dev/null 2>&1 && [[ -d "$PAPERBANANA_HOME" ]]; then
  exec uv run --project "$PAPERBANANA_HOME" paperbanana "$@"
fi

cat >&2 <<EOF
paperbanana-cli: unable to run PaperBanana.
- Tried: 'paperbanana'
- Fallback: 'uv run --project $PAPERBANANA_HOME paperbanana'
Set PAPERBANANA_HOME to your local PaperBanana project path if needed.
EOF
exit 127
