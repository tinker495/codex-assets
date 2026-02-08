#!/usr/bin/env python3
"""Manage Ralph-style `prd.json` state for Codex iterations."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any

TOP_LEVEL_REQUIRED = ("project", "branchName", "description", "userStories")
STORY_REQUIRED = ("id", "title", "description", "acceptanceCriteria", "priority", "passes", "notes")
TYPECHECK_CRITERION = "typecheck passes"
BROWSER_CRITERION = "verify in browser using dev-browser skill"
DEFAULT_UI_KEYWORDS = (
    "ui",
    "screen",
    "page",
    "frontend",
    "component",
    "button",
    "form",
    "modal",
    "layout",
)
DEFAULT_QUALITY_COMMANDS: dict[str, list[str]] = {
    "python": ["pytest -q", "pre-commit run --all-files"],
    "node": ["npm test", "npm run lint"],
    "go": ["go test ./...", "go vet ./..."],
    "rust": ["cargo test", "cargo clippy --all-targets --all-features"],
    "java": ["./gradlew test", "./gradlew check"],
    "unknown": ["make test"],
}
COMMAND_PREFIXES = (
    "pytest",
    "python -m pytest",
    "pre-commit",
    "npm ",
    "pnpm ",
    "yarn ",
    "go ",
    "cargo ",
    "./gradlew",
    "make ",
    "tox",
    "uv run ",
)


def _load_prd(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"PRD file not found: {path}")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc

    stories = data.get("userStories")
    if not isinstance(stories, list):
        raise ValueError("`userStories` must be a list in prd.json")
    return data


def _save_prd(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _story_priority(story: dict[str, Any]) -> tuple[int, str]:
    priority = story.get("priority", 1_000_000)
    if not isinstance(priority, int):
        priority = 1_000_000
    story_id = story.get("id", "ZZZ")
    if not isinstance(story_id, str):
        story_id = "ZZZ"
    return priority, story_id


def _pending_stories(data: dict[str, Any]) -> list[dict[str, Any]]:
    stories = data.get("userStories", [])
    return sorted(
        [story for story in stories if isinstance(story, dict) and not story.get("passes", False)],
        key=_story_priority,
    )


def _find_story(data: dict[str, Any], story_id: str) -> dict[str, Any]:
    target = story_id.strip()
    for story in data["userStories"]:
        if not isinstance(story, dict):
            continue
        if story.get("id") == target:
            return story
    raise ValueError(f"Story not found: {target}")


def _normalize(lines: list[str]) -> list[str]:
    return [line.strip().lower() for line in lines if isinstance(line, str)]


def _is_ui_story(story: dict[str, Any], ui_keywords: list[str]) -> bool:
    title = story.get("title", "")
    description = story.get("description", "")
    haystack = f"{title} {description}".lower()
    return any(keyword in haystack for keyword in ui_keywords)


def _init_progress_file(path: Path) -> None:
    if path.exists():
        return
    started = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z")
    path.write_text(f"# Ralph Progress Log\nStarted: {started}\n---\n", encoding="utf-8")


def _detect_stack(repo_root: Path) -> str:
    if (repo_root / "pyproject.toml").exists() or (repo_root / "requirements.txt").exists():
        return "python"
    if (repo_root / "package.json").exists():
        return "node"
    if (repo_root / "go.mod").exists():
        return "go"
    if (repo_root / "Cargo.toml").exists():
        return "rust"
    if (repo_root / "build.gradle").exists() or (repo_root / "pom.xml").exists():
        return "java"
    return "unknown"


def _is_command_candidate(line: str) -> bool:
    normalized = line.strip()
    if not normalized or normalized.startswith("#"):
        return False
    if normalized.startswith("```"):
        return False
    if normalized.startswith("- "):
        normalized = normalized[2:].strip()
    if normalized.startswith("* "):
        normalized = normalized[2:].strip()
    normalized = re.sub(r"^\d+\.\s+", "", normalized)
    if normalized.startswith("$ "):
        normalized = normalized[2:]
    return any(normalized.startswith(prefix) for prefix in COMMAND_PREFIXES)


def _extract_quality_commands_from_agents(agents_path: Path) -> list[str]:
    if not agents_path.exists():
        return []

    commands: list[str] = []
    seen: set[str] = set()
    for raw_line in agents_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not _is_command_candidate(line):
            continue
        if line.startswith("$ "):
            line = line[2:].strip()
        if line in seen:
            continue
        seen.add(line)
        commands.append(line)
    return commands


def cmd_status(args: argparse.Namespace) -> int:
    data = _load_prd(Path(args.prd))
    stories = data["userStories"]
    total = len(stories)
    passed = sum(1 for story in stories if isinstance(story, dict) and story.get("passes", False))
    pending = total - passed

    payload = {"project": data.get("project"), "total": total, "passed": passed, "pending": pending}
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"project: {payload['project']}")
        print(f"total: {total}")
        print(f"passed: {passed}")
        print(f"pending: {pending}")
    return 0


def cmd_next(args: argparse.Namespace) -> int:
    data = _load_prd(Path(args.prd))
    pending = _pending_stories(data)
    if not pending:
        print("<promise>COMPLETE</promise>")
        return 0
    print(json.dumps(pending[0], indent=2))
    return 0


def cmd_mark_pass(args: argparse.Namespace) -> int:
    path = Path(args.prd)
    data = _load_prd(path)
    target_id = args.story_id.strip()
    story = _find_story(data, target_id)
    story["passes"] = True
    if args.note:
        existing = story.get("notes")
        if isinstance(existing, str) and existing.strip():
            story["notes"] = f"{existing.rstrip()}\n{args.note.strip()}"
        else:
            story["notes"] = args.note.strip()
    _save_prd(path, data)
    print(f"Marked {target_id} as passed")
    return 0


def cmd_mark_blocked(args: argparse.Namespace) -> int:
    path = Path(args.prd)
    data = _load_prd(path)
    target_id = args.story_id.strip()
    story = _find_story(data, target_id)

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z")
    reason = args.reason.strip()
    next_action = args.next_action.strip() if args.next_action else "Retry after resolving blocker"
    note_line = f"[{timestamp}] BLOCKED: {reason} | NEXT: {next_action}"

    existing = story.get("notes")
    if isinstance(existing, str) and existing.strip():
        story["notes"] = f"{existing.rstrip()}\n{note_line}"
    else:
        story["notes"] = note_line
    story["passes"] = False
    _save_prd(path, data)
    print(f"Marked {target_id} as blocked")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    data = _load_prd(Path(args.prd))
    errors: list[str] = []
    warnings: list[str] = []

    for field in TOP_LEVEL_REQUIRED:
        if field not in data:
            errors.append(f"Missing top-level field: {field}")

    project = data.get("project")
    if not isinstance(project, str) or not project.strip():
        errors.append("`project` must be a non-empty string")

    branch = data.get("branchName")
    if not isinstance(branch, str) or not branch.strip():
        errors.append("`branchName` must be a non-empty string")
    elif not branch.startswith("ralph/"):
        warnings.append("`branchName` should start with `ralph/`")

    description = data.get("description")
    if not isinstance(description, str) or not description.strip():
        errors.append("`description` must be a non-empty string")

    stories = data.get("userStories")
    if not isinstance(stories, list):
        errors.append("`userStories` must be a list")
        stories = []

    seen_ids: set[str] = set()
    ui_keywords = [value.strip().lower() for value in args.ui_keywords.split(",") if value.strip()]

    for idx, story in enumerate(stories, start=1):
        label = f"userStories[{idx}]"
        if not isinstance(story, dict):
            errors.append(f"{label} must be an object")
            continue

        for field in STORY_REQUIRED:
            if field not in story:
                errors.append(f"{label}: missing field `{field}`")

        story_id = story.get("id")
        if not isinstance(story_id, str) or not story_id.strip():
            errors.append(f"{label}: `id` must be a non-empty string")
        else:
            if story_id in seen_ids:
                errors.append(f"{label}: duplicate id `{story_id}`")
            seen_ids.add(story_id)

        title = story.get("title")
        if not isinstance(title, str) or not title.strip():
            errors.append(f"{label}: `title` must be a non-empty string")

        story_description = story.get("description")
        if not isinstance(story_description, str) or not story_description.strip():
            errors.append(f"{label}: `description` must be a non-empty string")

        priority = story.get("priority")
        if not isinstance(priority, int):
            errors.append(f"{label}: `priority` must be an integer")

        passes = story.get("passes")
        if not isinstance(passes, bool):
            errors.append(f"{label}: `passes` must be a boolean")

        notes = story.get("notes")
        if not isinstance(notes, str):
            errors.append(f"{label}: `notes` must be a string")

        criteria = story.get("acceptanceCriteria")
        if not isinstance(criteria, list) or not criteria:
            errors.append(f"{label}: `acceptanceCriteria` must be a non-empty list")
            continue

        normalized_criteria = _normalize(criteria)
        if TYPECHECK_CRITERION not in normalized_criteria:
            errors.append(f"{label}: missing acceptance criterion `Typecheck passes`")

        if args.check_ui and _is_ui_story(story, ui_keywords):
            if BROWSER_CRITERION not in normalized_criteria:
                warnings.append(
                    f"{label}: detected as UI story but missing `{BROWSER_CRITERION}` criterion"
                )

    result = {"ok": not errors and not (args.strict_warnings and warnings), "errors": errors, "warnings": warnings}
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"ok: {result['ok']}")
        if errors:
            print("errors:")
            for msg in errors:
                print(f"- {msg}")
        if warnings:
            print("warnings:")
            for msg in warnings:
                print(f"- {msg}")

    if errors:
        return 1
    if args.strict_warnings and warnings:
        return 1
    return 0


def cmd_append_progress(args: argparse.Namespace) -> int:
    progress_path = Path(args.progress)
    _init_progress_file(progress_path)

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z")
    lines = [f"## [{timestamp}] - {args.story_id.strip()}"]
    if args.thread_url:
        lines.append(f"Thread: {args.thread_url.strip()}")

    lines.append("- Summary:")
    lines.append(f"  - {args.summary.strip()}")

    if args.file:
        lines.append("- Files changed:")
        for file_path in args.file:
            lines.append(f"  - {file_path}")

    if args.learning:
        lines.append("- Learnings for future iterations:")
        for learning in args.learning:
            lines.append(f"  - {learning}")

    lines.append("---")
    block = "\n".join(lines) + "\n"
    with progress_path.open("a", encoding="utf-8") as handle:
        handle.write(block)

    print(f"Appended progress entry for {args.story_id.strip()} to {progress_path}")
    return 0


def cmd_brief(args: argparse.Namespace) -> int:
    data = _load_prd(Path(args.prd))
    stories = data["userStories"]
    pending = _pending_stories(data)
    next_story = pending[0] if pending else None

    payload: dict[str, Any] = {
        "project": data.get("project"),
        "branchName": data.get("branchName"),
        "description": data.get("description"),
        "totalStories": len(stories),
        "passedStories": sum(1 for story in stories if isinstance(story, dict) and story.get("passes", False)),
        "pendingStories": len(pending),
        "complete": len(pending) == 0,
        "nextStory": next_story,
        "stopSignal": "<promise>COMPLETE</promise>" if len(pending) == 0 else "",
    }
    print(json.dumps(payload, indent=2))
    return 0


def cmd_quality_plan(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).resolve()
    stack = args.stack
    if stack == "auto":
        stack = _detect_stack(repo_root)

    agents_path = (repo_root / args.agents) if not Path(args.agents).is_absolute() else Path(args.agents)
    agents_commands = _extract_quality_commands_from_agents(agents_path)

    source = "agents" if agents_commands else "defaults"
    commands = agents_commands if agents_commands else DEFAULT_QUALITY_COMMANDS.get(stack, DEFAULT_QUALITY_COMMANDS["unknown"])

    payload = {
        "repoRoot": str(repo_root),
        "stack": stack,
        "source": source,
        "agentsPath": str(agents_path),
        "commands": commands,
    }

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"repoRoot: {payload['repoRoot']}")
        print(f"stack: {stack}")
        print(f"source: {source}")
        print("commands:")
        for cmd in commands:
            print(f"- {cmd}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ralph state helper for Codex.")
    sub = parser.add_subparsers(dest="command", required=True)

    status = sub.add_parser("status", help="Show summary counts for prd.json.")
    status.add_argument("--prd", default="prd.json", help="Path to prd.json")
    status.add_argument("--json", action="store_true", help="Print JSON output")
    status.set_defaults(func=cmd_status)

    nxt = sub.add_parser("next", help="Print highest-priority pending story.")
    nxt.add_argument("--prd", default="prd.json", help="Path to prd.json")
    nxt.set_defaults(func=cmd_next)

    mark = sub.add_parser("mark-pass", help="Mark one story as passed.")
    mark.add_argument("--prd", default="prd.json", help="Path to prd.json")
    mark.add_argument("--story-id", required=True, help="Story id, e.g. US-003")
    mark.add_argument("--note", help="Optional note to append to story notes")
    mark.set_defaults(func=cmd_mark_pass)

    blocked = sub.add_parser("mark-blocked", help="Keep story pending and append blocker details to notes.")
    blocked.add_argument("--prd", default="prd.json", help="Path to prd.json")
    blocked.add_argument("--story-id", required=True, help="Story id, e.g. US-003")
    blocked.add_argument("--reason", required=True, help="Short blocker reason.")
    blocked.add_argument("--next-action", help="Next action to resolve blocker.")
    blocked.set_defaults(func=cmd_mark_blocked)

    validate = sub.add_parser("validate", help="Validate prd.json shape and criteria quality gates.")
    validate.add_argument("--prd", default="prd.json", help="Path to prd.json")
    validate.add_argument("--json", action="store_true", help="Print JSON output")
    validate.add_argument(
        "--strict-warnings",
        action="store_true",
        help="Fail when warnings are present (default: warnings do not fail).",
    )
    validate.add_argument(
        "--check-ui",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Check for browser verification criterion on UI stories.",
    )
    validate.add_argument(
        "--ui-keywords",
        default=",".join(DEFAULT_UI_KEYWORDS),
        help="Comma-separated keywords used to detect UI stories.",
    )
    validate.set_defaults(func=cmd_validate)

    append_progress = sub.add_parser("append-progress", help="Append one structured entry to progress.txt.")
    append_progress.add_argument("--progress", default="progress.txt", help="Path to progress.txt")
    append_progress.add_argument("--story-id", required=True, help="Story id, e.g. US-003")
    append_progress.add_argument("--summary", required=True, help="One-line summary of work done.")
    append_progress.add_argument("--thread-url", help="Optional thread URL for traceability.")
    append_progress.add_argument(
        "--file",
        action="append",
        help="File changed. Repeat this flag for multiple files.",
    )
    append_progress.add_argument(
        "--learning",
        action="append",
        help="Reusable learning or gotcha. Repeat for multiple items.",
    )
    append_progress.set_defaults(func=cmd_append_progress)

    brief = sub.add_parser("brief", help="Print machine-readable iteration brief.")
    brief.add_argument("--prd", default="prd.json", help="Path to prd.json")
    brief.set_defaults(func=cmd_brief)

    quality_plan = sub.add_parser("quality-plan", help="Suggest quality-check commands for current repository.")
    quality_plan.add_argument("--repo-root", default=".", help="Repository root path")
    quality_plan.add_argument("--agents", default="AGENTS.md", help="Path to AGENTS.md (relative to repo root by default)")
    quality_plan.add_argument(
        "--stack",
        choices=["auto", "python", "node", "go", "rust", "java", "unknown"],
        default="auto",
        help="Stack selection. Use auto to detect from repo files.",
    )
    quality_plan.add_argument("--json", action="store_true", help="Print JSON output")
    quality_plan.set_defaults(func=cmd_quality_plan)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except FileNotFoundError as exc:
        print(f"Error: {exc}")
        return 2
    except ValueError as exc:
        print(f"Error: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
