from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

IGNORE = (
    "**/node_modules/**,**/.git/**,**/.venv/**,**/venv/**,**/dist/**,**/build/**,"
    "**/__pycache__/**,**/.mypy_cache/**,**/.pytest_cache/**,**/.tox/**,"
    "**/tests/**,**/__tests__/**,**/test/**,**/*.test.*,**/*.spec.*,"
    "**/*.json,**/*.md,**/*.yaml,**/*.yml,**/*.toml,**/*.lock,**/htmlcov/**"
)


def run(cmd: list[str], check: bool = True) -> str:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if check and result.returncode != 0:
        raise subprocess.CalledProcessError(
            returncode=result.returncode, cmd=cmd, output=result.stdout, stderr=result.stderr
        )
    return (result.stdout + result.stderr).strip()


def run_module(module: str, args: list[str], check: bool = True) -> str:
    if shutil.which("uv"):
        cmd = ["uv", "run", module, *args]
    else:
        cmd = [sys.executable, "-m", module, *args]
    return run(cmd, check=check)


def run_python_script(script: Path, args: list[str], check: bool = True) -> str:
    return run([sys.executable, str(script), *args], check=check)


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
    args = parser.parse_args()

    skill_dir = Path(__file__).resolve().parent
    repo_root = get_repo_root()
    project = slugify(repo_root.name)
    branch = slugify(get_branch_name())
    out_dir = args.out_dir if args.out_dir else default_output_dir()
    output_path, json_path = build_report_paths(out_dir, project, branch)
    main_ref = args.base if args.base else resolve_main_ref()
    diff_out = run_python_script(
        skill_dir / "diff_summary_compact.py",
        ["--base", main_ref],
    )
    main_diff_out = run_python_script(
        skill_dir / "diff_summary_compact.py",
        [
            "--base",
            main_ref,
            "--deep",
            "--all-files",
            "--top-files",
            str(args.top_files),
        ],
    )

    jscpd_dir = out_dir / "jscpd"
    jscpd_dir.mkdir(parents=True, exist_ok=True)
    jscpd_json = jscpd_dir / "jscpd-report.json"
    jscpd_cmd = jscpd_command()
    if jscpd_cmd:
        run(
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
        )

    code_out = run_python_script(
        skill_dir / "code_health_compact.py",
        ["--mode", args.mode, "--top", str(args.top), "--jscpd-json", str(jscpd_json)],
    )

    coverage_out = ""
    if not args.skip_coverage:
        coverage_json = out_dir / "coverage.json"
        run_module("pytest", ["--cov=stowage", "--cov=tui", "-q"])
        run_module("coverage", ["json", "-o", str(coverage_json)])
        coverage_out = run_python_script(
            skill_dir / "coverage_hotspots.py",
            ["--coverage-json", str(coverage_json)],
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
        "output_markdown": str(output_path),
        "output_json": str(json_path),
    }

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
    )
    write_json(json_path, report_data)


if __name__ == "__main__":
    main()
