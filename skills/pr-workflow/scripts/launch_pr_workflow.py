#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

COMMON_DIR = Path(__file__).resolve().parents[2] / "_common"
if str(COMMON_DIR) not in sys.path:
    sys.path.insert(0, str(COMMON_DIR))

from progress_runtime import StatusTracker, default_status_path, run_command_capture


@dataclass(frozen=True)
class CommandResult:
    name: str
    command: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str


def _excerpt(text: str, limit: int = 2000) -> str:
    normalized = text.strip()
    if len(normalized) <= limit:
        return normalized
    return f"{normalized[:limit]}...(truncated)"


def run_command(
    *,
    name: str,
    command: list[str],
    cwd: Path,
    tracker: StatusTracker | None = None,
    relay_stdout_to_stderr: bool = False,
) -> CommandResult:
    process = run_command_capture(
        command=command,
        cwd=cwd,
        step_name=name,
        tracker=tracker,
        relay_stdout_to_stderr=relay_stdout_to_stderr,
        relay_stderr=True,
    )
    return CommandResult(
        name=name,
        command=tuple(command),
        returncode=process.returncode,
        stdout=process.stdout,
        stderr=process.stderr,
    )


def git_output(repo_root: Path, *args: str) -> str:
    process = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        text=True,
        capture_output=True,
    )
    if process.returncode != 0:
        raise ValueError(process.stderr.strip() or process.stdout.strip() or f"git {' '.join(args)} failed")
    return process.stdout.strip()


def resolve_repo_root(path: Path) -> Path:
    return Path(git_output(path, "rev-parse", "--show-toplevel"))


def slugify(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in "._-" else "-" for ch in value.strip())
    while "--" in cleaned:
        cleaned = cleaned.replace("--", "-")
    cleaned = cleaned.strip("-")
    return cleaned or "unknown"


def parse_optional_command(text: str) -> list[str]:
    parsed = shlex.split(text)
    if not parsed:
        raise ValueError("Command must not be empty")
    return parsed


def serialize_command(result: CommandResult) -> dict[str, Any]:
    return {
        "name": result.name,
        "command": list(result.command),
        "returncode": result.returncode,
        "stdout_excerpt": _excerpt(result.stdout),
        "stderr_excerpt": _excerpt(result.stderr),
    }


def load_json_from_stdout(result: CommandResult, *, expected_name: str) -> dict[str, Any]:
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{expected_name} did not emit valid JSON") from exc


def build_default_artifacts_dir(repo_root: Path) -> Path:
    branch = git_output(repo_root, "branch", "--show-current")
    return repo_root / ".codex_tmp" / "pr-workflow" / slugify(branch)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Single-entry PR workflow launcher")
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument(
        "--base",
        default="",
        help="Upstream branch used only to resolve the fork point; omit to auto-detect origin/HEAD, then main/master.",
    )
    parser.add_argument("--artifacts-dir", type=Path, default=None)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--pr-title", default="")
    parser.add_argument("--code-health-json", type=Path, default=None)
    parser.add_argument("--code-health-mode", default="summary", choices=["summary", "full"])
    parser.add_argument("--code-health-top", type=int, default=20)
    parser.add_argument("--code-health-top-files", type=int, default=10)
    parser.add_argument("--code-health-out-dir", type=Path, default=None)
    parser.add_argument("--skip-coverage", action="store_true")
    parser.add_argument("--lint-cmd", default="make lint")
    parser.add_argument("--format-cmd", default="make format")
    parser.add_argument("--require-full-dataset", action="store_true")
    parser.add_argument("--full-dataset-cmd", default="make test-full")
    parser.add_argument("--push-branch", action="store_true")
    parser.add_argument("--allow-nonpassing", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--status-json", type=Path, default=None)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    repo_root = resolve_repo_root(args.repo_root.resolve())
    artifacts_dir = args.artifacts_dir.resolve() if args.artifacts_dir is not None else build_default_artifacts_dir(repo_root)
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    status_path = (
        args.status_json.resolve()
        if args.status_json is not None
        else default_status_path(args.output_json.resolve() if args.output_json is not None else None, fallback_dir=artifacts_dir, stem="launch")
    )
    run_status_path = artifacts_dir / "run_pr_workflow.status.json"
    create_status_path = artifacts_dir / "create_pr.status.json"
    tracker = StatusTracker(
        status_path=status_path,
        script_name="pr-workflow.launch",
        initial_state={
            "repo_root": str(repo_root),
            "artifacts_dir": str(artifacts_dir),
            "base": args.base or "(auto fork-point upstream)",
        },
    )
    tracker.set_artifact("status_json", str(status_path) if status_path is not None else None)
    tracker.set_artifact("run_stage_status_json", str(run_status_path))
    tracker.set_artifact("create_stage_status_json", str(create_status_path))

    workflow_json_path = artifacts_dir / "workflow.json"
    pr_brief_path = artifacts_dir / "pr_brief.md"
    create_json_path = artifacts_dir / "create_pr.json"
    tracker.set_artifact("workflow_json", str(workflow_json_path))
    tracker.set_artifact("pr_brief_markdown", str(pr_brief_path))
    tracker.set_artifact("create_pr_json", str(create_json_path))

    run_script = Path("/Users/mrx-ksjung/.codex/skills/pr-workflow/scripts/run_pr_workflow.py")
    create_script = Path("/Users/mrx-ksjung/.codex/skills/pr-workflow/scripts/create_pr_from_workflow.py")

    run_command_args = [
        "python3",
        str(run_script),
        "--repo-root",
        str(repo_root),
        "--output-json",
        str(workflow_json_path),
        "--pr-brief-output",
        str(pr_brief_path),
        "--status-json",
        str(run_status_path),
    ]
    if args.base.strip():
        run_command_args.extend(["--base", args.base.strip()])
    if args.pr_title.strip():
        run_command_args.extend(["--pr-title", args.pr_title.strip()])
    if args.code_health_json is not None:
        run_command_args.extend(["--code-health-json", str(args.code_health_json.resolve())])
    else:
        run_command_args.extend(
            [
                "--code-health-mode",
                args.code_health_mode,
                "--code-health-top",
                str(args.code_health_top),
                "--code-health-top-files",
                str(args.code_health_top_files),
            ]
        )
        if args.code_health_out_dir is not None:
            run_command_args.extend(["--code-health-out-dir", str(args.code_health_out_dir.resolve())])
        if args.skip_coverage:
            run_command_args.append("--skip-coverage")
    if args.lint_cmd.strip():
        parse_optional_command(args.lint_cmd)
        run_command_args.extend(["--lint-cmd", args.lint_cmd])
    if args.format_cmd.strip():
        parse_optional_command(args.format_cmd)
        run_command_args.extend(["--format-cmd", args.format_cmd])
    if args.require_full_dataset:
        run_command_args.append("--require-full-dataset")
        run_command_args.extend(["--full-dataset-cmd", args.full_dataset_cmd])

    tracker.set_phase("run-stage", message="launching run_pr_workflow stage")
    run_result = run_command(name="run_pr_workflow", command=run_command_args, cwd=repo_root, tracker=tracker)
    workflow_payload = load_json_from_stdout(run_result, expected_name="run_pr_workflow")

    create_result_payload: dict[str, Any] | None = None
    create_result_command: CommandResult | None = None
    workflow_status = str(workflow_payload.get("checklist", {}).get("overall_status", "unknown"))
    should_attempt_create = workflow_status == "passed" or args.allow_nonpassing

    if should_attempt_create:
        create_command_args = [
            "python3",
            str(create_script),
            "--repo-root",
            str(repo_root),
            "--workflow-json",
            str(workflow_json_path),
            "--body-markdown",
            str(pr_brief_path),
            "--output-json",
            str(create_json_path),
            "--status-json",
            str(create_status_path),
        ]
        if args.pr_title.strip():
            create_command_args.extend(["--title", args.pr_title.strip()])
        if args.push_branch:
            create_command_args.append("--push-branch")
        if args.allow_nonpassing:
            create_command_args.append("--allow-nonpassing")
        if args.execute:
            create_command_args.append("--execute")
        tracker.set_phase("create-stage", message="launching create_pr_from_workflow stage")
        create_result_command = run_command(
            name="create_pr_from_workflow",
            command=create_command_args,
            cwd=repo_root,
            tracker=tracker,
        )
        create_result_payload = load_json_from_stdout(create_result_command, expected_name="create_pr_from_workflow")

    output = {
        "repo_root": str(repo_root),
        "artifacts_dir": str(artifacts_dir),
        "artifacts": {
            "workflow_json": str(workflow_json_path),
            "pr_brief_markdown": str(pr_brief_path),
            "create_pr_json": str(create_json_path) if create_result_payload is not None else None,
            "status_json": str(status_path) if status_path is not None else None,
            "run_stage_status_json": str(run_status_path),
            "create_stage_status_json": str(create_status_path) if create_result_payload is not None else None,
        },
        "execute": args.execute,
        "push_branch": args.push_branch,
        "allow_nonpassing": args.allow_nonpassing,
        "workflow_stage": {
            "result": serialize_command(run_result),
            "payload": workflow_payload,
        },
        "create_stage": (
            {
                "skipped": False,
                "result": serialize_command(create_result_command) if create_result_command is not None else None,
                "payload": create_result_payload,
            }
            if create_result_payload is not None
            else {
                "skipped": True,
                "reason": (
                    f"workflow checklist overall_status={workflow_status}; "
                    "pass --allow-nonpassing to continue to PR creation stage"
                ),
            }
        ),
    }

    rendered = json.dumps(output, indent=2)
    if args.output_json is not None:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(rendered)
    print(rendered)
    final_status = "passed"
    if run_result.returncode != 0:
        final_status = "failed"
    elif create_result_command is not None and create_result_command.returncode != 0:
        final_status = "failed"
    elif not should_attempt_create:
        final_status = "blocked"
    tracker.finish(final_status, message=f"launch_pr_workflow completed with status={final_status}")

    if run_result.returncode != 0:
        raise SystemExit(run_result.returncode)
    if create_result_command is not None:
        raise SystemExit(create_result_command.returncode)
    raise SystemExit(2 if not should_attempt_create else 0)


if __name__ == "__main__":
    main()
