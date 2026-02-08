#!/usr/bin/env python3
"""Create, save, load, complete, reopen, archive, and clean git-aware plan markdown files."""

import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

DEFAULT_STORE_DIR = Path("/tmp/plan-save-load")
DEFAULT_ARCHIVE_DIR = Path.home() / ".cache" / "plan-save-load" / "archive"
POLICY_REQUIRED_TICKET_GROUPS = {"hotfix", "release-checklist", "pr-review"}
DEFAULT_RETAIN_DAYS = 30


def run_git(repo_dir: Path, args: list[str]) -> str:
    """Run a git command and return stripped stdout."""
    command = ["git", *args]
    try:
        result = subprocess.run(
            command,
            cwd=str(repo_dir),
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as error:
        message = error.stderr.strip() or error.stdout.strip() or "git command failed"
        raise RuntimeError(f"{' '.join(command)}: {message}") from error
    return result.stdout.strip()


def sanitize_part(value: str, fallback: str) -> str:
    """Convert arbitrary text to a filename-safe token."""
    cleaned = re.sub(r"\s+", "-", value.strip())
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", cleaned)
    cleaned = re.sub(r"-{2,}", "-", cleaned)
    cleaned = cleaned.strip("-._")
    if not cleaned:
        cleaned = fallback
    return cleaned[:120]


def resolve_group_dir(store_dir: Path, plan_group: str | None) -> Path:
    """Resolve subdirectory used to separate scenario/task plans."""
    if not plan_group:
        return store_dir
    return store_dir / sanitize_part(plan_group, "default-group")


def ensure_store_dir(path: Path) -> None:
    """Create the storage directory if needed."""
    path.mkdir(parents=True, exist_ok=True)


def sort_by_mtime_desc(paths: list[Path]) -> list[Path]:
    """Sort files by most recently modified first, then by name."""
    return sorted(paths, key=lambda path: (path.stat().st_mtime, path.name), reverse=True)


def build_context(repo_dir: Path, ticket: str | None = None) -> dict[str, str]:
    """Collect repo metadata used for file naming and template content."""
    repo_root = Path(run_git(repo_dir, ["rev-parse", "--show-toplevel"]))
    repo_name = repo_root.name
    branch_name = run_git(repo_dir, ["rev-parse", "--abbrev-ref", "HEAD"])
    last_commit_subject = run_git(repo_dir, ["log", "-1", "--pretty=%s"])
    last_commit_hash = run_git(repo_dir, ["rev-parse", "--short", "HEAD"])

    repo_token = sanitize_part(repo_name, "repo")
    branch_token = sanitize_part(branch_name, "branch")
    commit_token = sanitize_part(last_commit_subject, "commit")
    ticket_token = sanitize_part(ticket, "") if ticket else ""

    name_tokens = [repo_token, branch_token]
    if ticket_token:
        name_tokens.append(ticket_token)
    name_tokens.append(commit_token)
    filename = f"{'-'.join(name_tokens)}.md"

    return {
        "repo_root": str(repo_root),
        "repo_name": repo_name,
        "branch_name": branch_name,
        "last_commit_subject": last_commit_subject,
        "last_commit_hash": last_commit_hash,
        "repo_token": repo_token,
        "branch_token": branch_token,
        "ticket_token": ticket_token,
        "filename": filename,
    }


def resolve_target_path(
    repo_dir: Path,
    store_dir: Path,
    plan_group: str | None,
    ticket: str | None,
) -> tuple[Path, dict[str, str], Path]:
    """Resolve target plan path for the current git state and group."""
    context = build_context(repo_dir, ticket=ticket)
    group_dir = resolve_group_dir(store_dir, plan_group)
    return group_dir / context["filename"], context, group_dir


def build_match_prefix(repo_dir: Path, ticket: str | None = None) -> str:
    """Build file prefix used to find matching plans."""
    context = build_context(repo_dir, ticket=ticket)
    prefix_tokens = [context["repo_token"], context["branch_token"]]
    if context["ticket_token"]:
        prefix_tokens.append(context["ticket_token"])
    return f"{'-'.join(prefix_tokens)}-"


def find_matching_paths(repo_dir: Path, group_dir: Path, ticket: str | None = None) -> list[Path]:
    """Find files matching current repo+branch naming prefix."""
    if not group_dir.exists():
        return []

    prefix = build_match_prefix(repo_dir, ticket=ticket)
    return sort_by_mtime_desc(list(group_dir.glob(f"{prefix}*.md")))


def resolve_latest_path(repo_dir: Path, group_dir: Path, ticket: str | None = None) -> Path:
    """Resolve latest matching plan file or raise if missing."""
    matches = find_matching_paths(repo_dir, group_dir, ticket=ticket)
    if not matches:
        raise RuntimeError(f"No matching plan file found in: {group_dir}")
    return matches[0]


def render_template(
    context: dict[str, str],
    plan_group: str | None,
    issue_id: str | None,
    pr_id: str | None,
    base_branch: str | None,
    policy_exempt_reason: str | None,
) -> str:
    """Create initial markdown body for new plan files."""
    created_at = datetime.now(tz=timezone.utc).isoformat(timespec="seconds")
    group_value = sanitize_part(plan_group or "default", "default")
    ticket_value = context["ticket_token"] or ""

    return (
        "# Plan\n\n"
        f"- Repository: `{context['repo_name']}`\n"
        f"- Branch: `{context['branch_name']}`\n"
        f"- Base Branch: `{base_branch or ''}`\n"
        f"- Plan Group: `{group_value}`\n"
        f"- Ticket: `{ticket_value}`\n"
        f"- Issue: `{issue_id or ''}`\n"
        f"- PR: `{pr_id or ''}`\n"
        f"- Policy Exempt Reason: `{policy_exempt_reason or ''}`\n"
        f"- Last Commit: `{context['last_commit_subject']}` ({context['last_commit_hash']})\n"
        f"- Created At (UTC): `{created_at}`\n\n"
        "## Goal\n"
        "- \n\n"
        "## Scope\n"
        "- \n\n"
        "## Steps\n"
        "1. \n\n"
        "## Validation Commands\n"
        "```bash\n"
        "# pytest -q\n"
        "```\n\n"
        "## Rollback Plan\n"
        "- \n\n"
        "## Decision Log\n"
        "- \n\n"
        "## Notes\n"
        "- \n"
    )


def read_save_content(args: argparse.Namespace) -> str:
    """Resolve content from --content or stdin input."""
    if args.stdin:
        content = sys.stdin.read()
    else:
        content = args.content
    if not content:
        raise RuntimeError("No content provided. Use --content or --stdin.")
    return content


def requires_ticket_by_policy(plan_group: str | None) -> bool:
    """Return true when the selected plan group enforces ticket usage by policy."""
    if not plan_group:
        return False
    return sanitize_part(plan_group, "").lower() in POLICY_REQUIRED_TICKET_GROUPS


def validate_common_options(args: argparse.Namespace) -> None:
    """Validate cross-command options before executing handlers."""
    plan_group = getattr(args, "plan_group", None)
    ticket = getattr(args, "ticket", None)
    explicit_required = getattr(args, "require_ticket", False)
    policy_exempt = getattr(args, "policy_exempt", False)
    policy_exempt_reason = getattr(args, "policy_exempt_reason", None)
    policy_required = requires_ticket_by_policy(plan_group)

    if explicit_required and policy_exempt:
        raise RuntimeError("--policy-exempt cannot be combined with --require-ticket.")

    if policy_exempt and not policy_required:
        raise RuntimeError("--policy-exempt is only valid for policy groups.")

    if policy_exempt and not policy_exempt_reason:
        raise RuntimeError("--policy-exempt-reason is required when using --policy-exempt.")

    if explicit_required and not ticket:
        raise RuntimeError("Ticket is required. Provide --ticket when using --require-ticket.")

    if policy_required and not ticket and not policy_exempt:
        if policy_required and plan_group:
            normalized = sanitize_part(plan_group, "").lower()
            raise RuntimeError(
                f"Ticket is required for policy group '{normalized}'. "
                f"Provide --ticket or use --policy-exempt with --policy-exempt-reason."
            )


def unique_destination(destination: Path) -> Path:
    """Return destination or a suffixed path if it already exists."""
    if not destination.exists():
        return destination

    stem = destination.stem
    suffix = destination.suffix
    timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return destination.with_name(f"{stem}-{timestamp}{suffix}")


def archive_plan_file(
    source_path: Path,
    archive_dir: Path,
    plan_group: str | None,
    move: bool,
) -> Path:
    """Archive one plan file to a persistent location."""
    archive_group_dir = resolve_group_dir(archive_dir, plan_group)
    ensure_store_dir(archive_group_dir)

    destination = unique_destination(archive_group_dir / source_path.name)
    if move:
        shutil.move(str(source_path), str(destination))
    else:
        shutil.copy2(source_path, destination)
    return destination


def append_completion_note(path: Path, summary: str | None) -> None:
    """Append a completion section to a plan markdown file."""
    completed_at = datetime.now(tz=timezone.utc).isoformat(timespec="seconds")
    note = (
        "\n\n## Completion\n"
        f"- Completed At (UTC): `{completed_at}`\n"
        f"- Summary: {summary or ''}\n"
        "- Archived By: `complete` command\n"
    )
    with path.open("a", encoding="utf-8") as handle:
        handle.write(note)


def append_archive_record(
    path: Path,
    source_path: Path,
    destination_path: Path,
    retain_days: int,
    archived_via: str,
) -> None:
    """Append archive metadata to an archived plan file."""
    archived_at = datetime.now(tz=timezone.utc).isoformat(timespec="seconds")
    note = (
        "\n\n## Archive Record\n"
        f"- Archived At (UTC): `{archived_at}`\n"
        f"- Archived Via: `{archived_via}`\n"
        f"- Source Path: `{source_path}`\n"
        f"- Archived Path: `{destination_path}`\n"
        f"- Suggested Retention (days): `{retain_days}`\n"
    )
    with path.open("a", encoding="utf-8") as handle:
        handle.write(note)


def append_reopen_note(path: Path, archive_source: Path, reason: str | None) -> None:
    """Append reopen metadata when a plan is restored from archive."""
    reopened_at = datetime.now(tz=timezone.utc).isoformat(timespec="seconds")
    note = (
        "\n\n## Reopen\n"
        f"- Reopened At (UTC): `{reopened_at}`\n"
        f"- Archive Source: `{archive_source}`\n"
        f"- Reason: {reason or ''}\n"
    )
    with path.open("a", encoding="utf-8") as handle:
        handle.write(note)


def select_current_or_latest(
    target_path: Path,
    repo_dir: Path,
    group_dir: Path,
    ticket: str | None,
    latest: bool,
) -> Path:
    """Resolve a plan path based on --latest preference."""
    if latest:
        return resolve_latest_path(repo_dir, group_dir, ticket=ticket)
    return target_path


def cmd_path(args: argparse.Namespace) -> int:
    repo_dir = Path(args.repo_dir).resolve()
    store_dir = Path(args.store_dir).resolve()
    target_path, _, group_dir = resolve_target_path(repo_dir, store_dir, args.plan_group, args.ticket)
    path = select_current_or_latest(target_path, repo_dir, group_dir, args.ticket, args.latest)
    print(path)
    return 0


def cmd_create(args: argparse.Namespace) -> int:
    repo_dir = Path(args.repo_dir).resolve()
    store_dir = Path(args.store_dir).resolve()
    path, context, group_dir = resolve_target_path(repo_dir, store_dir, args.plan_group, args.ticket)
    ensure_store_dir(group_dir)

    if path.exists() and not args.force:
        raise RuntimeError(f"Plan file already exists: {path}")

    body = render_template(
        context,
        plan_group=args.plan_group,
        issue_id=args.issue_id,
        pr_id=args.pr_id,
        base_branch=args.base_branch,
        policy_exempt_reason=args.policy_exempt_reason,
    )
    path.write_text(body, encoding="utf-8")
    print(path)
    return 0


def cmd_save(args: argparse.Namespace) -> int:
    repo_dir = Path(args.repo_dir).resolve()
    store_dir = Path(args.store_dir).resolve()
    target_path, _, group_dir = resolve_target_path(repo_dir, store_dir, args.plan_group, args.ticket)
    ensure_store_dir(group_dir)

    path = select_current_or_latest(target_path, repo_dir, group_dir, args.ticket, args.latest)
    content = read_save_content(args)

    if args.append and path.exists():
        with path.open("a", encoding="utf-8") as handle:
            if handle.tell() > 0 and not content.startswith("\n"):
                handle.write("\n")
            handle.write(content)
    else:
        path.write_text(content, encoding="utf-8")

    print(path)
    return 0


def cmd_load(args: argparse.Namespace) -> int:
    repo_dir = Path(args.repo_dir).resolve()
    store_dir = Path(args.store_dir).resolve()
    target_path, _, group_dir = resolve_target_path(repo_dir, store_dir, args.plan_group, args.ticket)

    path = select_current_or_latest(target_path, repo_dir, group_dir, args.ticket, args.latest)
    if not path.exists():
        raise RuntimeError(f"Plan file not found: {path}")

    sys.stdout.write(path.read_text(encoding="utf-8"))
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    store_dir = Path(args.store_dir).resolve()
    if not store_dir.exists():
        return 0

    if args.all_groups:
        files = sort_by_mtime_desc(list(store_dir.rglob("*.md")))
    else:
        group_dir = resolve_group_dir(store_dir, args.plan_group)
        if not group_dir.exists():
            return 0

        if args.all:
            files = sort_by_mtime_desc(list(group_dir.glob("*.md")))
        else:
            repo_dir = Path(args.repo_dir).resolve()
            files = find_matching_paths(repo_dir, group_dir, ticket=args.ticket)

    if args.latest:
        if not files:
            raise RuntimeError("No plan files available for latest selection.")
        files = files[:1]

    for file_path in files:
        print(file_path)
    return 0


def cmd_archive(args: argparse.Namespace) -> int:
    repo_dir = Path(args.repo_dir).resolve()
    store_dir = Path(args.store_dir).resolve()
    archive_dir = Path(args.archive_dir).resolve()

    target_path, _, group_dir = resolve_target_path(repo_dir, store_dir, args.plan_group, args.ticket)
    source_path = select_current_or_latest(target_path, repo_dir, group_dir, args.ticket, args.latest)

    if not source_path.exists():
        raise RuntimeError(f"Plan file not found: {source_path}")

    destination = archive_plan_file(
        source_path=source_path,
        archive_dir=archive_dir,
        plan_group=args.plan_group,
        move=args.move,
    )
    append_archive_record(
        path=destination,
        source_path=source_path,
        destination_path=destination,
        retain_days=args.retain_days,
        archived_via="archive",
    )

    print(destination)
    return 0


def cmd_complete(args: argparse.Namespace) -> int:
    repo_dir = Path(args.repo_dir).resolve()
    store_dir = Path(args.store_dir).resolve()
    archive_dir = Path(args.archive_dir).resolve()

    target_path, _, group_dir = resolve_target_path(repo_dir, store_dir, args.plan_group, args.ticket)
    source_path = select_current_or_latest(target_path, repo_dir, group_dir, args.ticket, args.latest)

    if not source_path.exists():
        raise RuntimeError(f"Plan file not found: {source_path}")

    append_completion_note(source_path, args.summary)
    destination = archive_plan_file(
        source_path=source_path,
        archive_dir=archive_dir,
        plan_group=args.plan_group,
        move=args.move,
    )
    append_archive_record(
        path=destination,
        source_path=source_path,
        destination_path=destination,
        retain_days=args.retain_days,
        archived_via="complete",
    )

    print(destination)
    return 0


def cmd_reopen(args: argparse.Namespace) -> int:
    repo_dir = Path(args.repo_dir).resolve()
    store_dir = Path(args.store_dir).resolve()
    archive_dir = Path(args.archive_dir).resolve()

    target_path, _, archive_group_dir = resolve_target_path(repo_dir, archive_dir, args.plan_group, args.ticket)
    source_path = select_current_or_latest(target_path, repo_dir, archive_group_dir, args.ticket, args.latest)
    if not source_path.exists():
        raise RuntimeError(f"Archived plan file not found: {source_path}")

    restore_group_dir = resolve_group_dir(store_dir, args.plan_group)
    ensure_store_dir(restore_group_dir)

    destination = unique_destination(restore_group_dir / source_path.name)
    if args.move:
        shutil.move(str(source_path), str(destination))
    else:
        shutil.copy2(source_path, destination)

    append_reopen_note(destination, source_path, args.reason)
    print(destination)
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    repo_dir = Path(args.repo_dir).resolve()
    store_dir = Path(args.store_dir).resolve()
    archive_dir = Path(args.archive_dir).resolve()

    active_group_dir = resolve_group_dir(store_dir, args.plan_group)
    archive_group_dir = resolve_group_dir(archive_dir, args.plan_group)

    active_matches = find_matching_paths(repo_dir, active_group_dir, ticket=args.ticket)
    archive_matches = find_matching_paths(repo_dir, archive_group_dir, ticket=args.ticket)

    latest_active = active_matches[0] if active_matches else None
    latest_archived = archive_matches[0] if archive_matches else None

    print(f"active_count={len(active_matches)}")
    print(f"archived_count={len(archive_matches)}")
    print(f"latest_active={latest_active or ''}")
    print(f"latest_archived={latest_archived or ''}")
    return 0


def cmd_gc(args: argparse.Namespace) -> int:
    store_dir = Path(args.store_dir).resolve()
    if not store_dir.exists():
        return 0

    cutoff_ts = time.time() - (args.older_than_days * 86400)

    if args.all_groups:
        candidates = list(store_dir.rglob("*.md"))
    else:
        group_dir = resolve_group_dir(store_dir, args.plan_group)
        if not group_dir.exists():
            return 0

        if args.match_current:
            repo_dir = Path(args.repo_dir).resolve()
            candidates = find_matching_paths(repo_dir, group_dir, ticket=args.ticket)
        else:
            candidates = list(group_dir.glob("*.md"))

    stale_files = [path for path in candidates if path.stat().st_mtime < cutoff_ts]
    stale_files = sort_by_mtime_desc(stale_files)

    for path in stale_files:
        if args.dry_run:
            print(f"DRY-RUN {path}")
        else:
            path.unlink(missing_ok=True)
            print(path)

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Manage create/save/load/complete/reopen/archive lifecycle for plan markdown files."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--repo-dir", default=os.getcwd(), help="Git repository path")
    common.add_argument(
        "--store-dir",
        default=str(DEFAULT_STORE_DIR),
        help="Directory where plan markdown files are saved",
    )
    common.add_argument(
        "--plan-group",
        help="Optional task/scenario group, stored as a subdirectory under store dir",
    )
    common.add_argument("--ticket", help="Optional stable ticket/issue token used in filename matching")
    common.add_argument(
        "--require-ticket",
        action="store_true",
        help="Require --ticket (in addition to policy-required groups)",
    )
    common.add_argument(
        "--policy-exempt",
        action="store_true",
        help="Allow one-time policy exception in ticket-required groups",
    )
    common.add_argument(
        "--policy-exempt-reason",
        help="Reason for policy exemption; required with --policy-exempt",
    )

    path_parser = subparsers.add_parser("path", parents=[common], help="Print target plan file path")
    path_parser.add_argument(
        "--latest",
        action="store_true",
        help="Print latest matching plan path for current repo+branch",
    )
    path_parser.set_defaults(func=cmd_path)

    create_parser = subparsers.add_parser("create", parents=[common], help="Create plan markdown")
    create_parser.add_argument("--force", action="store_true", help="Overwrite existing file")
    create_parser.add_argument("--issue-id", help="Issue identifier to seed template metadata")
    create_parser.add_argument("--pr-id", help="PR identifier to seed template metadata")
    create_parser.add_argument("--base-branch", help="Base branch recorded in template metadata")
    create_parser.set_defaults(func=cmd_create)

    save_parser = subparsers.add_parser("save", parents=[common], help="Save plan content")
    content_group = save_parser.add_mutually_exclusive_group(required=True)
    content_group.add_argument("--content", help="Markdown content to save")
    content_group.add_argument("--stdin", action="store_true", help="Read markdown content from stdin")
    save_parser.add_argument("--append", action="store_true", help="Append to existing content")
    save_parser.add_argument(
        "--latest",
        action="store_true",
        help="Save to latest matching plan file instead of current commit-derived file",
    )
    save_parser.set_defaults(func=cmd_save)

    load_parser = subparsers.add_parser("load", parents=[common], help="Load plan markdown")
    load_parser.add_argument(
        "--latest",
        action="store_true",
        help="Load latest matching plan file for current repo+branch",
    )
    load_parser.set_defaults(func=cmd_load)

    complete_parser = subparsers.add_parser(
        "complete",
        parents=[common],
        help="Mark a plan complete and archive it to persistent storage",
    )
    complete_parser.add_argument(
        "--archive-dir",
        default=str(DEFAULT_ARCHIVE_DIR),
        help="Persistent archive directory",
    )
    complete_parser.add_argument(
        "--latest",
        action="store_true",
        help="Complete latest matching plan file instead of current commit-derived file",
    )
    complete_parser.add_argument("--summary", help="Short completion summary text")
    complete_parser.add_argument(
        "--retain-days",
        type=int,
        default=DEFAULT_RETAIN_DAYS,
        help=f"Suggested retention period written to archive record (default: {DEFAULT_RETAIN_DAYS})",
    )
    complete_parser.add_argument(
        "--move",
        action="store_true",
        help="Move source file to archive after completion (default: copy)",
    )
    complete_parser.set_defaults(func=cmd_complete)

    reopen_parser = subparsers.add_parser(
        "reopen",
        parents=[common],
        help="Restore an archived plan into active /tmp workspace",
    )
    reopen_parser.add_argument(
        "--archive-dir",
        default=str(DEFAULT_ARCHIVE_DIR),
        help="Persistent archive directory",
    )
    reopen_parser.add_argument(
        "--latest",
        action="store_true",
        help="Reopen latest matching archived plan file",
    )
    reopen_parser.add_argument(
        "--reason",
        help="Optional reason for reopening this plan",
    )
    reopen_parser.add_argument(
        "--move",
        action="store_true",
        help="Move from archive to active workspace (default: copy)",
    )
    reopen_parser.set_defaults(func=cmd_reopen)

    status_parser = subparsers.add_parser(
        "status",
        parents=[common],
        help="Show active vs archived plan counts and latest matching paths",
    )
    status_parser.add_argument(
        "--archive-dir",
        default=str(DEFAULT_ARCHIVE_DIR),
        help="Persistent archive directory",
    )
    status_parser.set_defaults(func=cmd_status)

    list_parser = subparsers.add_parser("list", parents=[common], help="List saved plan files")
    list_parser.add_argument("--all", action="store_true", help="List every plan file in selected group")
    list_parser.add_argument(
        "--all-groups",
        action="store_true",
        help="List every plan file recursively under store dir",
    )
    list_parser.add_argument(
        "--latest",
        action="store_true",
        help="Show only one latest plan from the selected list scope",
    )
    list_parser.set_defaults(func=cmd_list)

    archive_parser = subparsers.add_parser(
        "archive",
        parents=[common],
        help="Copy or move a plan from /tmp to a persistent archive location",
    )
    archive_parser.add_argument(
        "--archive-dir",
        default=str(DEFAULT_ARCHIVE_DIR),
        help="Persistent archive directory",
    )
    archive_parser.add_argument(
        "--latest",
        action="store_true",
        help="Archive latest matching plan file instead of current commit-derived file",
    )
    archive_parser.add_argument(
        "--retain-days",
        type=int,
        default=DEFAULT_RETAIN_DAYS,
        help=f"Suggested retention period written to archive record (default: {DEFAULT_RETAIN_DAYS})",
    )
    archive_parser.add_argument("--move", action="store_true", help="Move instead of copy")
    archive_parser.set_defaults(func=cmd_archive)

    gc_parser = subparsers.add_parser("gc", parents=[common], help="Delete stale plan files by age")
    gc_parser.add_argument(
        "--older-than-days",
        type=int,
        default=14,
        help="Delete files older than this many days (default: 14)",
    )
    gc_parser.add_argument("--dry-run", action="store_true", help="Show files without deleting them")
    gc_parser.add_argument(
        "--all-groups",
        action="store_true",
        help="Apply cleanup across all groups recursively",
    )
    gc_parser.add_argument(
        "--match-current",
        action="store_true",
        help="Only cleanup files matching current repo+branch (and optional ticket)",
    )
    gc_parser.set_defaults(func=cmd_gc)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        validate_common_options(args)
        return args.func(args)
    except RuntimeError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
