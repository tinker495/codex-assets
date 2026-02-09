#!/usr/bin/env bash
set -euo pipefail

# Rebuild symbol index with a bounded foreground watch run, then re-measure trace graph roots.
# Usage:
#   ./scripts/reindex_and_measure.sh [refresh_seconds]
# Env:
#   ROOTS="runWatchForeground watchProject discoverWorktreesForWatch"

refresh_seconds="${1:-20}"
roots="${ROOTS:-runWatchForeground watchProject discoverWorktreesForWatch}"

was_running=0
status_out="$(go run ./cmd/grepai watch --status 2>&1 || true)"
if printf '%s' "$status_out" | rg -q 'Status: running'; then
  was_running=1
fi

if (( was_running )); then
  echo "[info] stopping background watcher"
  go run ./cmd/grepai watch --stop >/dev/null 2>&1 || true
fi

log_file="${HOME}/.codex/sub_agent_runs/trace-noise-watch-refresh.log"
mkdir -p "$(dirname "$log_file")"

echo "[info] refreshing index via foreground watch (${refresh_seconds}s)"
( go run ./cmd/grepai watch >"$log_file" 2>&1 ) &
watch_pid=$!
watch_child_pid=""
sleep "$refresh_seconds"
watch_child_pid="$(pgrep -P "$watch_pid" | head -n1 || true)"

kill -INT "$watch_pid" >/dev/null 2>&1 || true
if [[ -n "$watch_child_pid" ]]; then
  kill -INT "$watch_child_pid" >/dev/null 2>&1 || true
fi

for _ in $(seq 1 20); do
  if ! kill -0 "$watch_pid" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

if kill -0 "$watch_pid" >/dev/null 2>&1; then
  kill -TERM "$watch_pid" >/dev/null 2>&1 || true
  if [[ -n "$watch_child_pid" ]]; then
    kill -TERM "$watch_child_pid" >/dev/null 2>&1 || true
  fi
  sleep 1
fi

if kill -0 "$watch_pid" >/dev/null 2>&1; then
  kill -KILL "$watch_pid" >/dev/null 2>&1 || true
fi
if [[ -n "$watch_child_pid" ]] && kill -0 "$watch_child_pid" >/dev/null 2>&1; then
  kill -KILL "$watch_child_pid" >/dev/null 2>&1 || true
fi

wait "$watch_pid" >/dev/null 2>&1 || true

echo "[info] measurements"
for root in $roots; do
  go run ./cmd/grepai trace graph "$root" --depth 2 --mode precise --json \
    | jq '{root:.graph.root,node_count:(.graph.nodes|length),edge_count:(.graph.edges|length)}'
done

if (( was_running )); then
  echo "[info] restoring background watcher"
  go run ./cmd/grepai watch --background >/dev/null 2>&1 || true
fi

echo "[info] refresh log: $log_file"
