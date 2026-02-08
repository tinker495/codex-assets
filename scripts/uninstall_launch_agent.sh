#!/usr/bin/env bash
set -euo pipefail

LABEL="${LAUNCH_AGENT_LABEL:-com.tinker495.codexskills.sync}"
USER_ID="$(id -u)"
PLIST_PATH="${HOME}/Library/LaunchAgents/${LABEL}.plist"

launchctl bootout "gui/${USER_ID}" "$PLIST_PATH" >/dev/null 2>&1 || true
launchctl disable "gui/${USER_ID}/${LABEL}" >/dev/null 2>&1 || true

if [[ -f "$PLIST_PATH" ]]; then
  rm -f "$PLIST_PATH"
fi

echo "Uninstalled launch agent: ${LABEL}"
