#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LABEL="${LAUNCH_AGENT_LABEL:-com.tinker495.codexassets.sync}"
OLD_LABEL="${OLD_LAUNCH_AGENT_LABEL:-com.tinker495.codexskills.sync}"
INTERVAL_MINUTES="${INTERVAL_MINUTES:-30}"
SKILLS_SOURCE_DIR="${CODEX_SKILLS_SOURCE:-${HOME}/.codex/skills}"
AUTOMATIONS_SOURCE_DIR="${CODEX_AUTOMATIONS_SOURCE:-${HOME}/.codex/automations}"
REPO_SPEC="${GITHUB_REPO:-}"
USER_ID="$(id -u)"
PLIST_PATH="${HOME}/Library/LaunchAgents/${LABEL}.plist"
OLD_PLIST_PATH="${HOME}/Library/LaunchAgents/${OLD_LABEL}.plist"
LOG_DIR="${ROOT_DIR}/.logs"

if ! [[ "$INTERVAL_MINUTES" =~ ^[0-9]+$ ]] || [[ "$INTERVAL_MINUTES" -lt 1 ]]; then
  echo "INTERVAL_MINUTES must be a positive integer" >&2
  exit 1
fi

if [[ ! -d "$SKILLS_SOURCE_DIR" ]]; then
  echo "Skills source directory not found: $SKILLS_SOURCE_DIR" >&2
  exit 1
fi

if [[ ! -d "$AUTOMATIONS_SOURCE_DIR" ]]; then
  echo "Automations source directory not found: $AUTOMATIONS_SOURCE_DIR" >&2
  exit 1
fi

if [[ -z "$REPO_SPEC" ]]; then
  if git -C "$ROOT_DIR" remote get-url origin >/dev/null 2>&1; then
    origin_url="$(git -C "$ROOT_DIR" remote get-url origin)"
    REPO_SPEC="$(printf '%s' "$origin_url" | sed -E 's#(git@github.com:|https://github.com/)##; s#\.git$##')"
  else
    gh_user="$(gh api user -q .login)"
    REPO_SPEC="${gh_user}/$(basename "$ROOT_DIR")"
  fi
fi

mkdir -p "${HOME}/Library/LaunchAgents" "$LOG_DIR"

cat > "$PLIST_PATH" <<EOF_PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>${LABEL}</string>

  <key>ProgramArguments</key>
  <array>
    <string>${ROOT_DIR}/scripts/sync_and_push.sh</string>
    <string>--skills-source</string>
    <string>${SKILLS_SOURCE_DIR}</string>
    <string>--automations-source</string>
    <string>${AUTOMATIONS_SOURCE_DIR}</string>
    <string>--repo</string>
    <string>${REPO_SPEC}</string>
  </array>

  <key>WorkingDirectory</key>
  <string>${ROOT_DIR}</string>

  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key>
    <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    <key>HOME</key>
    <string>${HOME}</string>
  </dict>

  <key>RunAtLoad</key>
  <true/>

  <key>StartInterval</key>
  <integer>$((INTERVAL_MINUTES * 60))</integer>

  <key>StandardOutPath</key>
  <string>${LOG_DIR}/launch-agent.out.log</string>

  <key>StandardErrorPath</key>
  <string>${LOG_DIR}/launch-agent.err.log</string>
</dict>
</plist>
EOF_PLIST

if [[ "$OLD_LABEL" != "$LABEL" ]]; then
  launchctl bootout "gui/${USER_ID}" "$OLD_PLIST_PATH" >/dev/null 2>&1 || true
  launchctl disable "gui/${USER_ID}/${OLD_LABEL}" >/dev/null 2>&1 || true
  rm -f "$OLD_PLIST_PATH"
fi

launchctl bootout "gui/${USER_ID}" "$PLIST_PATH" >/dev/null 2>&1 || true
launchctl bootstrap "gui/${USER_ID}" "$PLIST_PATH"
launchctl enable "gui/${USER_ID}/${LABEL}"
launchctl kickstart -k "gui/${USER_ID}/${LABEL}"

echo "Installed launch agent: ${LABEL}"
echo "Plist: ${PLIST_PATH}"
echo "Interval: every ${INTERVAL_MINUTES} minute(s)"
echo "Logs: ${LOG_DIR}/launch-agent.out.log, ${LOG_DIR}/launch-agent.err.log"
