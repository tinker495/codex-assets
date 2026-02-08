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


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect branch diff info vs base.")
    parser.add_argument("--base", default="main", help="Base branch to compare against")
    parser.add_argument("--format", default="json", choices=["json", "md"], help="Output format")
    args = parser.parse_args()

    branch = run(["git", "branch", "--show-current"])
    commits = run(["git", "log", f"{args.base}..HEAD", "--oneline"])
    name_only = run(["git", "diff", f"{args.base}..HEAD", "--name-only"])
    numstat_raw = run(["git", "diff", f"{args.base}..HEAD", "--numstat"])
    stat_raw = run(["git", "diff", "--stat", f"{args.base}..HEAD"])

    numstats = parse_numstat(numstat_raw)
    total_added = sum(n.added for n in numstats)
    total_deleted = sum(n.deleted for n in numstats)

    top_add = sorted(numstats, key=lambda n: n.added, reverse=True)[:10]
    top_del = sorted(numstats, key=lambda n: n.deleted, reverse=True)[:10]

    payload = {
        "branch": branch,
        "base": args.base,
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
    lines.append(f"# Branch Brief: {branch} vs {args.base}")
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
