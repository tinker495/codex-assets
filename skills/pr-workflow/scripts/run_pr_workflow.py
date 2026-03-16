#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CommandResult:
    name: str
    command: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str
    reused: bool = False


@dataclass(frozen=True)
class NumstatRow:
    path: str
    added: int
    deleted: int


def _excerpt(text: str, limit: int = 2000) -> str:
    normalized = text.strip()
    if len(normalized) <= limit:
        return normalized
    return f"{normalized[:limit]}...(truncated)"


def run_command(*, name: str, command: list[str], cwd: Path) -> CommandResult:
    process = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        capture_output=True,
    )
    return CommandResult(
        name=name,
        command=tuple(command),
        returncode=process.returncode,
        stdout=process.stdout,
        stderr=process.stderr,
    )


def parse_command(command_text: str) -> list[str]:
    parsed = shlex.split(command_text)
    if not parsed:
        raise ValueError("Command must not be empty")
    return parsed


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


def default_code_health_out_dir() -> Path:
    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        return Path(codex_home) / "shared" / "code-health"
    return Path("/tmp") / "code-health"


def expected_code_health_json(repo_root: Path, branch: str, out_dir: Path) -> Path:
    project = slugify(repo_root.name)
    branch_slug = slugify(branch)
    return out_dir / f"{project}__{branch_slug}__code_health.json"


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text())
    except FileNotFoundError as exc:
        raise ValueError(f"JSON file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON file: {path}") from exc


def command_status(result: CommandResult) -> str:
    return "passed" if result.returncode == 0 else "failed"


def commit_subjects(commit_log: list[str]) -> list[str]:
    subjects: list[str] = []
    for line in commit_log:
        parts = line.split("\t", 1)
        subjects.append(parts[1] if len(parts) == 2 else parts[0])
    return subjects


def parse_numstat(text: str) -> list[NumstatRow]:
    rows: list[NumstatRow] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        added, deleted, path = line.split("\t", 2)
        if added == "-" or deleted == "-":
            continue
        rows.append(NumstatRow(path=path, added=int(added), deleted=int(deleted)))
    return rows


def runtime_category_from_commits(commit_log: list[str]) -> str:
    if not commit_log:
        return "Feature"
    subjects = [subject.lower() for subject in commit_subjects(commit_log)]
    if subjects and all(subject.startswith("refactor") for subject in subjects):
        return "Refactor"
    if subjects and all(subject.startswith(("fix", "bugfix")) for subject in subjects):
        return "Bugfix"
    return "Feature"


def _matches(text: str, keywords: tuple[str, ...]) -> int:
    return sum(1 for keyword in keywords if keyword in text)


def infer_narrative_hints(
    *,
    branch: str,
    commit_log: list[str],
    file_list: list[str],
    runtime_bucket: str,
) -> dict[str, Any]:
    subjects = commit_subjects(commit_log)
    corpus_parts = [branch.lower(), *(subject.lower() for subject in subjects), *(path.lower() for path in file_list)]
    corpus = " ".join(corpus_parts)
    branch_sources = [branch, *subjects[:3], *file_list[:5]]

    evidence_score = _matches(
        corpus,
        ("evidence", "diagnostic", "diagnostics", "debug", "trace", "log", "export", "visibility", "observability"),
    )
    ui_score = _matches(corpus, ("tui", "widget", "render", "visual", "legend", "color", "overlay", "display"))
    constraint_score = _matches(
        corpus,
        ("constraint", "validation", "anomaly", "blocked", "support", "reject", "fallback", "budget", "solver"),
    )
    timeout_score = _matches(corpus, ("timeout", "stale", "async", "race", "concurrency"))

    if evidence_score >= 2:
        problem = "이 브랜치는 기존에 SPP 진단 근거와 가시성이 부족해 원인 추적과 리뷰가 어려웠던 문제를 보완하려는 것으로 보입니다."
        if ui_score >= 1:
            solution = "이를 위해 진단 근거 export를 강화하고, TUI/시각화 경로에서 해당 정보를 바로 확인할 수 있게 기능을 추가한 것으로 추론됩니다."
        else:
            solution = "이를 위해 진단 근거 수집과 export 흐름을 보강하는 기능을 추가한 것으로 추론됩니다."
        confidence = "high"
    elif constraint_score >= 2:
        problem = "이 브랜치는 기존 제약/검증 정보가 부족하거나 실패 원인이 충분히 드러나지 않던 문제를 보완하려는 것으로 보입니다."
        solution = "이를 위해 제약/검증 관련 근거와 처리 로직을 강화하는 기능을 추가한 것으로 추론됩니다."
        confidence = "medium"
    elif timeout_score >= 1:
        problem = "이 브랜치는 기존 비동기/타이밍 경로에서 불안정하거나 재현이 어려운 문제가 있었던 것으로 보입니다."
        solution = "이를 위해 타이밍 관련 처리와 검증 경로를 보강한 것으로 추론됩니다."
        confidence = "medium"
    elif runtime_bucket == "Bugfix":
        problem = "이 브랜치는 기존 동작의 오류 또는 불일치를 수정하려는 맥락으로 보입니다."
        solution = "이를 위해 관련 로직 수정과 검증 보강이 추가된 것으로 추론됩니다."
        confidence = "low"
    elif runtime_bucket == "Refactor":
        problem = "이 브랜치는 기존 구조의 복잡도 또는 유지보수 부담을 줄이려는 맥락으로 보입니다."
        solution = "이를 위해 구조 정리와 책임 분리가 진행된 것으로 추론됩니다."
        confidence = "low"
    else:
        return {
            "problem_statement": None,
            "solution_statement": None,
            "confidence": "low",
            "source_hints": branch_sources,
            "needs_manual_completion": True,
            "manual_prompt": "TODO: 이 브랜치 이전에 어떤 문제/운영 불편/결함이 있었는지 1~2문장으로 보강해 주세요.",
        }

    return {
        "problem_statement": problem,
        "solution_statement": solution,
        "confidence": confidence,
        "source_hints": branch_sources,
        "needs_manual_completion": confidence == "low",
        "manual_prompt": (
            "TODO: 자동 추론 문장이 약하면, 이 브랜치가 해결하려는 기존 문제를 실제 배경에 맞게 보강해 주세요."
            if confidence == "low"
            else ""
        ),
    }


def classify_path(path: str, *, runtime_bucket: str) -> str:
    if path.startswith("tests/"):
        return "Test"
    if path.startswith("docs/") or path in {"README.md", "AGENTS.md", "CLAUDE.md"} or path.endswith(".md"):
        return "Document"
    if path.startswith(("scripts/", "src/scripts/", ".github/")) or path in {
        "Makefile",
        "pyproject.toml",
        "uv.lock",
        "package.json",
        "package-lock.json",
    }:
        return "Tooling"
    return runtime_bucket


def build_category_metrics(numstats: list[NumstatRow], *, runtime_bucket: str) -> dict[str, dict[str, Any]]:
    categories: dict[str, dict[str, Any]] = {
        "Feature": {"added": 0, "deleted": 0, "net": 0, "files": []},
        "Refactor": {"added": 0, "deleted": 0, "net": 0, "files": []},
        "Test": {"added": 0, "deleted": 0, "net": 0, "files": []},
        "Document": {"added": 0, "deleted": 0, "net": 0, "files": []},
        "Tooling": {"added": 0, "deleted": 0, "net": 0, "files": []},
        "Bugfix": {"added": 0, "deleted": 0, "net": 0, "files": []},
    }
    for row in numstats:
        category = classify_path(row.path, runtime_bucket=runtime_bucket)
        current = categories[category]
        current["added"] += row.added
        current["deleted"] += row.deleted
        current["net"] = current["added"] - current["deleted"]
        current["files"].append(row.path)
    return categories


def collect_branch_context(repo_root: Path, base: str) -> dict[str, Any]:
    branch = git_output(repo_root, "branch", "--show-current")
    commits = git_output(repo_root, "log", f"{base}..HEAD", "--pretty=format:%h%x09%s")
    files = git_output(repo_root, "diff", f"{base}...HEAD", "--name-only")
    numstat_raw = git_output(repo_root, "diff", f"{base}...HEAD", "--numstat")
    diff_stat = git_output(repo_root, "diff", "--shortstat", f"{base}...HEAD")
    commit_log = [line for line in commits.splitlines() if line.strip()]
    numstats = parse_numstat(numstat_raw)
    runtime_bucket = runtime_category_from_commits(commit_log)
    category_metrics = build_category_metrics(numstats, runtime_bucket=runtime_bucket)
    return {
        "branch": branch,
        "base": base,
        "commit_count": len(commit_log),
        "commit_log": commit_log,
        "files_changed": len([line for line in files.splitlines() if line.strip()]),
        "file_list": [line for line in files.splitlines() if line.strip()],
        "numstat": [
            {"path": row.path, "added": row.added, "deleted": row.deleted, "net": row.added - row.deleted}
            for row in numstats
        ],
        "runtime_bucket": runtime_bucket,
        "narrative_hints": infer_narrative_hints(
            branch=branch,
            commit_log=commit_log,
            file_list=[line for line in files.splitlines() if line.strip()],
            runtime_bucket=runtime_bucket,
        ),
        "category_metrics": category_metrics,
        "diff_stat": diff_stat,
    }


def collect_breaking_change_hints(repo_root: Path, base: str) -> dict[str, Any]:
    raw = git_output(repo_root, "diff", "--name-status", f"{base}...HEAD")
    deleted_files: list[str] = []
    renamed_files: list[dict[str, str]] = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        status = parts[0]
        if status == "D" and len(parts) >= 2:
            deleted_files.append(parts[1])
            continue
        if status.startswith("R") and len(parts) >= 3:
            renamed_files.append({"from": parts[1], "to": parts[2]})
    return {
        "deleted_files": deleted_files,
        "renamed_files": renamed_files,
        "suspected_breaking_changes": bool(deleted_files or renamed_files),
        "summary": (
            f"deleted={len(deleted_files)}, renamed={len(renamed_files)}; "
            "review required for public API/config changes"
        ),
    }


def run_code_health(
    *,
    repo_root: Path,
    base: str,
    out_dir: Path,
    mode: str,
    top: int,
    top_files: int,
    skip_coverage: bool,
) -> tuple[CommandResult, Path, dict[str, Any]]:
    script = Path("/Users/mrx-ksjung/.codex/skills/code-health/scripts/run_code_health.py")
    branch = git_output(repo_root, "branch", "--show-current")
    expected_json = expected_code_health_json(repo_root, branch, out_dir)
    command = [
        "python3",
        str(script),
        "--mode",
        mode,
        "--top",
        str(top),
        "--top-files",
        str(top_files),
        "--base",
        base,
        "--out-dir",
        str(out_dir),
    ]
    if skip_coverage:
        command.append("--skip-coverage")
    result = run_command(name="code_health", command=command, cwd=repo_root)
    payload = load_json(expected_json)
    return result, expected_json, payload


def reuse_code_health_json(path: Path) -> tuple[CommandResult, Path, dict[str, Any]]:
    payload = load_json(path)
    result = CommandResult(
        name="code_health",
        command=("reuse", str(path)),
        returncode=0,
        stdout="",
        stderr="",
        reused=True,
    )
    return result, path, payload


def run_checklist_evaluator(
    *,
    code_health_json: Path,
    repo_root: Path,
    lint_status: str,
    format_status: str,
    breaking_changes_status: str,
    require_full_dataset: bool,
    full_dataset_status: str,
) -> dict[str, Any]:
    script = Path("/Users/mrx-ksjung/.codex/skills/pr-workflow/scripts/evaluate_pr_checklist.py")
    command = [
        "python3",
        str(script),
        "--code-health-json",
        str(code_health_json),
        "--lint",
        lint_status,
        "--format",
        format_status,
        "--breaking-changes",
        breaking_changes_status,
        "--full-dataset",
        full_dataset_status,
    ]
    if require_full_dataset:
        command.append("--require-full-dataset")
    result = run_command(name="checklist_evaluator", command=command, cwd=repo_root)
    if result.returncode != 0:
        raise ValueError(result.stderr.strip() or result.stdout.strip() or "Checklist evaluator failed")
    return json.loads(result.stdout)


def serialize_command_result(result: CommandResult) -> dict[str, Any]:
    return {
        "name": result.name,
        "command": list(result.command),
        "returncode": result.returncode,
        "status": command_status(result) if not result.reused else "reused",
        "reused": result.reused,
        "stdout_excerpt": _excerpt(result.stdout),
        "stderr_excerpt": _excerpt(result.stderr),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run PR workflow prerequisites and emit checklist verdict JSON")
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--base", default="origin/main")
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
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--pr-title", default="")
    parser.add_argument("--pr-brief-output", type=Path, default=None)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    repo_root = resolve_repo_root(args.repo_root.resolve())
    branch_context = collect_branch_context(repo_root, args.base)
    out_dir = args.code_health_out_dir if args.code_health_out_dir is not None else default_code_health_out_dir()

    if args.code_health_json is None:
        code_health_result, code_health_json_path, code_health_payload = run_code_health(
            repo_root=repo_root,
            base=args.base,
            out_dir=out_dir,
            mode=args.code_health_mode,
            top=args.code_health_top,
            top_files=args.code_health_top_files,
            skip_coverage=args.skip_coverage,
        )
    else:
        code_health_result, code_health_json_path, code_health_payload = reuse_code_health_json(
            args.code_health_json.resolve()
        )

    lint_result = run_command(name="lint", command=parse_command(args.lint_cmd), cwd=repo_root)
    format_result = run_command(name="format", command=parse_command(args.format_cmd), cwd=repo_root)

    if args.require_full_dataset:
        full_dataset_result = run_command(
            name="full_dataset",
            command=parse_command(args.full_dataset_cmd),
            cwd=repo_root,
        )
        full_dataset_status = command_status(full_dataset_result)
    else:
        full_dataset_result = CommandResult(
            name="full_dataset",
            command=tuple(),
            returncode=0,
            stdout="",
            stderr="",
            reused=True,
        )
        full_dataset_status = "not_run"

    breaking_changes = collect_breaking_change_hints(repo_root, args.base)
    checklist_payload = run_checklist_evaluator(
        code_health_json=code_health_json_path,
        repo_root=repo_root,
        lint_status=command_status(lint_result),
        format_status=command_status(format_result),
        breaking_changes_status="passed",
        require_full_dataset=args.require_full_dataset,
        full_dataset_status=full_dataset_status,
    )

    output = {
        "repo_root": str(repo_root),
        "branch_context": branch_context,
        "artifacts": {
            "code_health_json": str(code_health_json_path),
            "code_health_markdown": code_health_payload.get("output_markdown"),
        },
        "code_health": {
            "status": code_health_payload.get("status"),
            "standard_test_status": code_health_payload.get("standard_test_status"),
            "xenon_status": code_health_payload.get("xenon_status"),
            "duplication": code_health_payload.get("duplication"),
            "failure": code_health_payload.get("failure"),
        },
        "commands": {
            "code_health": serialize_command_result(code_health_result),
            "lint": serialize_command_result(lint_result),
            "format": serialize_command_result(format_result),
            "full_dataset": serialize_command_result(full_dataset_result),
        },
        "breaking_changes": {
            **breaking_changes,
            "documentation_status": "passed",
            "documentation_note": "Auto-generated diff hint summary available for PR body.",
        },
        "checklist": checklist_payload,
        "pr_body_inputs": {
            "overview_inputs": {
                "branch": branch_context["branch"],
                "base": branch_context["base"],
                "commit_count": branch_context["commit_count"],
                "files_changed": branch_context["files_changed"],
                "diff_stat": branch_context["diff_stat"],
            },
            "narrative_hints": branch_context["narrative_hints"],
            "category_metrics": branch_context["category_metrics"],
            "runtime_bucket": branch_context["runtime_bucket"],
            "code_health_summary": {
                "status": code_health_payload.get("status"),
                "standard_test_status": code_health_payload.get("standard_test_status"),
                "xenon_status": code_health_payload.get("xenon_status"),
                "duplication": code_health_payload.get("duplication"),
            },
            "breaking_changes": breaking_changes,
        },
        "ready_to_create_pr": checklist_payload["overall_status"] == "passed",
    }

    rendered = json.dumps(output, indent=2)
    if args.output_json is not None:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(rendered)
    if args.pr_brief_output is not None:
        if args.output_json is None:
            raise ValueError("--pr-brief-output requires --output-json so the generator has a concrete input artifact")
        generator = Path("/Users/mrx-ksjung/.codex/skills/pr-workflow/scripts/generate_pr_brief.py")
        generator_command = [
            "python3",
            str(generator),
            "--input-json",
            str(args.output_json),
            "--output-markdown",
            str(args.pr_brief_output),
        ]
        if args.pr_title.strip():
            generator_command.extend(["--title", args.pr_title.strip()])
        generator_result = run_command(name="generate_pr_brief", command=generator_command, cwd=repo_root)
        if generator_result.returncode != 0:
            raise ValueError(
                generator_result.stderr.strip() or generator_result.stdout.strip() or "PR brief generation failed"
            )
        output["artifacts"]["pr_brief_markdown"] = str(args.pr_brief_output)
        rendered = json.dumps(output, indent=2)
        args.output_json.write_text(rendered)
    print(rendered)

    if checklist_payload["overall_status"] == "passed":
        raise SystemExit(0)
    if checklist_payload["overall_status"] == "blocked":
        raise SystemExit(2)
    raise SystemExit(1)


if __name__ == "__main__":
    main()
