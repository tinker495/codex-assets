#!/usr/bin/env bash
set -euo pipefail

LABEL="${LAUNCH_AGENT_LABEL:-com.tinker495.codexskills.sync}"
USER_ID="$(id -u)"
PLIST_PATH="${HOME}/Library/LaunchAgents/${LABEL}.plist"

if [[ -f "$PLIST_PATH" ]]; then
  echo "Plist exists: $PLIST_PATH"
else
  echo "Plist missing: $PLIST_PATH"
fi

launchctl print "gui/${USER_ID}/${LABEL}" 2>/dev/null | sed -n '1,80p' || echo "Launch agent not loaded"
