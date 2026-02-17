#!/usr/bin/env python3
"""
Scan recent Codex sessions for operational noise signals and attribute them to
active skill context.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Set


SIGNALS: List[str] = [
    "quick_validate failure",
    "frontmatter/YAML error",
    "PyYAML install/run mention",
    "ModuleNotFoundError: No module named 'yaml'",
    "No such file or directory",
    "missing collect_branch_info.py",
    "missing /shared/code-health",
    "Error: unknown flag: --json",
    "Error: unknown flag: --repo",
    "Error: PRD file not found: prd.json",
    "command not found: grepai",
    "command not found: timeout",
    "command not found: pdfinfo",
    "fatal: not a git repository",
    "Error: could not open a new TTY",
    "jq: parse error",
    "unable to resolve PR from current branch",
    "can't create temp file for here document: operation not permitted",
    "Sandbox(Denied, PermissionError: [Errno 1] Operation not permitted, blocked by policy]",
    "ls: /automations/automatically-create-new-skills",
    "ERROR:xenon:block",
    "ERROR:xenon:module",
    "date: invalid argument 's' for -I",
    "No module named pytest",
    "failed to send request to Ollama",
    "ERROR collecting",
    "ModuleNotFoundError: No module named",
    "write_stdin failed: stdin is closed",
]

BACKTICK_SKILL_PATTERN = re.compile(r"`([a-z0-9-]+)`")
DOLLAR_SKILL_PATTERN = re.compile(r"\$([a-z0-9-]+)")


@dataclass
class SignalStats:
    count: int
    sessions: Set[str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scan recent session noise.")
    parser.add_argument(
        "--since-seconds",
        type=int,
        default=86400,
        help="Lookback window in seconds (default: 86400).",
    )
    parser.add_argument(
        "--file",
        type=str,
        default="",
        help="Optional single JSONL file to scan (overrides time window).",
    )
    return parser.parse_args()


def get_codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser()


def discover_skill_names(codex_home: Path) -> Set[str]:
    skills_root = codex_home / "skills"
    names: Set[str] = set()
    if not skills_root.is_dir():
        return names
    for skill_md in skills_root.rglob("SKILL.md"):
        names.add(skill_md.parent.name)
    return names


def modified_skills_7d(codex_home: Path, now_ts: float) -> Set[str]:
    skills_root = codex_home / "skills"
    modified: Set[str] = set()
    if not skills_root.is_dir():
        return modified
    cutoff = now_ts - 7 * 24 * 60 * 60
    for skill_md in skills_root.rglob("SKILL.md"):
        try:
            if skill_md.stat().st_mtime >= cutoff:
                modified.add(skill_md.parent.name)
        except FileNotFoundError:
            continue
    return modified


def list_session_files(codex_home: Path, since_seconds: int, single_file: str) -> List[Path]:
    if single_file:
        path = Path(single_file).expanduser()
        if path.is_file():
            return [path]
        raise FileNotFoundError(f"Session file not found: {path}")

    now_ts = time.time()
    cutoff = now_ts - since_seconds
    files: List[Path] = []
    sessions_root = codex_home / "sessions"
    archived_root = codex_home / "archived_sessions"

    if sessions_root.is_dir():
        for path in sessions_root.rglob("*.jsonl"):
            try:
                if path.stat().st_mtime >= cutoff:
                    files.append(path)
            except FileNotFoundError:
                continue
    if archived_root.is_dir():
        for path in archived_root.glob("*.jsonl"):
            try:
                if path.stat().st_mtime >= cutoff:
                    files.append(path)
            except FileNotFoundError:
                continue

    return sorted(set(files))


def extract_message_text(payload: Dict) -> str:
    content = payload.get("content")
    chunks: List[str] = []
    if isinstance(content, str):
        chunks.append(content)
    elif isinstance(content, list):
        for item in content:
            if isinstance(item, dict) and isinstance(item.get("text"), str):
                chunks.append(item["text"])
    message_value = payload.get("message")
    if isinstance(message_value, str):
        chunks.append(message_value)
    return " ".join(chunks)


def should_count_no_such_file(output: str) -> bool:
    code_match = re.search(r"Process exited with code (\d+)", output)
    if code_match:
        return int(code_match.group(1)) != 0
    if re.search(r"\bexit code\s*([12])\b", output, flags=re.IGNORECASE):
        return True
    return False


def extract_skills_from_text(text: str, known_skills: Set[str]) -> Set[str]:
    found: Set[str] = set()
    for token in BACKTICK_SKILL_PATTERN.findall(text):
        if token in known_skills:
            found.add(token)
    for token in DOLLAR_SKILL_PATTERN.findall(text):
        if token in known_skills:
            found.add(token)
    return found


def ensure_signal_record(stats: Dict[str, SignalStats], signal: str) -> SignalStats:
    if signal not in stats:
        stats[signal] = SignalStats(count=0, sessions=set())
    return stats[signal]


def main() -> int:
    args = parse_args()
    codex_home = get_codex_home()
    now_ts = time.time()
    known_skills = discover_skill_names(codex_home)
    session_files = list_session_files(codex_home, args.since_seconds, args.file)

    signal_stats: Dict[str, SignalStats] = {}
    skill_signal_counts: Dict[str, Dict[str, SignalStats]] = defaultdict(dict)
    skill_total_counts: Dict[str, int] = defaultdict(int)
    skill_sessions: Dict[str, Set[str]] = defaultdict(set)
    used_skills_24h: Set[str] = set()

    for session_file in session_files:
        session_id = session_file.name
        active_skills: Set[str] = set()
        try:
            with session_file.open("r", encoding="utf-8") as handle:
                for line in handle:
                    raw = line.strip()
                    if not raw:
                        continue
                    try:
                        record = json.loads(raw)
                    except json.JSONDecodeError:
                        continue

                    if record.get("type") != "response_item":
                        continue
                    payload = record.get("payload")
                    if not isinstance(payload, dict):
                        continue
                    payload_type = payload.get("type")

                    if payload_type == "message":
                        role = payload.get("role")
                        if role not in {"assistant", "user"}:
                            continue
                        text = extract_message_text(payload)
                        if not text:
                            continue
                        found = extract_skills_from_text(text, known_skills)
                        if role == "user":
                            if found:
                                active_skills.update(found)
                                used_skills_24h.update(found)
                        else:
                            if found:
                                active_skills = set(found)
                                used_skills_24h.update(found)
                        continue

                    if payload_type != "function_call_output":
                        continue

                    output = payload.get("output")
                    if not isinstance(output, str):
                        continue

                    for signal in SIGNALS:
                        occurrences = output.count(signal)
                        if occurrences <= 0:
                            continue
                        if signal == "No such file or directory" and not should_count_no_such_file(output):
                            continue

                        signal_record = ensure_signal_record(signal_stats, signal)
                        signal_record.count += occurrences
                        signal_record.sessions.add(session_id)

                        attributed_skills: Iterable[str]
                        if active_skills:
                            attributed_skills = active_skills
                        else:
                            attributed_skills = {"__unattributed__"}
                        for skill_name in attributed_skills:
                            skill_total_counts[skill_name] += occurrences
                            skill_sessions[skill_name].add(session_id)
                            skill_signal_record = ensure_signal_record(
                                skill_signal_counts[skill_name], signal
                            )
                            skill_signal_record.count += occurrences
                            skill_signal_record.sessions.add(session_id)
        except FileNotFoundError:
            continue

    high_signals = sorted(
        signal
        for signal, stats in signal_stats.items()
        if stats.count >= 2 or len(stats.sessions) >= 2
    )

    high_noise_skills_before: List[str] = []
    for skill_name, per_signal in skill_signal_counts.items():
        if skill_name == "__unattributed__":
            continue
        for signal in high_signals:
            stats = per_signal.get(signal)
            if stats and stats.count > 0:
                high_noise_skills_before.append(skill_name)
                break
    high_noise_skills_before = sorted(set(high_noise_skills_before))

    modified_7d = modified_skills_7d(codex_home, now_ts)
    recently_touched_union = sorted(used_skills_24h | modified_7d)
    high_noise_skills_after = [
        skill for skill in high_noise_skills_before if skill in set(recently_touched_union)
    ]

    signals_output = {
        signal: {
            "count": stats.count,
            "sessions": len(stats.sessions),
        }
        for signal, stats in sorted(signal_stats.items(), key=lambda item: item[0])
    }

    skills_output = {}
    for skill_name in sorted(skill_total_counts.keys()):
        if skill_name == "__unattributed__":
            continue
        per_signal_output = {}
        for signal, stats in sorted(skill_signal_counts[skill_name].items(), key=lambda item: item[0]):
            per_signal_output[signal] = {
                "count": stats.count,
                "sessions": len(stats.sessions),
            }
        skills_output[skill_name] = {
            "count": skill_total_counts[skill_name],
            "sessions": len(skill_sessions[skill_name]),
            "signals": per_signal_output,
        }

    result = {
        "window_seconds": args.since_seconds,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_ts)),
        "files_scanned": len(session_files),
        "signals": signals_output,
        "skills": skills_output,
        "high_signals": high_signals,
        "high_noise_skills": {
            "before_recently_touched": high_noise_skills_before,
            "after_recently_touched": high_noise_skills_after,
        },
        "recently_touched": {
            "used_24h": sorted(used_skills_24h),
            "modified_7d": sorted(modified_7d),
            "union": recently_touched_union,
        },
    }
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
