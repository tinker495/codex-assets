#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
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


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text())
    except FileNotFoundError as exc:
        raise ValueError(f"Workflow JSON not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Workflow JSON is invalid: {path}") from exc


def load_markdown(path: Path) -> str:
    try:
        return path.read_text()
    except FileNotFoundError as exc:
        raise ValueError(f"PR brief markdown not found: {path}") from exc


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


def run_command(
    *,
    name: str,
    command: list[str],
    cwd: Path,
    env: dict[str, str] | None = None,
    tracker: StatusTracker | None = None,
    relay_stdout_to_stderr: bool = False,
) -> CommandResult:
    process = run_command_capture(
        command=command,
        cwd=cwd,
        env=env,
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


def serialize_command(result: CommandResult) -> dict[str, Any]:
    return {
        "name": result.name,
        "command": list(result.command),
        "returncode": result.returncode,
        "stdout_excerpt": _excerpt(result.stdout),
        "stderr_excerpt": _excerpt(result.stderr),
    }


def normalize_base(base: str) -> str:
    if base.startswith("origin/"):
        return base.split("/", 1)[1]
    return base


def extract_title(markdown: str) -> str:
    for line in markdown.splitlines():
        if line.startswith("## PR Description:"):
            title = line.split(":", 1)[1].strip()
            if title:
                return title
    raise ValueError("Unable to infer PR title from markdown. Pass --title explicitly.")


def gh_env() -> dict[str, str]:
    env = dict(os.environ)
    env["GH_FORCE_TTY"] = "0"
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GH_PAGER"] = "cat"
    return env


def ensure_checklist_passed(payload: dict[str, Any], *, allow_nonpassing: bool) -> str:
    checklist = payload.get("checklist")
    if not isinstance(checklist, dict):
        raise ValueError("workflow JSON must contain checklist object")
    overall_status = checklist.get("overall_status")
    if not isinstance(overall_status, str):
        raise ValueError("workflow JSON checklist.overall_status must be a string")
    if allow_nonpassing:
        return overall_status
    if overall_status != "passed":
        raise ValueError(f"Checklist overall_status={overall_status}; use --allow-nonpassing to override")
    return overall_status


def find_existing_open_pr(*, repo_root: Path, head_branch: str) -> dict[str, Any] | None:
    env = gh_env()
    command = [
        "gh",
        "pr",
        "list",
        "--head",
        head_branch,
        "--state",
        "open",
        "--json",
        "number,title,url,headRefName,baseRefName",
    ]
    result = run_command(name="gh_pr_list", command=command, cwd=repo_root, env=env)
    if result.returncode != 0:
        raise ValueError(result.stderr.strip() or result.stdout.strip() or "gh pr list failed")
    try:
        payload = json.loads(result.stdout or "[]")
    except json.JSONDecodeError as exc:
        raise ValueError("gh pr list returned invalid JSON") from exc
    if not payload:
        return None
    if not isinstance(payload, list):
        raise ValueError("gh pr list payload must be a list")
    first = payload[0]
    if not isinstance(first, dict):
        raise ValueError("gh pr list items must be objects")
    return first


def ensure_gh_auth(repo_root: Path) -> None:
    env = gh_env()
    result = run_command(name="gh_auth_status", command=["gh", "auth", "status"], cwd=repo_root, env=env)
    if result.returncode != 0:
        raise ValueError(result.stderr.strip() or result.stdout.strip() or "gh auth status failed")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Push branch and create a PR from workflow artifacts")
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--workflow-json", type=Path, required=True)
    parser.add_argument("--body-markdown", type=Path, required=True)
    parser.add_argument("--title", default="")
    parser.add_argument("--base", default="")
    parser.add_argument("--head", default="")
    parser.add_argument("--push-branch", action="store_true")
    parser.add_argument("--allow-nonpassing", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--status-json", type=Path, default=None)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    repo_root = resolve_repo_root(args.repo_root.resolve())
    workflow_payload = load_json(args.workflow_json.resolve())
    markdown = load_markdown(args.body_markdown.resolve())
    checklist_status = ensure_checklist_passed(workflow_payload, allow_nonpassing=args.allow_nonpassing)
    status_path = (
        args.status_json.resolve()
        if args.status_json is not None
        else default_status_path(args.output_json.resolve() if args.output_json is not None else None, fallback_dir=repo_root / ".codex_tmp" / "pr-workflow", stem="create-pr")
    )
    tracker = StatusTracker(
        status_path=status_path,
        script_name="pr-workflow.create",
        initial_state={
            "repo_root": str(repo_root),
            "workflow_json": str(args.workflow_json.resolve()),
            "body_markdown": str(args.body_markdown.resolve()),
        },
    )
    tracker.set_artifact("status_json", str(status_path) if status_path is not None else None)

    branch_context = workflow_payload.get("branch_context")
    if not isinstance(branch_context, dict):
        raise ValueError("workflow JSON must contain branch_context object")

    head_branch = args.head.strip() or str(branch_context.get("branch", "")).strip()
    if not head_branch:
        raise ValueError("Unable to determine head branch from workflow JSON. Pass --head explicitly.")

    base_branch = normalize_base(args.base.strip() or str(branch_context.get("base", "")).strip())
    if not base_branch:
        raise ValueError("Unable to determine base branch from workflow JSON. Pass --base explicitly.")

    title = args.title.strip() or extract_title(markdown)

    planned_commands: list[list[str]] = []
    if args.push_branch:
        planned_commands.append(["git", "push", "-u", "origin", head_branch])
    planned_commands.append(
        [
            "gh",
            "pr",
            "create",
            "--base",
            base_branch,
            "--head",
            head_branch,
            "--title",
            title,
            "--body-file",
            str(args.body_markdown.resolve()),
        ]
    )

    output: dict[str, Any] = {
        "repo_root": str(repo_root),
        "workflow_json": str(args.workflow_json.resolve()),
        "body_markdown": str(args.body_markdown.resolve()),
        "checklist_overall_status": checklist_status,
        "head_branch": head_branch,
        "base_branch": base_branch,
        "title": title,
        "push_branch": args.push_branch,
        "execute": args.execute,
        "planned_commands": planned_commands,
        "existing_open_pr": None,
        "push_result": None,
        "create_result": None,
        "pr_url": None,
        "status_json": str(status_path) if status_path is not None else None,
    }

    if not args.execute:
        rendered = json.dumps(output, indent=2)
        if args.output_json is not None:
            args.output_json.parent.mkdir(parents=True, exist_ok=True)
            args.output_json.write_text(rendered)
        print(rendered)
        tracker.finish("passed", message="create_pr_from_workflow dry-run completed")
        raise SystemExit(0)

    tracker.set_phase("auth", message="checking gh authentication")
    ensure_gh_auth(repo_root)
    tracker.set_phase("existing-pr", message=f"checking existing open PR for {head_branch}")
    existing_pr = find_existing_open_pr(repo_root=repo_root, head_branch=head_branch)
    if existing_pr is not None:
        output["existing_open_pr"] = existing_pr
        output["pr_url"] = existing_pr.get("url")
        rendered = json.dumps(output, indent=2)
        if args.output_json is not None:
            args.output_json.parent.mkdir(parents=True, exist_ok=True)
            args.output_json.write_text(rendered)
        print(rendered)
        tracker.finish("passed", message="existing PR already open", pr_url=output["pr_url"])
        raise SystemExit(0)

    if args.push_branch:
        tracker.set_phase("push", message=f"pushing branch {head_branch}")
        push_result = run_command(
            name="git_push",
            command=["git", "push", "-u", "origin", head_branch],
            cwd=repo_root,
            tracker=tracker,
        )
        output["push_result"] = serialize_command(push_result)
        if push_result.returncode != 0:
            rendered = json.dumps(output, indent=2)
            if args.output_json is not None:
                args.output_json.parent.mkdir(parents=True, exist_ok=True)
                args.output_json.write_text(rendered)
            print(rendered)
            tracker.finish("failed", message="git push failed")
            raise SystemExit(1)

    tracker.set_phase("create-pr", message=f"creating PR from {head_branch} to {base_branch}")
    create_result = run_command(
        name="gh_pr_create",
        command=[
            "gh",
            "pr",
            "create",
            "--base",
            base_branch,
            "--head",
            head_branch,
            "--title",
            title,
            "--body-file",
            str(args.body_markdown.resolve()),
        ],
        cwd=repo_root,
        env=gh_env(),
        tracker=tracker,
    )
    output["create_result"] = serialize_command(create_result)
    if create_result.returncode == 0:
        url = create_result.stdout.strip().splitlines()[-1] if create_result.stdout.strip() else None
        output["pr_url"] = url

    rendered = json.dumps(output, indent=2)
    if args.output_json is not None:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(rendered)
    print(rendered)

    if create_result.returncode == 0:
        tracker.finish("passed", message="PR created successfully", pr_url=output["pr_url"])
        raise SystemExit(0)
    tracker.finish("failed", message="gh pr create failed")
    raise SystemExit(1)


if __name__ == "__main__":
    main()
