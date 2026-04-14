#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

READ_ONLY_PREFIXES = (
    "cat ",
    "sed ",
    "find ",
    "rg ",
    "head ",
    "tail ",
    "wc ",
    "tmux capture-pane",
    "git rev-parse",
    "git status",
    "git diff",
    "git log",
    "git show",
    "test -f ",
    "test -d ",
    "[ -f ",
    "[ -d ",
    "pwd",
    "printf ",
    "echo ",
    "stat ",
    "ls ",
)
ARCHIVE_CONTEXT_MARKERS = (
    "/sessions/",
    ".jsonl",
    "memory.md",
    "automation.toml",
    ".log",
    "capture-pane",
    ".omx/notepad.md",
    "sub_agent_runs",
)
PATH_PROBE_PREFIXES = (
    "test -f ",
    "test -d ",
    "rg --files -g ",
    "git rev-parse",
)
EXIT_CODE_PATTERN = re.compile(r"Process exited with code (\d+)")
COMMAND_NOT_FOUND_PATTERN = re.compile(
    r"(?m)^(?:zsh:\d+:\s*)?[^:\n]+: command not found(?:[:\s]|$)"
)
FATAL_NOT_GIT_PATTERN = re.compile(r"(?m)^fatal: not a git repository")
JQ_PARSE_ERROR_PATTERN = re.compile(r"(?m)^jq: parse error")
NO_MATCHES_PATTERN = re.compile(r"(?m)^zsh:\d+:\s+no matches found:")
NO_SUCH_FILE_PATTERN = re.compile(
    r"(?m)^(?:[^:\n]+: )?(?P<path>[^\n:]+): No such file or directory$"
)
MODULE_NOT_FOUND_PATTERN = re.compile(
    r"ModuleNotFoundError: No module named '([^']+)'"
)
UNKNOWN_FLAG_JSON_PATTERN = re.compile(r"(?m)^Error: unknown flag: --json\b")
UNKNOWN_FLAG_REPO_PATTERN = re.compile(r"(?m)^Error: unknown flag: --repo\b")
UNABLE_TO_RESOLVE_PR_PATTERN = re.compile(r"(?m)^unable to resolve PR from current branch\b")
WRITE_STDIN_CLOSED_PATTERN = re.compile(r"(?m)^write_stdin failed: stdin is closed\b")
SKILL_PATH_PATTERN = re.compile(r"(/[^\s\"']*SKILL\.md)")
ENV_ASSIGNMENT_PATTERN = re.compile(
    r"^(?:[A-Za-z_][A-Za-z0-9_]*=(?:\"[^\"]*\"|'[^']*'|[^\s]+)\s+)+"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Join session tool calls and summarize automation-review evidence."
    )
    parser.add_argument(
        "--file",
        action="append",
        default=[],
        help="Session JSONL file to review. Repeatable.",
    )
    return parser.parse_args()


def load_call_args(raw: str) -> dict[str, Any]:
    try:
        return json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        return {}


def normalize_output(raw: Any) -> str:
    if isinstance(raw, str):
        return raw
    if raw is None:
        return ""
    if isinstance(raw, list):
        text_chunks: list[str] = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            for key in ("text", "output_text"):
                value = item.get(key)
                if isinstance(value, str):
                    text_chunks.append(value)
                    break
        return "\n".join(text_chunks)
    if isinstance(raw, dict):
        for key in ("text", "output_text"):
            value = raw.get(key)
            if isinstance(value, str):
                return value
        return json.dumps(raw, ensure_ascii=False)
    return str(raw)


def extract_exit_code(output: str) -> int | None:
    match = EXIT_CODE_PATTERN.search(output)
    return int(match.group(1)) if match else None


def strip_env_assignments(cmd: str) -> str:
    stripped = cmd.lstrip()
    while True:
        match = ENV_ASSIGNMENT_PATTERN.match(stripped)
        if not match:
            return stripped
        stripped = stripped[match.end() :].lstrip()


def split_shell_segments(cmd: str) -> list[str]:
    base = strip_env_assignments(cmd)
    return [segment.strip() for segment in re.split(r"[|;&]", base) if segment.strip()]


def is_read_only_command(cmd: str) -> bool:
    parts = split_shell_segments(cmd)
    if not parts:
        return False
    for part in parts:
        if part in {"then", "else", "fi", "do", "done"}:
            continue
        if not part.startswith(READ_ONLY_PREFIXES):
            return False
    return True


def is_archive_context(cmd: str) -> bool:
    return any(marker in cmd for marker in ARCHIVE_CONTEXT_MARKERS)


def has_shell_failure(output: str) -> bool:
    return any(
        pattern.search(output)
        for pattern in (
            COMMAND_NOT_FOUND_PATTERN,
            FATAL_NOT_GIT_PATTERN,
            JQ_PARSE_ERROR_PATTERN,
            NO_MATCHES_PATTERN,
            NO_SUCH_FILE_PATTERN,
            UNKNOWN_FLAG_JSON_PATTERN,
            UNKNOWN_FLAG_REPO_PATTERN,
            UNABLE_TO_RESOLVE_PR_PATTERN,
            WRITE_STDIN_CLOSED_PATTERN,
        )
    )


def looks_like_path_listing(line: str) -> bool:
    return "/" in line or line.endswith(".py") or line.endswith(".md")


def derive_edit_target(runtime_path: Path, codex_home: Path) -> str:
    parts = runtime_path.parts
    if "skills" not in parts:
        return "unmapped"
    skill_index = parts.index("skills")
    if skill_index + 1 >= len(parts):
        return "unmapped"
    skill_name = parts[skill_index + 1]
    return str(codex_home / "skills" / skill_name / "SKILL.md")


def classify_failure(
    *,
    tool_name: str | None,
    cmd: str,
    output: str,
    exit_code: int | None,
    session_cwd: str | None,
) -> tuple[str, str] | None:
    stripped = strip_env_assignments(cmd)

    if tool_name == "write_stdin" and WRITE_STDIN_CLOSED_PATTERN.search(output):
        return ("operational", "write_stdin failed: stdin is closed")

    if tool_name != "exec_command":
        return None

    shell_failure = has_shell_failure(output)
    if is_read_only_command(cmd) and exit_code == 0 and is_archive_context(cmd):
        shell_failure = False
    if exit_code in (None, 0) and not shell_failure:
        return None

    if WRITE_STDIN_CLOSED_PATTERN.search(output):
        return ("operational", "write_stdin failed: stdin is closed")
    if "Invalid YAML in frontmatter" in output or "mapping values are not allowed here" in output:
        return ("operational", "frontmatter/YAML error")
    if NO_MATCHES_PATTERN.search(output):
        return ("operational", "zsh: no matches found")
    if stripped.startswith("rg ") and (
        "unmatched \"" in output
        or "parse error near `|'" in output
        or 'the literal "\\n" is not allowed in a regex' in output
    ):
        return ("operational", "rg search syntax error")
    if exit_code == 1 and not shell_failure:
        if any(stripped.startswith(prefix) for prefix in PATH_PROBE_PREFIXES) or stripped == "pwd":
            return ("operational", "discovery/path probe failure")
        if stripped.startswith("rg "):
            return None
    if "ModuleNotFoundError: No module named" in output:
        match = MODULE_NOT_FOUND_PATTERN.search(output)
        target = match.group(1) if match else "unknown"
        return ("repo_specific", f"ModuleNotFoundError::{target}")
    if "ERROR collecting" in output:
        return ("repo_specific", "ERROR collecting")
    if FATAL_NOT_GIT_PATTERN.search(output):
        category = "repo_specific" if session_cwd and "/project/" in session_cwd else "operational"
        return (category, "fatal: not a git repository")
    if "No such file or directory" in output:
        match = NO_SUCH_FILE_PATTERN.search(output)
        target = match.group("path") if match else "No such file or directory"
        for prefix in ("can't read ", "cannot open ", "open "):
            if target.startswith(prefix):
                target = target[len(prefix) :]
        repo_tokens = ("pytest", "tests/", "uv run pytest", "PYTHONPATH=src")
        if "docs/shared/agent-tiers.md" in output:
            category = "operational"
        elif any(token in cmd for token in repo_tokens):
            category = "repo_specific"
        elif session_cwd and session_cwd.startswith("/Users/mrx-ksjung/project/"):
            category = "repo_specific"
        else:
            category = "operational"
        return (category, f"No such file or directory::{target}")
    if UNKNOWN_FLAG_JSON_PATTERN.search(output):
        return ("operational", "Error: unknown flag: --json")
    if UNKNOWN_FLAG_REPO_PATTERN.search(output):
        return ("operational", "Error: unknown flag: --repo")
    if JQ_PARSE_ERROR_PATTERN.search(output):
        return ("operational", "jq: parse error")
    if UNABLE_TO_RESOLVE_PR_PATTERN.search(output):
        return ("operational", "unable to resolve PR from current branch")
    if COMMAND_NOT_FOUND_PATTERN.search(output):
        return ("operational", "command not found")
    if any(stripped.startswith(prefix) for prefix in PATH_PROBE_PREFIXES) or stripped == "pwd":
        return ("operational", "discovery/path probe failure")
    return ("operational", "other failure")


def summarize(files: list[Path], codex_home: Path) -> dict[str, Any]:
    calls_by_session: dict[str, dict[str, dict[str, Any]]] = {}
    session_cwds: dict[str, str | None] = {}
    operational_counts: Counter[str] = Counter()
    repo_counts: Counter[str] = Counter()
    operational_sessions: defaultdict[str, set[str]] = defaultdict(set)
    repo_sessions: defaultdict[str, set[str]] = defaultdict(set)
    missing_paths: Counter[str] = Counter()
    missing_path_sessions: defaultdict[str, set[str]] = defaultdict(set)
    missing_modules: Counter[str] = Counter()
    missing_module_sessions: defaultdict[str, set[str]] = defaultdict(set)
    discovery_failures: list[dict[str, Any]] = []
    partial_success_probes: list[dict[str, Any]] = []
    skill_drift_counts: Counter[str] = Counter()
    skill_drift_sessions: defaultdict[str, set[str]] = defaultdict(set)
    sessions_with_records = 0

    for file_path in files:
        session_id = file_path.name
        calls = calls_by_session.setdefault(session_id, {})
        saw_response_item = False
        for raw_line in file_path.read_text().splitlines():
            if not raw_line.strip():
                continue
            item = json.loads(raw_line)
            if item.get("type") == "session_meta":
                payload = item.get("payload") or {}
                session_cwds[session_id] = payload.get("cwd")
            if item.get("type") != "response_item":
                continue
            saw_response_item = True
            payload = item.get("payload") or {}
            payload_type = payload.get("type")

            if payload_type == "function_call":
                calls[payload.get("call_id", "")] = {
                    "name": payload.get("name"),
                    "args": load_call_args(payload.get("arguments", "")),
                }
            elif payload_type == "function_call_output":
                call = calls.get(payload.get("call_id", ""), {})
                tool_name = call.get("name")
                args = call.get("args") or {}
                cmd = args.get("cmd", "") if isinstance(args, dict) else ""
                output = normalize_output(payload.get("output"))
                exit_code = extract_exit_code(output)
                classification = classify_failure(
                    tool_name=tool_name,
                    cmd=cmd,
                    output=output,
                    exit_code=exit_code,
                    session_cwd=session_cwds.get(session_id),
                )
                if classification is not None:
                    category, label = classification
                    if category == "operational":
                        operational_counts[label] += 1
                        operational_sessions[label].add(session_id)
                    else:
                        repo_counts[label] += 1
                        repo_sessions[label].add(session_id)
                    if label.startswith("No such file or directory::"):
                        target = label.split("::", 1)[1]
                        missing_paths[target] += 1
                        missing_path_sessions[target].add(session_id)
                    if label.startswith("ModuleNotFoundError::"):
                        target = label.split("::", 1)[1]
                        missing_modules[target] += 1
                        missing_module_sessions[target].add(session_id)

                    stripped = strip_env_assignments(cmd)
                    probe_type = next(
                        (
                            prefix.strip()
                            for prefix in PATH_PROBE_PREFIXES
                            if stripped.startswith(prefix)
                        ),
                        None,
                    )
                    if probe_type is None and "2>/dev/null" in cmd and any(
                        token in cmd for token in ("sed ", "cat ", "rg ", "find ")
                    ):
                        probe_type = "suppressed-read-only"
                    if probe_type is not None and exit_code not in (None, 0):
                        body = output.split("Output:", 1)[1] if "Output:" in output else output
                        nonempty_lines = [line.strip() for line in body.splitlines() if line.strip()]
                        record = {
                            "session": session_id,
                            "probe_type": probe_type,
                            "cmd": cmd,
                            "exit_code": exit_code,
                            "body": body.strip()[:300],
                        }
                        if any(looks_like_path_listing(line) for line in nonempty_lines):
                            partial_success_probes.append(record)
                        else:
                            discovery_failures.append(record)

                for text in (cmd, output):
                    for match in SKILL_PATH_PATTERN.findall(text):
                        runtime_path = Path(match)
                        if str(runtime_path).startswith(str(codex_home)):
                            continue
                        mapping = f"{runtime_path} => {derive_edit_target(runtime_path, codex_home)}"
                        skill_drift_counts[mapping] += 1
                        skill_drift_sessions[mapping].add(session_id)

        if saw_response_item:
            sessions_with_records += 1

    return {
        "files_scanned": len(files),
        "sessions_with_records": sessions_with_records,
        "top_operational": [
            {
                "label": label,
                "count": count,
                "sessions": len(operational_sessions[label]),
            }
            for label, count in operational_counts.most_common(20)
        ],
        "top_repo_specific": [
            {
                "label": label,
                "count": count,
                "sessions": len(repo_sessions[label]),
            }
            for label, count in repo_counts.most_common(20)
        ],
        "top_missing_paths": [
            {
                "path": path,
                "count": count,
                "sessions": len(missing_path_sessions[path]),
            }
            for path, count in missing_paths.most_common(20)
        ],
        "top_missing_modules": [
            {
                "module": module,
                "count": count,
                "sessions": len(missing_module_sessions[module]),
            }
            for module, count in missing_modules.most_common(20)
        ],
        "discovery_failures": discovery_failures[:50],
        "partial_success_probes": partial_success_probes[:50],
        "skill_path_drift": [
            {
                "mapping": mapping,
                "count": count,
                "sessions": len(skill_drift_sessions[mapping]),
            }
            for mapping, count in skill_drift_counts.most_common(20)
        ],
    }


def main() -> int:
    args = parse_args()
    if not args.file:
        raise SystemExit("manual_review.py requires at least one --file")
    files = [Path(raw).expanduser() for raw in args.file]
    missing = [str(path) for path in files if not path.is_file()]
    if missing:
        raise SystemExit(f"Missing session files: {', '.join(missing)}")
    codex_home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser()
    print(json.dumps(summarize(files, codex_home), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
