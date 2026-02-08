#!/usr/bin/env bash
set -euo pipefail

LABEL="${LAUNCH_AGENT_LABEL:-com.tinker495.codexassets.sync}"
OLD_LABEL="${OLD_LAUNCH_AGENT_LABEL:-com.tinker495.codexskills.sync}"
USER_ID="$(id -u)"
PLIST_PATH="${HOME}/Library/LaunchAgents/${LABEL}.plist"
OLD_PLIST_PATH="${HOME}/Library/LaunchAgents/${OLD_LABEL}.plist"

launchctl bootout "gui/${USER_ID}" "$PLIST_PATH" >/dev/null 2>&1 || true
launchctl disable "gui/${USER_ID}/${LABEL}" >/dev/null 2>&1 || true
rm -f "$PLIST_PATH"

if [[ "$OLD_LABEL" != "$LABEL" ]]; then
  launchctl bootout "gui/${USER_ID}" "$OLD_PLIST_PATH" >/dev/null 2>&1 || true
  launchctl disable "gui/${USER_ID}/${OLD_LABEL}" >/dev/null 2>&1 || true
  rm -f "$OLD_PLIST_PATH"
fi

echo "Uninstalled launch agent: ${LABEL}"
