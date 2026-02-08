#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_LIMIT = 4
DEFAULT_SNIPPET_LEN = 220
WHITESPACE_RE = re.compile(r"\s+")


@dataclass
class SessionSummary:
    file_path: str
    mtime_ns: int
    session_id: str | None = None
    started_at: str | None = None
    cwd: str | None = None
    source: str | None = None
    user_messages: list[str] = field(default_factory=list)
    assistant_final_messages: list[str] = field(default_factory=list)

    def timestamp(self) -> str:
        if self.started_at:
            return self.started_at
        dt = datetime.fromtimestamp(self.mtime_ns / 1_000_000_000, tz=timezone.utc)
        return dt.isoformat().replace("+00:00", "Z")

    def last_user_message(self) -> str | None:
        if not self.user_messages:
            return None
        return self.user_messages[-1]

    def last_final_answer(self) -> str | None:
        if not self.assistant_final_messages:
            return None
        return self.assistant_final_messages[-1]


def normalize_space(text: str) -> str:
    return WHITESPACE_RE.sub(" ", text).strip()


def truncate(text: str, max_len: int) -> str:
    compact = normalize_space(text)
    if len(compact) <= max_len:
        return compact
    return f"{compact[: max_len - 3]}..."


def safe_str(value: Any) -> str | None:
    if isinstance(value, str):
        stripped = value.strip()
        return stripped if stripped else None
    return None


def safe_stat_mtime_ns(path: Path) -> int:
    try:
        return path.stat().st_mtime_ns
    except OSError:
        return 0


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            for raw in handle:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    parsed = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                if isinstance(parsed, dict):
                    rows.append(parsed)
    except OSError:
        return []
    return rows


def extract_message_text(payload: dict[str, Any]) -> str | None:
    content = payload.get("content")
    if not isinstance(content, list):
        return None
    chunks: list[str] = []
    for part in content:
        if not isinstance(part, dict):
            continue
        text = safe_str(part.get("text"))
        if text:
            chunks.append(text)
    if not chunks:
        return None
    return "\n".join(chunks)


def parse_session(path: Path) -> SessionSummary:
    summary = SessionSummary(
        file_path=str(path),
        mtime_ns=safe_stat_mtime_ns(path),
    )
    for row in read_jsonl(path):
        row_type = row.get("type")
        payload = row.get("payload")
        if row_type == "session_meta" and isinstance(payload, dict):
            summary.session_id = safe_str(payload.get("id"))
            summary.started_at = safe_str(payload.get("timestamp"))
            summary.cwd = safe_str(payload.get("cwd"))
            summary.source = safe_str(payload.get("source"))
            continue

        if not isinstance(payload, dict):
            continue

        if row_type == "event_msg" and payload.get("type") == "user_message":
            message = safe_str(payload.get("message"))
            if message:
                summary.user_messages.append(message)
            continue

        if row_type == "response_item" and payload.get("type") == "message" and payload.get("role") == "assistant":
            phase = payload.get("phase")
            if phase != "final_answer":
                continue
            message = extract_message_text(payload)
            if message:
                summary.assistant_final_messages.append(message)
    return summary


def discover_session_files(root: Path, include_archived: bool) -> list[Path]:
    candidates: list[Path] = []
    sessions_root = root / "sessions"
    archived_root = root / "archived_sessions"

    if sessions_root.exists():
        candidates.extend(sessions_root.rglob("*.jsonl"))
    if include_archived and archived_root.exists():
        candidates.extend(archived_root.glob("*.jsonl"))

    dedup: dict[str, Path] = {}
    for path in candidates:
        try:
            key = str(path.resolve())
        except OSError:
            key = str(path)
        dedup[key] = path

    return sorted(
        dedup.values(),
        key=safe_stat_mtime_ns,
        reverse=True,
    )


def build_snippet(text: str, pattern: re.Pattern[str], max_len: int) -> str:
    compact = normalize_space(text)
    if len(compact) <= max_len:
        return compact

    match = pattern.search(compact)
    if not match:
        return truncate(compact, max_len)

    half_window = max_len // 2
    start = max(0, match.start() - half_window)
    end = min(len(compact), start + max_len)
    if end - start < max_len:
        start = max(0, end - max_len)
    snippet = compact[start:end]
    if start > 0:
        snippet = f"...{snippet}"
    if end < len(compact):
        snippet = f"{snippet}..."
    return snippet


def collect_matches(session: SessionSummary, pattern: re.Pattern[str], max_len: int) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    for index, text in enumerate(session.user_messages, start=1):
        if pattern.search(text):
            matches.append(
                {
                    "role": "user",
                    "index": index,
                    "snippet": build_snippet(text, pattern, max_len),
                }
            )
    for index, text in enumerate(session.assistant_final_messages, start=1):
        if pattern.search(text):
            matches.append(
                {
                    "role": "assistant_final",
                    "index": index,
                    "snippet": build_snippet(text, pattern, max_len),
                }
            )
    return matches


def render_text(
    sessions: list[SessionSummary],
    query: str | None,
    query_pattern: re.Pattern[str] | None,
    match_only: bool,
    max_matches_per_session: int,
    max_len: int,
) -> str:
    lines: list[str] = []
    lines.append(f"# Recent Codex Sessions (limit={len(sessions)})")
    lines.append("")

    shown = 0
    for session in sessions:
        matches: list[dict[str, Any]] = []
        total_matches = 0
        hidden_matches = 0
        if query_pattern:
            all_matches = collect_matches(session, query_pattern, max_len)
            total_matches = len(all_matches)
            if match_only and not all_matches:
                continue
            if max_matches_per_session > 0:
                matches = all_matches[:max_matches_per_session]
                hidden_matches = max(0, total_matches - len(matches))
            else:
                matches = all_matches

        shown += 1
        lines.append(f"{shown}. {session.timestamp()} | id={session.session_id or '-'}")
        lines.append(f"   cwd: {session.cwd or '-'}")
        lines.append(f"   file: {session.file_path}")
        lines.append(f"   user(last): {truncate(session.last_user_message() or '-', max_len)}")
        lines.append(f"   assistant(final,last): {truncate(session.last_final_answer() or '-', max_len)}")

        if query:
            lines.append(f"   query: {query}")
            if total_matches > 0:
                if hidden_matches > 0:
                    lines.append(
                        f"   matches: {total_matches} (showing {len(matches)}, capped by {max_matches_per_session})"
                    )
                else:
                    lines.append(f"   matches: {total_matches}")
                for match in matches:
                    lines.append(
                        f"   - {match['role']}#{match['index']}: {truncate(match['snippet'], max_len)}"
                    )
            else:
                lines.append("   matches: 0")
        lines.append("")

    if shown == 0:
        if query and match_only:
            lines.append("No matching sessions found for query.")
        else:
            lines.append("No sessions found.")

    return "\n".join(lines).rstrip() + "\n"


def render_json(
    sessions: list[SessionSummary],
    query: str | None,
    query_pattern: re.Pattern[str] | None,
    match_only: bool,
    max_matches_per_session: int,
    max_len: int,
) -> str:
    data: list[dict[str, Any]] = []
    for session in sessions:
        matches: list[dict[str, Any]] = []
        total_matches = 0
        hidden_matches = 0
        if query_pattern:
            all_matches = collect_matches(session, query_pattern, max_len)
            total_matches = len(all_matches)
            if match_only and not all_matches:
                continue
            if max_matches_per_session > 0:
                matches = all_matches[:max_matches_per_session]
                hidden_matches = max(0, total_matches - len(matches))
            else:
                matches = all_matches
        data.append(
            {
                "timestamp": session.timestamp(),
                "session_id": session.session_id,
                "cwd": session.cwd,
                "source": session.source,
                "file_path": session.file_path,
                "last_user_message": truncate(session.last_user_message() or "", max_len),
                "last_assistant_final_answer": truncate(session.last_final_answer() or "", max_len),
                "user_message_count": len(session.user_messages),
                "assistant_final_count": len(session.assistant_final_messages),
                "query": query,
                "matches": matches,
                "match_count_total": total_matches,
                "match_count_shown": len(matches),
                "match_count_hidden": hidden_matches,
            }
        )
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Summarize recent Codex session logs and search reusable context."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))),
        help="Codex home path. Defaults to $CODEX_HOME or ~/.codex.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_LIMIT,
        help=f"Number of recent sessions to inspect (default: {DEFAULT_LIMIT}).",
    )
    parser.add_argument(
        "--query",
        type=str,
        default=None,
        help="Case-insensitive keyword search over user messages and assistant final answers.",
    )
    parser.add_argument(
        "--match-only",
        action="store_true",
        help="Show only sessions with query matches.",
    )
    parser.add_argument(
        "--no-archived",
        action="store_true",
        help="Exclude ~/.codex/archived_sessions.",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format.",
    )
    parser.add_argument(
        "--max-matches-per-session",
        type=int,
        default=0,
        help="Cap query matches shown per session. 0 means no cap.",
    )
    parser.add_argument(
        "--max-snippet-len",
        type=int,
        default=DEFAULT_SNIPPET_LEN,
        help=f"Max snippet length in output (default: {DEFAULT_SNIPPET_LEN}).",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.limit <= 0:
        parser.error("--limit must be greater than 0")
    if args.max_snippet_len <= 20:
        parser.error("--max-snippet-len must be greater than 20")
    if args.max_matches_per_session < 0:
        parser.error("--max-matches-per-session must be 0 or greater")

    include_archived = not args.no_archived
    session_files = discover_session_files(args.root, include_archived=include_archived)
    selected_files = session_files[: args.limit]
    sessions = [parse_session(path) for path in selected_files]

    query_pattern: re.Pattern[str] | None = None
    if args.query:
        query_pattern = re.compile(re.escape(args.query), re.IGNORECASE)

    if args.format == "json":
        output = render_json(
            sessions=sessions,
            query=args.query,
            query_pattern=query_pattern,
            match_only=args.match_only,
            max_matches_per_session=args.max_matches_per_session,
            max_len=args.max_snippet_len,
        )
    else:
        output = render_text(
            sessions=sessions,
            query=args.query,
            query_pattern=query_pattern,
            match_only=args.match_only,
            max_matches_per_session=args.max_matches_per_session,
            max_len=args.max_snippet_len,
        )
    sys.stdout.write(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
