#!/usr/bin/env bash
set -euo pipefail

LABEL="${LAUNCH_AGENT_LABEL:-com.tinker495.codexassets.sync}"
OLD_LABEL="${OLD_LAUNCH_AGENT_LABEL:-com.tinker495.codexskills.sync}"
USER_ID="$(id -u)"
PLIST_PATH="${HOME}/Library/LaunchAgents/${LABEL}.plist"
OLD_PLIST_PATH="${HOME}/Library/LaunchAgents/${OLD_LABEL}.plist"

if [[ -f "$PLIST_PATH" ]]; then
  echo "Plist exists: $PLIST_PATH"
else
  echo "Plist missing: $PLIST_PATH"
fi

launchctl print "gui/${USER_ID}/${LABEL}" 2>/dev/null | sed -n '1,80p' || echo "Launch agent not loaded"

if [[ "$OLD_LABEL" != "$LABEL" ]]; then
  if [[ -f "$OLD_PLIST_PATH" ]]; then
    echo "Legacy plist still exists: $OLD_PLIST_PATH"
  fi
  launchctl print "gui/${USER_ID}/${OLD_LABEL}" 2>/dev/null | sed -n '1,40p' || true
fi
