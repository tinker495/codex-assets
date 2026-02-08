#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEFAULT_SOURCE="${HOME}/.codex/skills"
SOURCE_DIR="${CODEX_SKILLS_SOURCE:-$DEFAULT_SOURCE}"
REPO_SPEC="${GITHUB_REPO:-}"
VISIBILITY="${GITHUB_VISIBILITY:-private}"
COMMIT_PREFIX="${COMMIT_PREFIX:-chore(sync): codex skills update}"

print_help() {
  cat <<'HELP'
Usage: ./scripts/sync_and_push.sh [options]

Options:
  --source <path>        Source folder to sync (default: ~/.codex/skills)
  --repo <owner/name>    GitHub repository to create/use as origin
  --public               Create repo as public when origin is missing
  --private              Create repo as private when origin is missing (default)
  --message <text>       Commit message prefix
  -h, --help             Show this help

Environment variables:
  CODEX_SKILLS_SOURCE, GITHUB_REPO, GITHUB_VISIBILITY, COMMIT_PREFIX
HELP
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --source)
      SOURCE_DIR="$2"
      shift 2
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

if [[ ! -d "$SOURCE_DIR" ]]; then
  echo "Source directory not found: $SOURCE_DIR" >&2
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
    gh repo create "$REPO_SPEC" "--$VISIBILITY" --source "$ROOT_DIR" --remote origin --description "Synced Codex skills backup"
  fi
fi

mkdir -p "$ROOT_DIR/skills"
rsync -a --delete --exclude='.DS_Store' --exclude='.git' "$SOURCE_DIR"/ "$ROOT_DIR/skills"/

if [[ ! -f "$ROOT_DIR/.gitignore" ]]; then
  cat > "$ROOT_DIR/.gitignore" <<'IGNORE'
.DS_Store
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
