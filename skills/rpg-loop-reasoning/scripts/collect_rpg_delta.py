#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

TEST_RE = re.compile(r"(^|/)(tests?|__tests__)/|\.test\.|\.spec\.")


def run(cmd: list[str], cwd: Path) -> str:
    return subprocess.check_output(cmd, cwd=str(cwd), text=True).strip()


def parse_name_status(text: str) -> dict[str, list[dict[str, str]]]:
    result: dict[str, list[dict[str, str]]] = {
        "added": [],
        "modified": [],
        "deleted": [],
        "renamed": [],
    }
    for line in text.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        status = parts[0]
        if status == "A" and len(parts) >= 2:
            result["added"].append({"path": parts[1]})
        elif status == "M" and len(parts) >= 2:
            result["modified"].append({"path": parts[1]})
        elif status == "D" and len(parts) >= 2:
            result["deleted"].append({"path": parts[1]})
        elif status.startswith("R") and len(parts) >= 3:
            result["renamed"].append({"from": parts[1], "to": parts[2]})
        elif len(parts) >= 2:
            # Treat unknown statuses as modified to stay conservative.
            result["modified"].append({"path": parts[1]})
    return result


def parse_numstat(text: str) -> tuple[int, int, int, int]:
    non_test_add = non_test_del = test_add = test_del = 0
    for line in text.splitlines():
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        add_raw, del_raw = parts[0], parts[1]
        if not add_raw.isdigit() or not del_raw.isdigit():
            continue
        path = parts[-1]
        add_v, del_v = int(add_raw), int(del_raw)
        if TEST_RE.search(path):
            test_add += add_v
            test_del += del_v
        else:
            non_test_add += add_v
            non_test_del += del_v
    return non_test_add, non_test_del, test_add, test_del


def to_markdown(payload: dict[str, object]) -> str:
    counts = payload["counts"]
    totals = payload["totals"]
    lines: list[str] = []
    lines.append(f"# RPG Delta: {payload['branch']} vs {payload['base']}")
    lines.append("")
    lines.append("## Change Counts")
    lines.append(f"- added: {counts['added']}")
    lines.append(f"- modified: {counts['modified']}")
    lines.append(f"- deleted: {counts['deleted']}")
    lines.append(f"- renamed: {counts['renamed']}")
    lines.append("")
    lines.append("## Diff Totals")
    lines.append(
        f"- non-test: +{totals['non_test_added']} / -{totals['non_test_deleted']} "
        f"(net {totals['non_test_net']:+d})"
    )
    lines.append(
        f"- test: +{totals['test_added']} / -{totals['test_deleted']} "
        f"(net {totals['test_net']:+d})"
    )
    lines.append("")
    lines.append("## Renames")
    renamed = payload["changes"]["renamed"]
    if renamed:
        for item in renamed:
            lines.append(f"- {item['from']} -> {item['to']}")
    else:
        lines.append("- (none)")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect branch delta for incremental RPG evolution.")
    parser.add_argument("--repo", default=".", help="Repository root.")
    parser.add_argument("--base", default="main", help="Base branch.")
    parser.add_argument("--format", choices=("json", "md"), default="json")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    branch = run(["git", "branch", "--show-current"], cwd=repo)
    name_status = run(["git", "diff", f"{args.base}..HEAD", "--name-status"], cwd=repo)
    numstat = run(["git", "diff", f"{args.base}..HEAD", "--numstat"], cwd=repo)

    changes = parse_name_status(name_status)
    non_test_add, non_test_del, test_add, test_del = parse_numstat(numstat)

    payload: dict[str, object] = {
        "branch": branch,
        "base": args.base,
        "changes": changes,
        "counts": {
            "added": len(changes["added"]),
            "modified": len(changes["modified"]),
            "deleted": len(changes["deleted"]),
            "renamed": len(changes["renamed"]),
        },
        "totals": {
            "non_test_added": non_test_add,
            "non_test_deleted": non_test_del,
            "non_test_net": non_test_add - non_test_del,
            "test_added": test_add,
            "test_deleted": test_del,
            "test_net": test_add - test_del,
        },
    }

    if args.format == "json":
        print(json.dumps(payload, indent=2))
    else:
        print(to_markdown(payload))


if __name__ == "__main__":
    main()
