#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass


@dataclass
class Numstat:
    path: str
    added: int
    deleted: int


def run(cmd: list[str], cwd: str | None = None) -> str:
    return subprocess.check_output(cmd, cwd=cwd, text=True).strip()


def maybe_run(cmd: list[str], cwd: str | None = None) -> str | None:
    try:
        return run(cmd, cwd=cwd)
    except subprocess.CalledProcessError:
        return None


def parse_numstat(text: str) -> list[Numstat]:
    stats: list[Numstat] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        added, deleted, path = line.split("\t")
        if added == "-" or deleted == "-":
            continue
        stats.append(Numstat(path=path, added=int(added), deleted=int(deleted)))
    return stats


def default_base_branch() -> str:
    symbolic = maybe_run(["git", "symbolic-ref", "refs/remotes/origin/HEAD"])
    if symbolic and symbolic.startswith("refs/remotes/origin/"):
        return symbolic.removeprefix("refs/remotes/origin/")
    for candidate in ("origin/main", "main", "origin/master", "master"):
        if maybe_run(["git", "rev-parse", "--verify", candidate]):
            return candidate
    return "HEAD~1"


def fork_point(base: str) -> str:
    return (
        maybe_run(["git", "merge-base", "--fork-point", base, "HEAD"])
        or maybe_run(["git", "merge-base", base, "HEAD"])
        or base
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect branch diff info from the branch fork point.")
    parser.add_argument(
        "--base",
        default=None,
        help="Upstream branch used only to resolve the fork point; defaults to origin/HEAD, then main/master.",
    )
    parser.add_argument("--format", default="json", choices=["json", "md"], help="Output format")
    args = parser.parse_args()

    base = args.base or default_base_branch()
    branch = run(["git", "branch", "--show-current"])
    fork = fork_point(base)
    commit_range = f"{fork}..HEAD"
    diff_range = f"{fork}..HEAD"
    commits = run(["git", "log", commit_range, "--oneline"])
    name_only = run(["git", "diff", diff_range, "--name-only"])
    numstat_raw = run(["git", "diff", diff_range, "--numstat"])
    stat_raw = run(["git", "diff", "--stat", diff_range])

    numstats = parse_numstat(numstat_raw)
    total_added = sum(n.added for n in numstats)
    total_deleted = sum(n.deleted for n in numstats)

    top_add = sorted(numstats, key=lambda n: n.added, reverse=True)[:10]
    top_del = sorted(numstats, key=lambda n: n.deleted, reverse=True)[:10]

    payload = {
        "branch": branch,
        "base": base,
        "fork_point": fork,
        "compare_mode": {
            "commit_log": commit_range,
            "files": diff_range,
            "numstat": diff_range,
            "diff_stat": diff_range,
        },
        "commit_log": commits.splitlines() if commits else [],
        "files": name_only.splitlines() if name_only else [],
        "numstat": [n.__dict__ for n in numstats],
        "total": {"added": total_added, "deleted": total_deleted, "net": total_added - total_deleted},
        "top_additions": [n.__dict__ for n in top_add],
        "top_deletions": [n.__dict__ for n in top_del],
        "diff_stat": stat_raw,
    }

    if args.format == "json":
        print(json.dumps(payload, indent=2))
        return

    # Markdown output
    lines = []
    lines.append(f"# Branch Brief: {branch} since fork point")
    lines.append("")
    lines.append(f"Base branch: {base}")
    lines.append(f"Fork point: {fork}")
    lines.append(f"Compare modes: commits={commit_range}, files/loc={diff_range}")
    lines.append("")
    lines.append(f"Total: +{total_added} / -{total_deleted} (net {total_added - total_deleted:+d})")
    lines.append("")
    lines.append("## Commits")
    lines.extend([f"- {c}" for c in payload["commit_log"]])
    lines.append("")
    lines.append("## Files")
    lines.extend([f"- {f}" for f in payload["files"]])
    lines.append("")
    lines.append("## Top Additions")
    lines.extend([f"- {n['path']}: +{n['added']} / -{n['deleted']}" for n in payload["top_additions"]])
    lines.append("")
    lines.append("## Top Deletions")
    lines.extend([f"- {n['path']}: +{n['added']} / -{n['deleted']}" for n in payload["top_deletions"]])

    print("\n".join(lines))


if __name__ == "__main__":
    main()
