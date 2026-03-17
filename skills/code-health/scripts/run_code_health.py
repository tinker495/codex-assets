from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

COMMON_DIR = Path(__file__).resolve().parents[2] / "_common"
if str(COMMON_DIR) not in sys.path:
    sys.path.insert(0, str(COMMON_DIR))

from progress_runtime import StatusTracker, default_status_path, run_command_capture

IGNORE = (
    "**/node_modules/**,**/.git/**,**/.venv/**,**/venv/**,**/dist/**,**/build/**,"
    "**/__pycache__/**,**/.mypy_cache/**,**/.pytest_cache/**,**/.tox/**,"
    "**/tests/**,**/__tests__/**,**/test/**,**/*.test.*,**/*.spec.*,"
    "**/*.json,**/*.md,**/*.yaml,**/*.yml,**/*.toml,**/*.lock,**/htmlcov/**"
)


_OUTPUT_EXCERPT_LIMIT = 2000


@dataclass(frozen=True)
class StepFailure(Exception):
    step: str
    command: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str


def _excerpt(text: str) -> str:
    normalized = text.strip()
    if len(normalized) <= _OUTPUT_EXCERPT_LIMIT:
        return normalized
    return f"{normalized[:_OUTPUT_EXCERPT_LIMIT]}...(truncated)"


def run(
    step: str,
    cmd: list[str],
    *,
    check: bool = True,
    tracker: StatusTracker | None = None,
    relay_stdout_to_stderr: bool = True,
) -> str:
    result = run_command_capture(
        command=cmd,
        cwd=get_repo_root(),
        step_name=step,
        tracker=tracker,
        relay_stdout_to_stderr=relay_stdout_to_stderr,
        relay_stderr=True,
    )
    if check and result.returncode != 0:
        raise StepFailure(
            step=step,
            command=tuple(cmd),
            returncode=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
        )
    return (result.stdout + result.stderr).strip()


def run_module(
    step: str,
    module: str,
    args: list[str],
    *,
    check: bool = True,
    tracker: StatusTracker | None = None,
    relay_stdout_to_stderr: bool = True,
) -> str:
    if shutil.which("uv"):
        cmd = ["uv", "run", module, *args]
    else:
        cmd = [sys.executable, "-m", module, *args]
    return run(
        step,
        cmd,
        check=check,
        tracker=tracker,
        relay_stdout_to_stderr=relay_stdout_to_stderr,
    )


def run_python_script(
    step: str,
    script: Path,
    args: list[str],
    *,
    check: bool = True,
    tracker: StatusTracker | None = None,
    relay_stdout_to_stderr: bool = True,
) -> str:
    return run(
        step,
        [sys.executable, str(script), *args],
        check=check,
        tracker=tracker,
        relay_stdout_to_stderr=relay_stdout_to_stderr,
    )


def jscpd_command() -> list[str] | None:
    if shutil.which("npx"):
        return ["npx", "--yes", "jscpd"]
    if shutil.which("jscpd"):
        return ["jscpd"]
    return None


def get_repo_root() -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        root = result.stdout.strip()
        if root:
            return Path(root)
    return Path.cwd()


def get_branch_name() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        name = result.stdout.strip()
        if name:
            return name
    return "detached"


def resolve_main_ref() -> str:
    candidates = [
        "refs/remotes/origin/main",
        "refs/heads/main",
    ]
    for ref in candidates:
        result = subprocess.run(["git", "show-ref", "--verify", "--quiet", ref])
        if result.returncode == 0:
            if ref.startswith("refs/remotes/"):
                return ref.replace("refs/remotes/", "")
            if ref.startswith("refs/heads/"):
                return ref.replace("refs/heads/", "")
    return "main"


def slugify(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip())
    cleaned = re.sub(r"-{2,}", "-", cleaned).strip("-")
    return cleaned or "unknown"


def default_output_dir() -> Path:
    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        return Path(codex_home) / "shared" / "code-health"
    return Path("/tmp") / "code-health"


def build_report_paths(base_dir: Path, project: str, branch: str) -> tuple[Path, Path]:
    base_name = f"{project}__{branch}__code_health"
    return base_dir / f"{base_name}.md", base_dir / f"{base_name}.json"


def rotate_legacy(path: Path, timestamp: str) -> None:
    if not path.exists():
        return
    legacy_name = f"legacy__{path.stem}__{timestamp}{path.suffix}"
    path.rename(path.with_name(legacy_name))


def parse_jscpd_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text())
        total = data.get("statistics", {}).get("total", {})
        return {
            "files": total.get("sources", 0),
            "clones": total.get("clones", 0),
            "dup_lines": total.get("duplicatedLines", 0),
            "pct": total.get("percentage", 0),
        }
    except (FileNotFoundError, json.JSONDecodeError):
        return {"files": 0, "clones": 0, "dup_lines": 0, "pct": 0}


def parse_xenon_status(text: str) -> str:
    match = re.search(r"Status:\s*(PASS|FAIL)", text)
    return match.group(1) if match else "UNKNOWN"


def build_failure_metadata(
    failure: StepFailure,
    *,
    coverage_skipped: bool,
    coverage_pytest_completed: bool,
) -> dict[str, Any]:
    if coverage_skipped:
        standard_test_status = "not_run"
    elif coverage_pytest_completed:
        standard_test_status = "passed"
    else:
        standard_test_status = "failed"

    return {
        "step": failure.step,
        "command": list(failure.command),
        "returncode": failure.returncode,
        "stdout_excerpt": _excerpt(failure.stdout),
        "stderr_excerpt": _excerpt(failure.stderr),
        "combined_excerpt": _excerpt(f"{failure.stdout}\n{failure.stderr}".strip()),
        "coverage_pytest_completed": coverage_pytest_completed,
        "standard_test_status": standard_test_status,
    }


def write_report(
    output_path: Path,
    mode: str,
    top: int,
    diff_out: str,
    main_diff_out: str,
    main_ref: str,
    code_out: str,
    coverage_out: str,
    jscpd_data: dict[str, Any],
    coverage_skipped: bool,
    status: str,
    standard_test_status: str,
    failure: dict[str, Any] | None,
) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    xenon_status = parse_xenon_status(code_out)

    lines: list[str] = []
    lines.append("# Code Health Report")
    lines.append(f"Generated: {timestamp}")
    lines.append(f"Mode: {mode}")
    lines.append(f"Top: {top}")
    lines.append("")
    lines.append("## Summary")
    lines.append(f"- Status: {status}")
    lines.append(f"- Standard test status: {standard_test_status}")
    lines.append(
        f"- Duplication: {jscpd_data['clones']} clones, {jscpd_data['dup_lines']} duplicated lines "
        f"({jscpd_data['pct']}%) across {jscpd_data['files']} files"
    )
    lines.append(f"- Xenon thresholds: {xenon_status}")
    lines.append(f"- Coverage hotspots: {'skipped' if coverage_skipped else 'included'}")
    lines.append("")

    lines.append(f"## Diff Summary (main: {main_ref}...HEAD)")
    lines.append("```text")
    lines.append(diff_out or "(no diff output)")
    lines.append("```")
    lines.append("")

    lines.append(f"## Diff Summary (main deep: {main_ref}...HEAD)")
    lines.append("```text")
    lines.append(main_diff_out or "(no main diff output)")
    lines.append("```")
    lines.append("")

    lines.append("## Code Health (vulture/radon/xenon)")
    lines.append("```text")
    lines.append(code_out or "(no code health output)")
    lines.append("```")
    lines.append("")

    if coverage_skipped:
        lines.append("## Coverage Hotspots")
        lines.append("(skipped)")
    else:
        lines.append("## Coverage Hotspots")
        lines.append("```text")
        lines.append(coverage_out or "(no coverage output)")
        lines.append("```")
    if failure is not None:
        lines.append("")
        lines.append("## Failure Evidence")
        lines.append("```text")
        lines.append(f"step: {failure['step']}")
        lines.append(f"command: {' '.join(failure['command'])}")
        lines.append(f"returncode: {failure['returncode']}")
        lines.append(f"standard_test_status: {failure['standard_test_status']}")
        lines.append("")
        lines.append("stdout:")
        lines.append(failure["stdout_excerpt"] or "(empty)")
        lines.append("")
        lines.append("stderr:")
        lines.append(failure["stderr_excerpt"] or "(empty)")
        lines.append("```")
    lines.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp_fs = datetime.now().strftime("%Y%m%d_%H%M%S")
    rotate_legacy(output_path, timestamp_fs)
    output_path.write_text("\n".join(lines))


def write_json(output_path: Path, data: dict[str, Any]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp_fs = datetime.now().strftime("%Y%m%d_%H%M%S")
    rotate_legacy(output_path, timestamp_fs)
    output_path.write_text(json.dumps(data, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run repo code health and write a report")
    parser.add_argument("--mode", choices=["summary", "full"], default="summary")
    parser.add_argument(
        "--base",
        type=str,
        default=None,
        help="Diff base ref (default: origin/main when present, else main)",
    )
    parser.add_argument("--top", type=int, default=20)
    parser.add_argument("--top-files", type=int, default=10)
    parser.add_argument("--skip-coverage", action="store_true")
    parser.add_argument("--out-dir", type=Path, default=None)
    parser.add_argument("--status-json", type=Path, default=None)
    args = parser.parse_args()

    skill_dir = Path(__file__).resolve().parent
    repo_root = get_repo_root()
    project = slugify(repo_root.name)
    branch = slugify(get_branch_name())
    out_dir = args.out_dir if args.out_dir else default_output_dir()
    output_path, json_path = build_report_paths(out_dir, project, branch)
    status_path = (
        args.status_json.resolve()
        if args.status_json is not None
        else default_status_path(json_path, fallback_dir=out_dir, stem=f"{project}__{branch}__code_health")
    )
    main_ref = args.base if args.base else resolve_main_ref()
    tracker = StatusTracker(
        status_path=status_path,
        script_name="code-health",
        initial_state={
            "repo_root": str(repo_root),
            "project": project,
            "branch": branch,
            "base_ref": main_ref,
            "mode": args.mode,
            "top": args.top,
            "top_files": args.top_files,
        },
    )
    tracker.set_artifact("output_markdown", str(output_path))
    tracker.set_artifact("output_json", str(json_path))
    tracker.set_artifact("status_json", str(status_path) if status_path is not None else None)
    tracker.set_phase(
        "initializing",
        message=f"code-health start: base={main_ref}, mode={args.mode}, skip_coverage={args.skip_coverage}",
        output_dir=str(out_dir),
    )
    diff_out = ""
    main_diff_out = ""
    code_out = ""
    coverage_out = ""
    coverage_pytest_completed = False
    status = "passed"
    standard_test_status = "not_run" if args.skip_coverage else "failed"
    failure_data: dict[str, Any] | None = None

    jscpd_dir = out_dir / "jscpd"
    jscpd_dir.mkdir(parents=True, exist_ok=True)
    jscpd_json = jscpd_dir / "jscpd-report.json"
    jscpd_data = parse_jscpd_json(jscpd_json)

    try:
        tracker.set_phase("diff", message=f"collecting diff summaries against {main_ref}")
        diff_out = run_python_script(
            "diff_summary",
            skill_dir / "diff_summary_compact.py",
            ["--base", main_ref],
            tracker=tracker,
        )
        main_diff_out = run_python_script(
            "diff_summary_deep",
            skill_dir / "diff_summary_compact.py",
            [
                "--base",
                main_ref,
                "--deep",
                "--all-files",
                "--top-files",
                str(args.top_files),
            ],
            tracker=tracker,
        )

        tracker.set_phase("duplication", message="running duplication scan")
        jscpd_cmd = jscpd_command()
        if jscpd_cmd:
            run(
                "duplication_jscpd",
                [
                    *jscpd_cmd,
                    ".",
                    "--reporters",
                    "json",
                    "--output",
                    str(jscpd_dir),
                    "--min-lines",
                    "5",
                    "--min-tokens",
                    "70",
                    "--mode",
                    "weak",
                    "--gitignore",
                    "--silent",
                    "--ignore",
                    IGNORE,
                ],
                check=False,
                tracker=tracker,
            )

        tracker.set_phase("static-analysis", message="running compact code-health analysis")
        code_out = run_python_script(
            "code_health_compact",
            skill_dir / "code_health_compact.py",
            ["--mode", args.mode, "--top", str(args.top), "--jscpd-json", str(jscpd_json)],
            tracker=tracker,
        )

        if not args.skip_coverage:
            tracker.set_phase("coverage", message="running coverage-backed pytest")
            coverage_json = out_dir / "coverage.json"
            tracker.set_artifact("coverage_json", str(coverage_json))
            run_module("coverage_pytest", "pytest", ["--cov=stowage", "--cov=tui", "-q"], tracker=tracker)
            coverage_pytest_completed = True
            run_module("coverage_json", "coverage", ["json", "-o", str(coverage_json)], tracker=tracker)
            tracker.set_phase("coverage-report", message="building coverage hotspot report")
            coverage_out = run_python_script(
                "coverage_hotspots",
                skill_dir / "coverage_hotspots.py",
                ["--coverage-json", str(coverage_json)],
                tracker=tracker,
            )
            standard_test_status = "passed"
    except StepFailure as failure:
        status = "failed"
        failure_data = build_failure_metadata(
            failure,
            coverage_skipped=args.skip_coverage,
            coverage_pytest_completed=coverage_pytest_completed,
        )
        standard_test_status = failure_data["standard_test_status"]
        tracker.finish(
            "failed",
            message=f"code-health failed at step={failure.step}",
            failure=failure_data,
            standard_test_status=standard_test_status,
        )

    jscpd_data = parse_jscpd_json(jscpd_json)

    report_data = {
        "project": project,
        "branch": branch,
        "mode": args.mode,
        "top": args.top,
        "top_files": args.top_files,
        "main_ref": main_ref,
        "duplication": jscpd_data,
        "xenon_status": parse_xenon_status(code_out),
        "coverage_skipped": args.skip_coverage,
        "status": status,
        "standard_test_status": standard_test_status,
        "failure": failure_data,
        "output_markdown": str(output_path),
        "output_json": str(json_path),
        "status_json": str(status_path) if status_path is not None else None,
    }

    tracker.set_phase("writing", message="writing code-health artifacts")
    write_report(
        output_path=output_path,
        mode=args.mode,
        top=args.top,
        diff_out=diff_out,
        main_diff_out=main_diff_out,
        main_ref=main_ref,
        code_out=code_out,
        coverage_out=coverage_out,
        jscpd_data=jscpd_data,
        coverage_skipped=args.skip_coverage,
        status=status,
        standard_test_status=standard_test_status,
        failure=failure_data,
    )
    write_json(json_path, report_data)
    if failure_data is None:
        tracker.finish(
            "passed",
            message="code-health completed",
            standard_test_status=standard_test_status,
            xenon_status=report_data["xenon_status"],
        )

    if failure_data is not None:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
