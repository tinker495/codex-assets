#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

DOC_IMPACT_MAP: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "src/stowage/dataclasses/stowage_plan/",
        (
            "docs/data-structure/stowage-plan.md",
            "docs/data-structure/calculators.md",
            "docs/anomaly-aggregation-analysis.md",
            "docs/HardConstraints_Constraint_API_Spec.md",
            "docs/Raw_objectiveFunction_Canonical_List.md",
        ),
    ),
    (
        "src/stowage/dataclasses/rotation_history/",
        (
            "docs/data-structure/rotation-history.md",
            "docs/anomaly-aggregation-analysis.md",
            "docs/data-structure-analysis.md",
        ),
    ),
    (
        "src/stowage/dataclasses/vessel_define/",
        (
            "docs/data-structure/cargo.md",
            "docs/data-structure/infrastructure.md",
            "docs/data-structure/stability.md",
        ),
    ),
    (
        "src/tui/",
        (
            "docs/data-structure/stowage-plan.md",
            "docs/data-structure/rotation-history.md",
            "docs/data-structure/infrastructure.md",
        ),
    ),
)

AREA_PREFIXES: tuple[tuple[str, str], ...] = (
    ("docs", "docs/"),
    ("stowage_plan", "src/stowage/dataclasses/stowage_plan/"),
    ("rotation_history", "src/stowage/dataclasses/rotation_history/"),
    ("vessel_define", "src/stowage/dataclasses/vessel_define/"),
    ("tui", "src/tui/"),
    ("tests", "tests/"),
)


@dataclass(frozen=True)
class NumstatRow:
    path: str
    added: int
    deleted: int


def run(cmd: list[str], *, cwd: Path) -> str:
    return subprocess.check_output(cmd, cwd=str(cwd), text=True).strip()


def parse_numstat(text: str) -> list[NumstatRow]:
    rows: list[NumstatRow] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        added, deleted, path = line.split("\t", maxsplit=2)
        if added == "-" or deleted == "-":
            continue
        rows.append(NumstatRow(path=path, added=int(added), deleted=int(deleted)))
    return rows


def area_counts(paths: list[str]) -> dict[str, int]:
    counts = {name: 0 for name, _ in AREA_PREFIXES}
    counts["other"] = 0
    for path in paths:
        matched = False
        for name, prefix in AREA_PREFIXES:
            if path.startswith(prefix):
                counts[name] += 1
                matched = True
                break
        if not matched:
            counts["other"] += 1
    return {k: v for k, v in counts.items() if v > 0}


def _existing_docs(repo: Path, doc_paths: tuple[str, ...]) -> tuple[list[str], list[str]]:
    existing: list[str] = []
    missing: list[str] = []
    for doc_path in doc_paths:
        if (repo / doc_path).exists():
            existing.append(doc_path)
        else:
            missing.append(doc_path)
    return existing, missing


def compute_doc_impact(
    changed_files: list[str],
    *,
    repo: Path,
) -> tuple[list[str], list[dict[str, object]], list[str], list[str]]:
    direct_docs = sorted(
        path
        for path in changed_files
        if path.startswith("docs/") and path.endswith(".md") and (repo / path).exists()
    )
    mapped_docs = set(direct_docs)
    mapped_sources: list[dict[str, object]] = []
    unmapped_code: list[str] = []
    missing_doc_targets: set[str] = set()

    for path in changed_files:
        if path.startswith("docs/"):
            continue
        matched = False
        for prefix, doc_paths in DOC_IMPACT_MAP:
            if path.startswith(prefix):
                matched = True
                existing_docs, missing_docs = _existing_docs(repo, doc_paths)
                mapped_docs.update(existing_docs)
                missing_doc_targets.update(missing_docs)
                mapped_sources.append(
                    {
                        "path": path,
                        "matched_prefix": prefix,
                        "suggested_docs": existing_docs,
                        "missing_doc_targets": missing_docs,
                    }
                )
                break
        if not matched and path.startswith("src/"):
            unmapped_code.append(path)

    return sorted(mapped_docs), mapped_sources, sorted(unmapped_code), sorted(missing_doc_targets)


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect branch diff context for documentation refresh.")
    parser.add_argument("--base", default="main", help="Base branch to compare against.")
    parser.add_argument("--repo", default=".", help="Repository root path.")
    parser.add_argument("--format", default="json", choices=("json", "md"), help="Output format.")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    branch = run(["git", "branch", "--show-current"], cwd=repo)
    name_only = run(["git", "diff", f"{args.base}..HEAD", "--name-only"], cwd=repo)
    numstat_raw = run(["git", "diff", f"{args.base}..HEAD", "--numstat"], cwd=repo)
    files = [line for line in name_only.splitlines() if line.strip()]
    numstats = parse_numstat(numstat_raw)

    suggested_docs, mapped_sources, unmapped_code, missing_doc_targets = compute_doc_impact(files, repo=repo)
    totals = {
        "added": sum(row.added for row in numstats),
        "deleted": sum(row.deleted for row in numstats),
    }
    totals["net"] = totals["added"] - totals["deleted"]

    payload = {
        "branch": branch,
        "base": args.base,
        "changed_files": files,
        "changed_file_count": len(files),
        "area_counts": area_counts(files),
        "numstat": [row.__dict__ for row in numstats],
        "total": totals,
        "suggested_docs": suggested_docs,
        "mapped_sources": mapped_sources,
        "unmapped_src_files": unmapped_code,
        "missing_doc_targets": missing_doc_targets,
    }

    if args.format == "json":
        print(json.dumps(payload, indent=2))
        return

    lines: list[str] = []
    lines.append(f"# Doc Refresh Context: {branch} vs {args.base}")
    lines.append("")
    lines.append(f"Changed files: {len(files)}")
    lines.append(f"Net LOC: +{totals['added']} / -{totals['deleted']} (net {totals['net']:+d})")
    lines.append("")
    lines.append("## Area counts")
    for area, count in payload["area_counts"].items():
        lines.append(f"- {area}: {count}")
    lines.append("")
    lines.append("## Suggested docs")
    if suggested_docs:
        lines.extend(f"- {path}" for path in suggested_docs)
    else:
        lines.append("- (none)")
    lines.append("")
    lines.append("## Missing mapped docs")
    if missing_doc_targets:
        lines.extend(f"- {path}" for path in missing_doc_targets)
    else:
        lines.append("- (none)")
    lines.append("")
    lines.append("## Unmapped src files")
    if unmapped_code:
        lines.extend(f"- {path}" for path in unmapped_code)
    else:
        lines.append("- (none)")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
