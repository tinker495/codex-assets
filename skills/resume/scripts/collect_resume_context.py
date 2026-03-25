#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class GitFileStat:
    path: str
    added: int
    deleted: int

    @property
    def net(self) -> int:
        return self.added - self.deleted

    @property
    def total(self) -> int:
        return self.added + self.deleted

    @property
    def area(self) -> str:
        parts = Path(self.path).parts
        if len(parts) >= 3:
            return "/".join(parts[:3])
        if len(parts) >= 2:
            return "/".join(parts[:2])
        return self.path


def run(cmd: list[str], cwd: Path, check: bool = True) -> str:
    completed = subprocess.run(
        cmd,
        cwd=str(cwd),
        check=False,
        capture_output=True,
        text=True,
    )
    if check and completed.returncode != 0:
        stderr = completed.stderr.strip()
        raise RuntimeError(f"command failed ({completed.returncode}): {' '.join(cmd)}\n{stderr}")
    return completed.stdout.strip()


def maybe_run(cmd: list[str], cwd: Path) -> str | None:
    try:
        return run(cmd, cwd, check=True)
    except Exception:
        return None


def parse_numstat(output: str) -> list[GitFileStat]:
    stats: list[GitFileStat] = []
    for line in output.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t", 2)
        if len(parts) != 3:
            continue
        added_s, deleted_s, path = parts
        if added_s == "-" or deleted_s == "-":
            added = 0
            deleted = 0
        else:
            added = int(added_s)
            deleted = int(deleted_s)
        stats.append(GitFileStat(path=path, added=added, deleted=deleted))
    return stats


def summarize_stats(stats: list[GitFileStat]) -> dict[str, Any]:
    by_area: Counter[str] = Counter()
    by_test = {"test": 0, "runtime": 0}
    for stat in stats:
        by_area[stat.area] += stat.total
        if stat.path.startswith("tests/"):
            by_test["test"] += stat.total
        else:
            by_test["runtime"] += stat.total
    return {
        "files": len(stats),
        "added": sum(item.added for item in stats),
        "deleted": sum(item.deleted for item in stats),
        "net": sum(item.net for item in stats),
        "areas": [
            {"area": area, "weight": weight}
            for area, weight in by_area.most_common(6)
        ],
        "test_runtime_weight": by_test,
        "largest_files": [
            {
                "path": item.path,
                "added": item.added,
                "deleted": item.deleted,
                "net": item.net,
                "total": item.total,
            }
            for item in sorted(stats, key=lambda item: (item.total, item.added), reverse=True)[:8]
        ],
    }


def parse_porcelain(output: str) -> dict[str, list[str]]:
    parsed = {"staged": [], "unstaged": [], "untracked": [], "conflicted": []}
    for line in output.splitlines():
        if not line:
            continue
        status = line[:2]
        path = line[3:]
        if status == "??":
            parsed["untracked"].append(path)
            continue
        x, y = status[0], status[1]
        if x == "U" or y == "U" or status in {"AA", "DD"}:
            parsed["conflicted"].append(path)
        if x != " ":
            parsed["staged"].append(path)
        if y != " ":
            parsed["unstaged"].append(path)
    return parsed


def detect_base_branch(cwd: Path) -> str:
    symbolic = maybe_run(["git", "symbolic-ref", "refs/remotes/origin/HEAD"], cwd)
    if symbolic and symbolic.startswith("refs/remotes/origin/"):
        return symbolic.removeprefix("refs/remotes/origin/")
    for candidate in ("main", "master"):
        ref = maybe_run(["git", "rev-parse", "--verify", candidate], cwd)
        if ref:
            return candidate
    return "HEAD~1"


def load_json(path: Path) -> Any | None:
    if not path.exists() or not path.is_file():
        return None
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def list_recent_files(root: Path, pattern: str, limit: int) -> list[dict[str, Any]]:
    files = sorted(root.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    results: list[dict[str, Any]] = []
    for file in files[:limit]:
        try:
            preview = file.read_text().strip().splitlines()[:6]
        except Exception:
            preview = []
        results.append(
            {
                "path": str(file.relative_to(root.parent if root.name == ".omx" else root)),
                "modified_at": datetime.fromtimestamp(file.stat().st_mtime, tz=timezone.utc).isoformat(),
                "preview": preview,
            }
        )
    return results


def tail_working_memory(notepad: Path, limit: int) -> list[str]:
    if not notepad.exists():
        return []
    text = notepad.read_text()
    marker = "## WORKING MEMORY"
    if marker in text:
        text = text.split(marker, 1)[1]
    entries = [line.strip() for line in text.splitlines() if line.strip()]
    return entries[-limit:]


def relative_to_repo(path: Path, repo_root: Path) -> str:
    try:
        return str(path.relative_to(repo_root))
    except ValueError:
        return str(path)


def collect(repo_root: Path, max_notes: int, max_artifacts: int) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    if maybe_run(["git", "rev-parse", "--is-inside-work-tree"], repo_root) != "true":
        raise RuntimeError(f"not a git work tree: {repo_root}")

    branch = run(["git", "branch", "--show-current"], repo_root)
    head = run(["git", "rev-parse", "HEAD"], repo_root)
    head_short = run(["git", "rev-parse", "--short", "HEAD"], repo_root)
    base_branch = detect_base_branch(repo_root)
    ahead_behind = maybe_run(
        ["git", "rev-list", "--left-right", "--count", f"{base_branch}...HEAD"],
        repo_root,
    )
    behind = ahead = 0
    if ahead_behind:
        left, right = ahead_behind.split()
        behind, ahead = int(left), int(right)

    porcelain = parse_porcelain(run(["git", "status", "--short"], repo_root))
    staged_stats = parse_numstat(run(["git", "diff", "--cached", "--numstat"], repo_root))
    unstaged_stats = parse_numstat(run(["git", "diff", "--numstat"], repo_root))
    branch_stats = parse_numstat(
        maybe_run(["git", "diff", "--numstat", f"{base_branch}...HEAD"], repo_root) or ""
    )
    head_commit_files = parse_numstat(
        maybe_run(["git", "show", "--numstat", "--format=", "HEAD"], repo_root) or ""
    )

    recent_commits_raw = run(
        ["git", "log", "--oneline", "--decorate", "-n", "8"],
        repo_root,
    )
    recent_commits = [line for line in recent_commits_raw.splitlines() if line.strip()]

    latest_subject = maybe_run(["git", "show", "-s", "--format=%s", "HEAD"], repo_root) or ""
    latest_body = maybe_run(["git", "show", "-s", "--format=%b", "HEAD"], repo_root) or ""

    omx_root = repo_root / ".omx"
    state_dir = omx_root / "state"
    plans_dir = omx_root / "plans"
    active_plans_path = plans_dir / "ACTIVE.md"
    pr_status_path = omx_root / "pr-workflow-status.json"
    session_path = state_dir / "session.json"
    skill_state_path = state_dir / "skill-active-state.json"

    session_state = load_json(session_path) or {}
    skill_state = load_json(skill_state_path) or {}
    pr_status = load_json(pr_status_path) or {}

    active_state_files: list[dict[str, Any]] = []
    if state_dir.exists():
        candidates = sorted(
            [p for p in state_dir.glob("*.json") if p.is_file()],
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        for file in candidates[:10]:
            data = load_json(file)
            if not isinstance(data, dict):
                continue
            active = bool(data.get("active"))
            interesting = active or file.name in {
                "session.json",
                "skill-active-state.json",
                "ralph-state.json",
                "ralplan-state.json",
            }
            if not interesting:
                continue
            active_state_files.append(
                {
                    "path": relative_to_repo(file, repo_root),
                    "active": active,
                    "keys": sorted(list(data.keys()))[:12],
                    "summary": {
                        key: data[key]
                        for key in (
                            "active",
                            "skill",
                            "phase",
                            "current_phase",
                            "task_description",
                            "iteration",
                            "updated_at",
                            "last_turn_at",
                        )
                        if key in data
                    },
                }
            )

    active_plans_text = active_plans_path.read_text().strip().splitlines() if active_plans_path.exists() else []

    working_memory = tail_working_memory(omx_root / "notepad.md", max_notes)
    recent_contexts = []
    recent_plans = []
    if omx_root.exists():
        recent_contexts = list_recent_files(omx_root, "context/*.md", max_artifacts)
        recent_plans = list_recent_files(omx_root, "plans/*.md", max_artifacts)

    staged_summary = summarize_stats(staged_stats)
    unstaged_summary = summarize_stats(unstaged_stats)
    branch_summary = summarize_stats(branch_stats)
    head_commit_summary = summarize_stats(head_commit_files)

    changed_runtime = [item.path for item in staged_stats + unstaged_stats if not item.path.startswith("tests/")]
    changed_tests = [item.path for item in staged_stats + unstaged_stats if item.path.startswith("tests/")]

    risks: list[str] = []
    if porcelain["conflicted"]:
        risks.append("Working tree has merge conflicts; resolve before trusting deeper analysis.")
    if staged_summary["files"] and unstaged_summary["files"]:
        risks.append("Both staged and unstaged edits exist; the commit boundary is mixed.")
    if staged_summary["files"] and not changed_tests:
        risks.append("Runtime edits are staged without paired test edits in the working tree.")
    if staged_summary["added"] + unstaged_summary["added"] > 800:
        risks.append("The in-flight change set is large; summarize before editing further.")
    if not staged_summary["files"] and not unstaged_summary["files"] and ahead > 0:
        risks.append("Working tree is clean; continuation likely depends on the latest local commit(s), not unstaged work.")
    if skill_state.get("active"):
        risks.append(
            f"OMX skill state is still marked active ({skill_state.get('skill')}); check whether that mode should be resumed or cleared."
        )

    if staged_summary["files"] or unstaged_summary["files"] or porcelain["untracked"]:
        focus_mode = "working-tree"
    elif ahead > 0:
        focus_mode = "latest-commit"
    else:
        focus_mode = "branch-context"

    inspection_order: list[str] = []
    for item in staged_summary["largest_files"][:3]:
        inspection_order.append(item["path"])
    for item in unstaged_summary["largest_files"][:2]:
        if item["path"] not in inspection_order:
            inspection_order.append(item["path"])
    for path in changed_tests[:2]:
        if path not in inspection_order:
            inspection_order.append(path)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(repo_root),
        "branch": branch,
        "base_branch": base_branch,
        "head": head,
        "head_short": head_short,
        "ahead_of_base": ahead,
        "behind_base": behind,
        "focus_mode": focus_mode,
        "working_tree": {
            "staged_paths": porcelain["staged"],
            "unstaged_paths": porcelain["unstaged"],
            "untracked_paths": porcelain["untracked"],
            "conflicted_paths": porcelain["conflicted"],
            "staged_summary": staged_summary,
            "unstaged_summary": unstaged_summary,
        },
        "branch_summary": branch_summary,
        "head_commit": {
            "subject": latest_subject,
            "body": latest_body.strip(),
            "summary": head_commit_summary,
            "recent_commits": recent_commits,
        },
        "omx": {
            "session": session_state,
            "skill_state": skill_state,
            "active_state_files": active_state_files,
            "active_plans_excerpt": active_plans_text,
            "working_memory_tail": working_memory,
            "recent_context_files": recent_contexts,
            "recent_plan_files": recent_plans,
            "pr_workflow_status": {
                key: pr_status.get(key)
                for key in ("status", "phase", "message", "base", "updated_at", "artifacts_dir")
                if key in pr_status
            },
        },
        "changed_runtime_files": changed_runtime,
        "changed_test_files": changed_tests,
        "risks": risks,
        "inspection_order": inspection_order,
    }


def bullet_list(items: list[str], indent: str = "- ") -> str:
    if not items:
        return f"{indent}(none)"
    return "\n".join(f"{indent}{item}" for item in items)


def render_markdown(data: dict[str, Any]) -> str:
    wt = data["working_tree"]
    omx = data["omx"]
    lines: list[str] = []
    lines.append("# Commit Resume Snapshot")
    lines.append("")
    lines.append("## Core State")
    lines.append(f"- Repo: `{data['repo_root']}`")
    lines.append(f"- Branch: `{data['branch']}` vs base `{data['base_branch']}`")
    lines.append(
        f"- HEAD: `{data['head_short']}` | ahead {data['ahead_of_base']} / behind {data['behind_base']}"
    )
    lines.append(f"- Focus mode: `{data['focus_mode']}`")
    lines.append(
        f"- Working tree: staged {len(wt['staged_paths'])}, unstaged {len(wt['unstaged_paths'])}, untracked {len(wt['untracked_paths'])}, conflicted {len(wt['conflicted_paths'])}"
    )
    lines.append("")
    lines.append("## In-Flight Change Summary")
    lines.append(
        f"- Staged diff: {wt['staged_summary']['files']} files, +{wt['staged_summary']['added']}/-{wt['staged_summary']['deleted']} (net {wt['staged_summary']['net']:+d})"
    )
    lines.append(
        f"- Unstaged diff: {wt['unstaged_summary']['files']} files, +{wt['unstaged_summary']['added']}/-{wt['unstaged_summary']['deleted']} (net {wt['unstaged_summary']['net']:+d})"
    )
    if data["branch_summary"]["files"]:
        lines.append(
            f"- Branch vs base: {data['branch_summary']['files']} files, +{data['branch_summary']['added']}/-{data['branch_summary']['deleted']} (net {data['branch_summary']['net']:+d})"
        )
    lines.append("- Dominant staged areas:")
    staged_areas = [f"{item['area']} ({item['weight']})" for item in wt['staged_summary']['areas']]
    lines.append(bullet_list(staged_areas, "  - "))
    lines.append("- Largest staged files:")
    staged_files = [
        f"{item['path']} (+{item['added']}/-{item['deleted']})"
        for item in wt['staged_summary']['largest_files']
    ]
    lines.append(bullet_list(staged_files, "  - "))
    lines.append("")
    lines.append("## Commit Anchor")
    lines.append(f"- Latest commit: {data['head_commit']['subject'] or '(no subject)'}")
    if data['head_commit']['body']:
        first_line = data['head_commit']['body'].splitlines()[0]
        lines.append(f"- Commit body hint: {first_line}")
    lines.append("- Recent commits:")
    lines.append(bullet_list(data['head_commit']['recent_commits'], "  - "))
    lines.append("")
    lines.append("## OMX Resume Signals")
    session = omx.get("session", {})
    if session:
        lines.append(
            f"- Current session: `{session.get('session_id', '?')}` started {session.get('started_at', '?')}"
        )
    skill_state = omx.get("skill_state", {})
    if skill_state:
        lines.append(
            f"- Active skill flag: active={skill_state.get('active')} skill={skill_state.get('skill')} phase={skill_state.get('phase')}"
        )
    lines.append("- Active plans excerpt:")
    lines.append(bullet_list(omx.get("active_plans_excerpt", []), "  - "))
    lines.append("- Working memory tail:")
    lines.append(bullet_list(omx.get("working_memory_tail", []), "  - "))
    state_summaries = []
    for item in omx.get("active_state_files", []):
        summary = item.get("summary", {})
        compact = ", ".join(f"{k}={v}" for k, v in summary.items())
        state_summaries.append(f"{item['path']}: {compact}" if compact else item['path'])
    lines.append("- Active/interesting state files:")
    lines.append(bullet_list(state_summaries, "  - "))
    recent_contexts = [item["path"] for item in omx.get("recent_context_files", [])]
    lines.append("- Recent context files:")
    lines.append(bullet_list(recent_contexts, "  - "))
    recent_plans = [item["path"] for item in omx.get("recent_plan_files", [])]
    lines.append("- Recent plan files:")
    lines.append(bullet_list(recent_plans, "  - "))
    pr_status = omx.get("pr_workflow_status", {})
    if pr_status:
        compact = ", ".join(f"{k}={v}" for k, v in pr_status.items())
        lines.append(f"- PR workflow status: {compact}")
    lines.append("")
    lines.append("## Risks")
    lines.append(bullet_list(data.get("risks", []), "- "))
    lines.append("")
    lines.append("## Suggested Inspection Order")
    lines.append(bullet_list(data.get("inspection_order", []), "- "))
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect current repo + OMX resume context")
    parser.add_argument("--repo-root", default=".", help="Repository root to inspect")
    parser.add_argument("--format", choices=("json", "markdown"), default="markdown")
    parser.add_argument("--max-notes", type=int, default=6)
    parser.add_argument("--max-artifacts", type=int, default=4)
    args = parser.parse_args()

    try:
        data = collect(Path(args.repo_root), max_notes=args.max_notes, max_artifacts=args.max_artifacts)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.format == "json":
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(render_markdown(data))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
