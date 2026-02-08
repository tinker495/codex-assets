#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEFAULT_SKILLS_SOURCE="${HOME}/.codex/skills"
DEFAULT_AUTOMATIONS_SOURCE="${HOME}/.codex/automations"
SKILLS_SOURCE_DIR="${CODEX_SKILLS_SOURCE:-$DEFAULT_SKILLS_SOURCE}"
AUTOMATIONS_SOURCE_DIR="${CODEX_AUTOMATIONS_SOURCE:-$DEFAULT_AUTOMATIONS_SOURCE}"
SYNC_SKILLS=true
SYNC_AUTOMATIONS=true
SYNC_MODE="${CODEX_SYNC_MODE:-merge}"
REPO_SPEC="${GITHUB_REPO:-}"
VISIBILITY="${GITHUB_VISIBILITY:-private}"
COMMIT_PREFIX="${COMMIT_PREFIX:-chore(sync): codex assets update}"

print_help() {
  cat <<'HELP'
Usage: ./scripts/sync_and_push.sh [options]

Options:
  --skills-source <path>       Skills source folder (default: ~/.codex/skills)
  --automations-source <path>  Automations source folder (default: ~/.codex/automations)
  --source <path>              Backward-compatible alias of --skills-source
  --skills-only                Sync only skills
  --automations-only           Sync only automations
  --mode <merge|mirror>        Sync mode (default: merge)
  --merge                      Alias of --mode merge
  --mirror                     Alias of --mode mirror (deletes missing files)
  --repo <owner/name>          GitHub repository to create/use as origin
  --public                     Create repo as public when origin is missing
  --private                    Create repo as private when origin is missing (default)
  --message <text>             Commit message prefix
  -h, --help                   Show this help

Environment variables:
  CODEX_SKILLS_SOURCE, CODEX_AUTOMATIONS_SOURCE, GITHUB_REPO,
  GITHUB_VISIBILITY, COMMIT_PREFIX, CODEX_SYNC_MODE
HELP
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --skills-source)
      SKILLS_SOURCE_DIR="$2"
      shift 2
      ;;
    --automations-source)
      AUTOMATIONS_SOURCE_DIR="$2"
      shift 2
      ;;
    --source)
      SKILLS_SOURCE_DIR="$2"
      shift 2
      ;;
    --skills-only)
      SYNC_AUTOMATIONS=false
      shift
      ;;
    --automations-only)
      SYNC_SKILLS=false
      shift
      ;;
    --mode)
      SYNC_MODE="$2"
      shift 2
      ;;
    --merge)
      SYNC_MODE="merge"
      shift
      ;;
    --mirror)
      SYNC_MODE="mirror"
      shift
      ;;
    --repo)
      REPO_SPEC="$2"
      shift 2
      ;;
    --public)
      VISIBILITY="public"
      shift
      ;;
    --private)
      VISIBILITY="private"
      shift
      ;;
    --message)
      COMMIT_PREFIX="$2"
      shift 2
      ;;
    -h|--help)
      print_help
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      print_help
      exit 1
      ;;
  esac
done

if [[ "$SYNC_SKILLS" == "false" && "$SYNC_AUTOMATIONS" == "false" ]]; then
  echo "Nothing to sync: both skills and automations are disabled." >&2
  exit 1
fi

case "$SYNC_MODE" in
  merge|mirror)
    ;;
  *)
    echo "Invalid --mode value: $SYNC_MODE (expected: merge or mirror)" >&2
    exit 1
    ;;
esac

if [[ "$SYNC_SKILLS" == "true" && ! -d "$SKILLS_SOURCE_DIR" ]]; then
  echo "Skills source directory not found: $SKILLS_SOURCE_DIR" >&2
  exit 1
fi

if [[ "$SYNC_AUTOMATIONS" == "true" && ! -d "$AUTOMATIONS_SOURCE_DIR" ]]; then
  echo "Automations source directory not found: $AUTOMATIONS_SOURCE_DIR" >&2
  exit 1
fi

cd "$ROOT_DIR"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git init -b main
fi

if [[ -z "$REPO_SPEC" ]]; then
  if git remote get-url origin >/dev/null 2>&1; then
    origin_url="$(git remote get-url origin)"
    REPO_SPEC="$(printf '%s' "$origin_url" | sed -E 's#(git@github.com:|https://github.com/)##; s#\.git$##')"
  else
    gh_user="$(gh api user -q .login)"
    REPO_SPEC="${gh_user}/$(basename "$ROOT_DIR")"
  fi
fi

if ! git remote get-url origin >/dev/null 2>&1; then
  if gh repo view "$REPO_SPEC" >/dev/null 2>&1; then
    git remote add origin "https://github.com/${REPO_SPEC}.git"
  else
    gh repo create "$REPO_SPEC" "--$VISIBILITY" --source "$ROOT_DIR" --remote origin --description "Synced Codex skills and automations backup"
  fi
fi

if [[ "$SYNC_SKILLS" == "true" ]]; then
  mkdir -p "$ROOT_DIR/skills"
  if [[ "$SYNC_MODE" == "mirror" ]]; then
    rsync -a --delete --delete-excluded \
      --exclude='.DS_Store' \
      --exclude='.git' \
      --exclude='__pycache__/' \
      --exclude='*.pyc' \
      "$SKILLS_SOURCE_DIR"/ "$ROOT_DIR/skills"/
  else
    rsync -a \
      --exclude='.DS_Store' \
      --exclude='.git' \
      --exclude='__pycache__/' \
      --exclude='*.pyc' \
      "$SKILLS_SOURCE_DIR"/ "$ROOT_DIR/skills"/
  fi
fi

if [[ "$SYNC_AUTOMATIONS" == "true" ]]; then
  mkdir -p "$ROOT_DIR/automations"
  if [[ "$SYNC_MODE" == "mirror" ]]; then
    rsync -a --delete --delete-excluded \
      --exclude='.DS_Store' \
      --exclude='.git' \
      "$AUTOMATIONS_SOURCE_DIR"/ "$ROOT_DIR/automations"/
  else
    rsync -a \
      --exclude='.DS_Store' \
      --exclude='.git' \
      "$AUTOMATIONS_SOURCE_DIR"/ "$ROOT_DIR/automations"/
  fi
fi

if [[ ! -f "$ROOT_DIR/.gitignore" ]]; then
  cat > "$ROOT_DIR/.gitignore" <<'IGNORE'
.DS_Store
__pycache__/
*.pyc
.logs/
IGNORE
fi

git add -A

if git diff --cached --quiet; then
  echo "No changes to commit."
  exit 0
fi

timestamp="$(date '+%Y-%m-%d %H:%M:%S')"
git commit -m "$COMMIT_PREFIX ($timestamp)"

branch="$(git branch --show-current)"
if [[ -z "$branch" ]]; then
  branch="main"
  git checkout -b "$branch"
fi

git push -u origin "$branch"

echo "Sync complete: $REPO_SPEC ($branch)"
