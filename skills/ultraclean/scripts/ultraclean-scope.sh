#!/usr/bin/env bash
# ultraclean-scope.sh — deterministic scope detection for the ultraclean skill.
# Emits the raw git signals the orchestrator needs to build >=3 disjoint partitions.
#
# Usage: ultraclean-scope.sh [full|branch] [--base <ref>]
#   (no mode arg) -> auto: on main/master => full, else => branch
#   full          -> whole codebase; emits candidate module dirs with source-file counts
#   branch        -> diff vs base ref; emits changed files + touched dirs (folder = review unit)
#   --base <ref>  -> base ref for branch-mode diff (default: origin/main, then origin/master, main, master)
set -euo pipefail

mode_override=""
base_override=""
while [ $# -gt 0 ]; do
  case "$1" in
    full|branch) mode_override="$1" ;;
    --base) shift; base_override="${1:-}" ;;
    *) echo "ultraclean-scope: unknown arg '$1'" >&2; exit 2 ;;
  esac
  shift
done

git rev-parse --is-inside-work-tree >/dev/null 2>&1 \
  || { echo "ultraclean-scope: not inside a git work tree" >&2; exit 1; }

branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo DETACHED)"

if [ -n "$mode_override" ]; then
  mode="$mode_override"
elif [ "$branch" = "main" ] || [ "$branch" = "master" ]; then
  mode="full"
else
  mode="branch"
fi

# Broad source-file extension filter (tune as needed for the repo).
SRC='\.(py|pyi|js|jsx|ts|tsx|mjs|cjs|go|rs|java|kt|kts|c|h|cc|cpp|hpp|cs|rb|php|swift|scala|sh|bash|sql|vue|svelte|css|scss|md|toml|ya?ml|json|cfg|ini)$'

echo "MODE=$mode"
echo "BRANCH=$branch"

if [ "$mode" = "branch" ]; then
  base=""
  if [ -n "$base_override" ]; then
    base="$base_override"
  else
    for r in origin/main origin/master main master; do
      if git rev-parse --verify --quiet "$r" >/dev/null 2>&1; then base="$r"; break; fi
    done
  fi
  if [ -z "$base" ]; then
    echo "BASE=<none>"
    echo "ultraclean-scope: no base ref found; pass --base <ref>" >&2
    exit 1
  fi
  echo "BASE=$base"

  # Union of committed-since-base + unstaged + staged changes.
  changed="$( { git diff --name-only "$base"...HEAD; git diff --name-only; git diff --name-only --cached; } 2>/dev/null \
    | sort -u | sed '/^$/d' )"

  echo "--- CHANGED FILES ---"
  printf '%s\n' "$changed" | sed '/^$/d'

  # Folder = review unit. Count DIRECT (non-recursive) source files only, so a root-level
  # change ('.') or a parent dir does not pull the whole subtree and break partition disjointness.
  echo "--- TOUCHED DIRS (dir<TAB>direct_source_file_count) ---"
  printf '%s\n' "$changed" | sed '/^$/d' | while IFS= read -r f; do dirname "$f"; done \
    | sort -u | while IFS= read -r d; do
        [ -n "$d" ] || continue
        c="$(git ls-files -- "$d" \
             | awk -v d="$d" 'd=="."{if(index($0,"/")==0)print;next}{if(index(substr($0,length(d)+2),"/")==0)print}' \
             | { grep -Ec "$SRC" || true; })"
        printf '%s\t%s\n' "$d" "$c"
      done
else
  echo "--- CANDIDATE MODULE DIRS (dir<TAB>source_file_count, desc) ---"
  git ls-files | { grep -E "$SRC" || true; } | while IFS= read -r f; do dirname "$f"; done \
    | sort | uniq -c | sort -rn | sed -E 's/^ *([0-9]+) (.*)$/\2\t\1/'
fi
