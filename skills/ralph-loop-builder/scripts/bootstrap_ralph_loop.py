#!/usr/bin/env python3
"""Bootstrap a purpose-fit Ralph workspace under .codex/."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path


CORE_FILES = ("README.md", "CODEX.md", "prd.json", "progress.txt", "ralph.sh")


def slugify(value: str) -> str:
    lowered = value.strip().lower()
    lowered = re.sub(r"[^a-z0-9]+", "-", lowered)
    lowered = re.sub(r"-{2,}", "-", lowered).strip("-")
    return lowered


def derive_branch_name(base_ref: str) -> str:
    trimmed = base_ref.strip()
    if not trimmed:
        return "main"
    if "/" not in trimmed:
        return trimmed
    return trimmed.rsplit("/", maxsplit=1)[-1]


def build_audit_stories(workspace: str, purpose: str) -> list[dict]:
    entries = [
        ("AUDIT-001", "Scope + Baseline Gate Snapshot", "01-baseline-gates.md"),
        ("AUDIT-002", "Delegation Ownership Clusters", "02-delegation-clusters.md"),
        ("AUDIT-003", "High-Churn Module Focus Review", "03-high-churn-review.md"),
        ("AUDIT-004", "Cross-Module Consolidation Candidates", "04-cross-module-candidates.md"),
        ("AUDIT-005", "One-Cycle Dry-Run Verdict", "05-dry-run-verdict.md"),
        ("AUDIT-006", "Guardrails and Unknowns", "06-guardrail-unknowns.md"),
        ("AUDIT-007", "Final Backlog Index", "07-backlog-index.md"),
    ]
    stories: list[dict] = []
    for idx, (story_id, title, report_name) in enumerate(entries, start=1):
        stories.append(
            {
                "id": story_id,
                "title": title,
                "description": f"{purpose} 관점의 audit step {idx}.",
                "acceptanceCriteria": [
                    f"Created .codex/{workspace}/audit/{report_name} with ALL findings",
                    "Report cites gate evidence and explicit reason codes",
                    "Report keeps xenon non-regression and diff/LOC direction explicit",
                ],
                "priority": idx,
                "passes": False,
                "notes": (
                    "DO NOT FIX ANYTHING. Read-only audit only. "
                    f"Objective: {purpose}. Output only markdown content for "
                    f".codex/{workspace}/audit/{report_name}."
                ),
            }
        )
    return stories


def build_delivery_stories(workspace: str, purpose: str) -> list[dict]:
    entries = [
        ("US-001", "Baseline + Story Scope Definition", "01-scope-baseline.md"),
        ("US-002", "Primary Implementation Slice", "02-primary-slice.md"),
        ("US-003", "Secondary Integration Slice", "03-integration-slice.md"),
        ("US-004", "Quality Gate Stabilization", "04-quality-gates.md"),
        ("US-005", "Final Validation and Wrap-Up", "05-final-wrap-up.md"),
    ]
    stories: list[dict] = []
    for idx, (story_id, title, report_name) in enumerate(entries, start=1):
        stories.append(
            {
                "id": story_id,
                "title": title,
                "description": f"{purpose} delivery step {idx}.",
                "acceptanceCriteria": [
                    f"Created .codex/{workspace}/audit/{report_name} with run evidence",
                    "Implementation status and remaining risks are explicit",
                    "Gate checks and next action are documented",
                ],
                "priority": idx,
                "passes": False,
                "notes": (
                    f"Implement only story scope for {story_id}. "
                    "Keep verification evidence explicit in report output."
                ),
            }
        )
    return stories


def build_prd(workspace: str, purpose: str, mode: str, base_ref: str) -> dict:
    if mode == "audit":
        stories = build_audit_stories(workspace, purpose)
        description = (
            "Read-only audit loop for delegation integrity, xenon safety, and "
            "branch diff/LOC reduction."
        )
    else:
        stories = build_delivery_stories(workspace, purpose)
        description = "Implementation loop with one-story-at-a-time delivery and quality gates."

    return {
        "project": f"{workspace} Ralph Loop",
        "branchName": derive_branch_name(base_ref),
        "description": f"{description} Purpose: {purpose}",
        "verificationCommands": {
            "typecheck": "echo 'Ralph loop: capture verification evidence per story output'",
            "lint": "echo 'Ralph loop: capture verification evidence per story output'",
            "test": "echo 'Ralph loop: run focused checks required by story notes'",
        },
        "userStories": stories,
    }


def build_progress(stories: list[dict], purpose: str) -> str:
    lines = [
        "# Ralph Progress Log (Codex)",
        f"Started: TODO",
        f"Purpose: {purpose}",
        "Output: .codex/<workspace>/audit/*.md files",
        "---",
        "",
        "## Checklist",
    ]
    for story in stories:
        lines.append(f"- [ ] {story['id']}: {story['title']}")
    lines.extend(["---", ""])
    return "\n".join(lines)


def build_readme(workspace: str, purpose: str, mode: str, base_ref: str) -> str:
    return f"""# Ralph Workspace ({workspace})

Purpose: {purpose}
Mode: {mode}
Base Ref: {base_ref}

This workspace is generated by `ralph-loop-builder`.

## Run

```bash
cd .codex/{workspace}
./ralph.sh 20
```

## Outputs

- Reports: `.codex/{workspace}/audit/*.md`
- State: `.codex/{workspace}/prd.json`, `.codex/{workspace}/progress.txt`
- Logs: `.codex/{workspace}/events.log`, `.codex/{workspace}/run.log`
"""


def build_codex_md(workspace: str, purpose: str, mode: str, base_ref: str) -> str:
    mode_guardrail = (
        "DO NOT APPLY CODE CHANGES. Read-only evidence and decision-quality output only."
        if mode == "audit"
        else "Implement exactly one story per cycle and keep verification evidence explicit."
    )
    return f"""# Ralph Instructions ({workspace})

You are an autonomous Ralph operator for this workspace.

## Objective

{purpose}

## Core Rules

1. {mode_guardrail}
2. Evidence before claims.
3. Keep base ref explicit as `{base_ref}` when reporting diff metrics.
4. Keep xenon state non-regressive across cycles.
5. Keep non-test LOC trend explicit and prefer net reduction.

## Gate Bundle

```bash
uv run ruff check src tests
uv run radon cc src -s -n C
uv run xenon --max-absolute B --max-modules A --max-average A src
python "$CODEX_HOME/skills/code-health/scripts/diff_summary_compact.py" --base {base_ref}
```
"""


def copy_runner(template_dir: Path, target_dir: Path, max_iterations: int) -> None:
    source = template_dir / "ralph.sh"
    destination = target_dir / "ralph.sh"
    if source.exists():
        shutil.copy2(source, destination)
        text = destination.read_text(encoding="utf-8")
        text = re.sub(r"MAX_ITERATIONS=\d+", f"MAX_ITERATIONS={max_iterations}", text, count=1)
        destination.write_text(text, encoding="utf-8")
        destination.chmod(0o755)
        return

    destination.write_text(
        "#!/bin/bash\n"
        "set -euo pipefail\n"
        "echo \"No template ralph.sh found. Copy runner from an existing Ralph workspace first.\"\n"
        "exit 1\n",
        encoding="utf-8",
    )
    destination.chmod(0o755)


def ensure_target_dir(target: Path, force: bool) -> None:
    if target.exists() and any(target.iterdir()) and not force:
        raise FileExistsError(f"Target already exists and is not empty: {target}. Use --force to overwrite.")
    target.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bootstrap a Ralph workspace under .codex/")
    parser.add_argument("--repo-root", default=".", help="Repository root path")
    parser.add_argument("--workspace", required=True, help="Workspace folder name under .codex/")
    parser.add_argument("--purpose", required=True, help="One-line objective for this Ralph loop")
    parser.add_argument("--mode", choices=("audit", "delivery"), default="audit")
    parser.add_argument("--base-ref", default="origin/main")
    parser.add_argument("--template", default=".codex/ralph-audit", help="Template workspace path")
    parser.add_argument("--max-iterations", type=int, default=20)
    parser.add_argument("--force", action="store_true", help="Overwrite target workspace files if needed")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    workspace = slugify(args.workspace)
    if not workspace:
        print("workspace must contain at least one alphanumeric character", file=sys.stderr)
        return 1

    template_dir = (repo_root / args.template).resolve()
    target_dir = repo_root / ".codex" / workspace
    audit_dir = target_dir / "audit"

    try:
        ensure_target_dir(target_dir, force=args.force)
    except FileExistsError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    audit_dir.mkdir(parents=True, exist_ok=True)

    prd_payload = build_prd(workspace=workspace, purpose=args.purpose, mode=args.mode, base_ref=args.base_ref)
    progress_text = build_progress(prd_payload["userStories"], args.purpose)
    readme_text = build_readme(workspace=workspace, purpose=args.purpose, mode=args.mode, base_ref=args.base_ref)
    codex_text = build_codex_md(workspace=workspace, purpose=args.purpose, mode=args.mode, base_ref=args.base_ref)

    write_json(target_dir / "prd.json", prd_payload)
    (target_dir / "progress.txt").write_text(progress_text, encoding="utf-8")
    (target_dir / "README.md").write_text(readme_text, encoding="utf-8")
    (target_dir / "CODEX.md").write_text(codex_text, encoding="utf-8")
    copy_runner(template_dir=template_dir, target_dir=target_dir, max_iterations=args.max_iterations)

    for log_name in ("events.log", "run.log"):
        (target_dir / log_name).write_text("", encoding="utf-8")

    print(f"[OK] Created workspace: {target_dir}")
    print(f"[OK] Stories: {len(prd_payload['userStories'])} ({args.mode})")
    print(f"[OK] Base ref: {args.base_ref}")
    print(f"[NEXT] cd {target_dir} && ./ralph.sh {args.max_iterations}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
