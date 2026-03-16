#!/usr/bin/env python3
"""
Inventory TODO markers under a root path and summarize TODOs added in the current git diff.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
import re
from typing import Iterable

COMMENT_TODO_PATTERN = re.compile(
    r"(?:^\s*(?:#|//|/\*+|\*|<!--|;|--)\s*TODO\b|"
    r"\s(?:#|//|/\*+|\*|<!--|;|--)\s*TODO\b|"
    r"^\s*TODO\b)"
)
STRING_LITERAL_PATTERN = re.compile(r"""(?P<prefix>[rubfRUBF]*)(?P<quote>['"])(?P<content>.*?)(?P=quote)""")
NUMBERED_TODO_PATTERN = re.compile(r"^\d+\.\s+\*\*TODO\*\*")
CONTROL_FLOW_PREFIXES = (
    "if ",
    "elif ",
    "while ",
    "for ",
    "def ",
    "class ",
    "with ",
    "except ",
    "case ",
    "match ",
    "assert ",
)
HUNK_PATTERN = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")
DEFAULT_IGNORED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".idea",
    ".vscode",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    "coverage",
    ".next",
    ".nuxt",
    ".turbo",
    "target",
    "out",
}
SOURCE_SUFFIXES = {
    ".c",
    ".cc",
    ".cpp",
    ".cs",
    ".css",
    ".go",
    ".h",
    ".hpp",
    ".html",
    ".java",
    ".js",
    ".json",
    ".jsx",
    ".kt",
    ".kts",
    ".lua",
    ".mjs",
    ".php",
    ".py",
    ".rb",
    ".rs",
    ".scss",
    ".sh",
    ".sql",
    ".swift",
    ".toml",
    ".ts",
    ".tsx",
    ".vue",
    ".xml",
    ".yaml",
    ".yml",
    ".zsh",
}
SOURCE_FILENAMES = {
    "Dockerfile",
    "Makefile",
    "Justfile",
    "CMakeLists.txt",
}


@dataclass(frozen=True)
class TodoItem:
    path: str
    line: int
    text: str
    source: str


@dataclass(frozen=True)
class SkippedFile:
    path: str
    reason: str


def contains_todo_marker(line_text: str) -> bool:
    if COMMENT_TODO_PATTERN.search(line_text):
        return True
    stripped_line = line_text.lstrip()
    if any(stripped_line.startswith(prefix) for prefix in CONTROL_FLOW_PREFIXES):
        return False
    for match in STRING_LITERAL_PATTERN.finditer(line_text):
        if is_string_todo_placeholder(match.group("content")):
            return True
    return False


def is_string_todo_placeholder(content: str) -> bool:
    stripped = content.strip()
    if stripped in {"TODO", "[TODO]", "(TODO)", "{TODO}", "**TODO**"}:
        return True
    if "TODO:" in stripped:
        return True
    if stripped.startswith(("# TODO", "## TODO", "### TODO")):
        return True
    if NUMBERED_TODO_PATTERN.match(stripped):
        return True
    return False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inventory TODO markers and summarize TODOs added in the current git diff."
    )
    parser.add_argument("root", nargs="?", default=".", help="Root directory or file to scan.")
    parser.add_argument(
        "--mode",
        choices=("scan", "diff", "both"),
        default="both",
        help="Choose current inventory, diff-added TODOs, or both.",
    )
    parser.add_argument(
        "--all-text",
        action="store_true",
        help="Scan all UTF-8 text files instead of only common source/config files.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    return parser.parse_args()


def resolve_root(raw_root: str) -> Path:
    root = Path(raw_root).expanduser().resolve()
    if not root.exists():
        raise SystemExit(f"Root does not exist: {root}")
    return root


def iter_candidate_files(root: Path, all_text: bool) -> Iterable[Path]:
    if root.is_file():
        yield root
        return

    for path in root.rglob("*"):
        if path.is_dir():
            continue
        if any(part in DEFAULT_IGNORED_DIRS for part in path.parts):
            continue
        if all_text or should_scan_file(path):
            yield path


def should_scan_file(path: Path) -> bool:
    return path.suffix in SOURCE_SUFFIXES or path.name in SOURCE_FILENAMES


def read_text_lines(path: Path) -> tuple[list[str] | None, str | None]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        return None, f"os-error:{exc.strerror or exc.__class__.__name__}"
    if b"\x00" in raw:
        return None, "binary"
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return None, "non-utf8"
    return text.splitlines(), None


def collect_scan_todos(root: Path, all_text: bool) -> tuple[list[TodoItem], list[SkippedFile]]:
    items: list[TodoItem] = []
    skipped: list[SkippedFile] = []
    base_root = root.parent if root.is_file() else root
    for path in iter_candidate_files(root, all_text):
        lines, skip_reason = read_text_lines(path)
        relative_path = str(path.relative_to(base_root))
        if skip_reason is not None:
            skipped.append(SkippedFile(path=relative_path, reason=skip_reason))
            continue
        assert lines is not None
        for line_number, line_text in enumerate(lines, start=1):
            if contains_todo_marker(line_text):
                items.append(
                    TodoItem(
                        path=relative_path,
                        line=line_number,
                        text=line_text.strip(),
                        source="current",
                    )
                )
    return items, skipped


def find_git_repo_root(root: Path) -> Path | None:
    start = root if root.is_dir() else root.parent
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=start,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    repo_root = Path(result.stdout.strip()).resolve()
    return repo_root if repo_root.exists() else None


def collect_diff_todos(root: Path) -> tuple[list[TodoItem], str]:
    repo_root = find_git_repo_root(root)
    if repo_root is None:
        return [], "unavailable"

    scoped_items: dict[tuple[str, int, str, str], TodoItem] = {}
    scope_root = root if root.is_dir() else root
    for scope_name, extra_args in (("unstaged", []), ("staged", ["--cached"])):
        diff_text = run_git_diff(repo_root, extra_args)
        for item in parse_diff_todos(diff_text, repo_root, scope_root, scope_name):
            key = (item.path, item.line, item.text, item.source)
            scoped_items[key] = item
    items = sorted(scoped_items.values(), key=lambda item: (item.path, item.line, item.source))
    return items, "available"


def run_git_diff(repo_root: Path, extra_args: list[str]) -> str:
    command = ["git", "diff", "--no-color", "--unified=0", "--relative", *extra_args]
    result = subprocess.run(
        command,
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def parse_diff_todos(
    diff_text: str,
    repo_root: Path,
    scope_root: Path,
    scope_name: str,
) -> list[TodoItem]:
    items: list[TodoItem] = []
    current_file: Path | None = None
    next_new_line: int | None = None
    normalized_scope_root = scope_root.resolve()

    for raw_line in diff_text.splitlines():
        if raw_line.startswith("+++ "):
            file_token = raw_line[4:]
            if file_token == "/dev/null":
                current_file = None
                continue
            if file_token.startswith("b/"):
                file_token = file_token[2:]
            current_file = (repo_root / file_token).resolve()
            continue

        hunk_match = HUNK_PATTERN.match(raw_line)
        if hunk_match:
            next_new_line = int(hunk_match.group(1))
            continue

        if current_file is None or next_new_line is None:
            continue

        if raw_line.startswith("+") and not raw_line.startswith("+++"):
            line_text = raw_line[1:]
            if contains_todo_marker(line_text) and is_in_scope(current_file, normalized_scope_root):
                relative_path = make_relative_path(current_file, normalized_scope_root)
                items.append(
                    TodoItem(
                        path=relative_path,
                        line=next_new_line,
                        text=line_text.strip(),
                        source=f"diff-{scope_name}",
                    )
                )
            next_new_line += 1
            continue

        if raw_line.startswith(" ") and not raw_line.startswith("+++"):
            next_new_line += 1
            continue

        if raw_line.startswith("-") and not raw_line.startswith("---"):
            continue

    return items


def is_in_scope(path: Path, scope_root: Path) -> bool:
    if scope_root.is_file():
        return path == scope_root
    try:
        path.relative_to(scope_root)
    except ValueError:
        return False
    return True


def make_relative_path(path: Path, scope_root: Path) -> str:
    if scope_root.is_file():
        return path.name
    return str(path.relative_to(scope_root))


def build_summary(
    root: Path,
    current_items: list[TodoItem],
    skipped_files: list[SkippedFile],
    diff_items: list[TodoItem],
    diff_status: str,
    all_text: bool,
    mode: str,
) -> dict[str, object]:
    return {
        "root": str(root),
        "mode": mode,
        "scan_scope": "all-text" if all_text else "source-and-config",
        "current_todo_count": len(current_items),
        "current_todo_file_count": len({item.path for item in current_items}),
        "added_todo_count": len(diff_items),
        "diff_status": diff_status,
        "skipped_file_count": len(skipped_files),
    }


def render_text(
    summary: dict[str, object],
    current_items: list[TodoItem],
    skipped_files: list[SkippedFile],
    diff_items: list[TodoItem],
) -> str:
    lines = [
        "TODO Inventory",
        f"- Root: {summary['root']}",
        f"- Mode: {summary['mode']}",
        f"- Scan scope: {summary['scan_scope']}",
        f"- Current TODOs: {summary['current_todo_count']} across {summary['current_todo_file_count']} files",
        f"- Added TODOs in current diff: {summary['added_todo_count']} ({summary['diff_status']})",
        f"- Skipped files: {summary['skipped_file_count']}",
        "",
        "Current TODOs",
    ]

    if current_items:
        lines.extend(f"- {item.path}:{item.line} {item.text}" for item in current_items)
    else:
        lines.append("- none")

    lines.extend(["", "Added TODOs In Current Diff"])
    if diff_items:
        lines.extend(
            f"- [{item.source}] {item.path}:{item.line} {item.text}" for item in diff_items
        )
    else:
        lines.append("- none")

    lines.extend(["", "Skipped Files"])
    if skipped_files:
        lines.extend(f"- {item.path} ({item.reason})" for item in skipped_files)
    else:
        lines.append("- none")

    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    root = resolve_root(args.root)

    current_items: list[TodoItem] = []
    skipped_files: list[SkippedFile] = []
    if args.mode in {"scan", "both"}:
        current_items, skipped_files = collect_scan_todos(root, args.all_text)

    diff_items: list[TodoItem] = []
    diff_status = "not-requested"
    if args.mode in {"diff", "both"}:
        diff_items, diff_status = collect_diff_todos(root)

    summary = build_summary(
        root=root,
        current_items=current_items,
        skipped_files=skipped_files,
        diff_items=diff_items,
        diff_status=diff_status,
        all_text=args.all_text,
        mode=args.mode,
    )

    if args.json:
        payload = {
            "summary": summary,
            "current_todos": [asdict(item) for item in current_items],
            "added_todos_in_diff": [asdict(item) for item in diff_items],
            "skipped_files": [asdict(item) for item in skipped_files],
        }
        print(json.dumps(payload, indent=2))
        return

    print(render_text(summary, current_items, skipped_files, diff_items))


if __name__ == "__main__":
    main()
