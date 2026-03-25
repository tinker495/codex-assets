#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class Runner:
    name: str
    command: list[str]


def _slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip()).strip("-")
    return cleaned or "profile"


def _is_scalene_importable(python_executable: str) -> bool:
    probe = subprocess.run(
        [python_executable, "-c", "import scalene"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return probe.returncode == 0


def _default_output_dir(cwd: Path) -> Path:
    candidates: list[Path] = []
    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        candidates.append(Path(codex_home) / "shared" / "scalene-profiles")
    candidates.append(cwd / ".codex_tmp" / "scalene-profiles")
    candidates.append(Path("/tmp") / "scalene-profiles")

    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            test_file = candidate / ".write-test"
            test_file.write_text("ok")
            test_file.unlink()
            return candidate
        except OSError:
            continue

    raise RuntimeError("Could not find a writable output directory for Scalene artifacts.")


def _resolve_runner(mode: str, cwd: Path) -> Runner:
    if mode == "auto":
        if shutil.which("uv") and ((cwd / "pyproject.toml").exists() or (cwd / "uv.lock").exists()):
            return Runner("uv", ["uv", "run", "--with", "scalene", "python", "-m", "scalene"])
        if shutil.which("scalene"):
            return Runner("scalene", ["scalene"])
        if _is_scalene_importable(sys.executable):
            return Runner("module", [sys.executable, "-m", "scalene"])
        if shutil.which("uv"):
            return Runner("uv", ["uv", "run", "--with", "scalene", "python", "-m", "scalene"])
        raise RuntimeError("Scalene runner를 찾지 못했습니다. `scalene` 또는 `uv`가 필요합니다.")

    if mode == "uv":
        if not shutil.which("uv"):
            raise RuntimeError("`uv` 명령이 없습니다.")
        return Runner("uv", ["uv", "run", "--with", "scalene", "python", "-m", "scalene"])

    if mode == "scalene":
        if not shutil.which("scalene"):
            raise RuntimeError("`scalene` 명령이 PATH에 없습니다.")
        return Runner("scalene", ["scalene"])

    if mode == "module":
        if not _is_scalene_importable(sys.executable):
            raise RuntimeError(f"`{sys.executable} -m scalene` 를 사용할 수 없습니다.")
        return Runner("module", [sys.executable, "-m", "scalene"])

    raise RuntimeError(f"Unknown runner: {mode}")


def _build_run_command(args: argparse.Namespace, runner: Runner, json_path: Path, target: Path) -> list[str]:
    command = [*runner.command, "run", "-o", str(json_path)]

    if args.config:
        command.extend(["-c", str(Path(args.config).resolve())])
    if args.cpu_only:
        command.append("--cpu-only")
    if args.gpu:
        command.append("--gpu")
    if args.memory:
        command.append("--memory")
    if args.stacks:
        command.append("--stacks")
    if args.profile_all:
        command.append("--profile-all")
    if args.profile_only:
        command.extend(["--profile-only", args.profile_only])
    if args.profile_exclude:
        command.extend(["--profile-exclude", args.profile_exclude])
    if args.profile_system_libraries:
        command.append("--profile-system-libraries")
    if args.profile_interval is not None:
        command.extend(["--profile-interval", str(args.profile_interval)])
    if args.use_virtual_time:
        command.append("--use-virtual-time")
    if args.cpu_percent_threshold is not None:
        command.extend(["--cpu-percent-threshold", str(args.cpu_percent_threshold)])
    if args.cpu_sampling_rate is not None:
        command.extend(["--cpu-sampling-rate", str(args.cpu_sampling_rate)])
    if args.allocation_sampling_window is not None:
        command.extend(["--allocation-sampling-window", str(args.allocation_sampling_window)])
    if args.malloc_threshold is not None:
        command.extend(["--malloc-threshold", str(args.malloc_threshold)])
    if args.program_path:
        command.extend(["--program-path", str(Path(args.program_path).resolve())])
    if args.off:
        command.append("--off")
    for extra_arg in args.extra_scalene_arg:
        command.append(extra_arg)

    command.append(str(target))

    program_args = list(args.program_args)
    if program_args and program_args[0] == "--":
        program_args = program_args[1:]
    if program_args:
        command.append("---")
        command.extend(program_args)

    return command


def _run_command(command: list[str], cwd: Path, capture: bool = False) -> subprocess.CompletedProcess[str]:
    print(f"[scalene-profiler] cwd: {cwd}")
    print(f"[scalene-profiler] cmd: {' '.join(command)}")
    return subprocess.run(
        command,
        cwd=str(cwd),
        text=True,
        capture_output=capture,
        check=False,
    )


def _materialize_view(
    args: argparse.Namespace,
    runner: Runner,
    json_path: Path,
    output_dir: Path,
    stem: str,
) -> dict[str, str]:
    artifacts: dict[str, str] = {"json": str(json_path)}

    if args.view == "none":
        return artifacts

    view_command = [*runner.command, "view", str(json_path)]
    if args.view == "cli":
        view_command.append("--cli")
        if args.reduced:
            view_command.append("-r")
        result = _run_command(view_command, output_dir, capture=True)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "Scalene CLI view failed.")
        cli_path = output_dir / f"{stem}.cli.txt"
        cli_path.write_text(result.stdout)
        print(result.stdout, end="")
        artifacts["cli"] = str(cli_path)
        return artifacts

    if args.view == "html":
        view_command.append("--html")
        result = _run_command(view_command, output_dir, capture=True)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "Scalene HTML view failed.")
        generated_path = output_dir / "scalene-profile.html"
        html_path = output_dir / f"{stem}.html"
        if generated_path.exists():
            generated_path.replace(html_path)
        artifacts["html"] = str(html_path)
        return artifacts

    if args.view == "standalone":
        view_command.append("--standalone")
        result = _run_command(view_command, output_dir, capture=True)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "Scalene standalone view failed.")
        generated_path = output_dir / "scalene-profile.html"
        html_path = output_dir / f"{stem}.standalone.html"
        if generated_path.exists():
            generated_path.replace(html_path)
        artifacts["standalone_html"] = str(html_path)
        return artifacts

    raise RuntimeError(f"Unknown view type: {args.view}")


def _write_manifest(
    manifest_path: Path,
    *,
    runner: Runner,
    cwd: Path,
    target: Path,
    command: list[str],
    artifacts: dict[str, str],
    program_args: list[str],
) -> None:
    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "runner": runner.name,
        "cwd": str(cwd),
        "target": str(target),
        "program_args": program_args,
        "command": command,
        "artifacts": artifacts,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Scalene with reproducible artifact management.",
    )
    parser.add_argument("target", help="Python script path to profile.")
    parser.add_argument(
        "program_args",
        nargs=argparse.REMAINDER,
        help="Arguments passed to the profiled program. Put them after `--`.",
    )
    parser.add_argument("--cwd", default=".", help="Working directory for the profile run.")
    parser.add_argument(
        "--runner",
        choices=("auto", "uv", "scalene", "module"),
        default="auto",
        help="How to invoke Scalene. `auto` prefers `uv` inside uv-managed repos.",
    )
    parser.add_argument("--label", help="Optional artifact prefix. Defaults to target stem + timestamp.")
    parser.add_argument("--output-dir", help="Directory for JSON/HTML/manifest artifacts.")
    parser.add_argument("--config", help="Scalene YAML config file.")
    parser.add_argument("--cpu-only", action="store_true", help="Use Scalene CPU-only mode.")
    parser.add_argument("--gpu", action="store_true", help="Request GPU profiling.")
    parser.add_argument("--memory", action="store_true", help="Request explicit memory profiling.")
    parser.add_argument("--stacks", action="store_true", help="Collect stack traces.")
    parser.add_argument("--profile-all", action="store_true", help="Profile all code, not just the target tree.")
    parser.add_argument("--profile-only", help="Comma-separated path filters to include.")
    parser.add_argument("--profile-exclude", help="Comma-separated path filters to exclude.")
    parser.add_argument(
        "--profile-system-libraries",
        action="store_true",
        help="Include stdlib and installed packages.",
    )
    parser.add_argument("--profile-interval", type=float, help="Emit periodic profiles every N seconds.")
    parser.add_argument(
        "--use-virtual-time",
        action="store_true",
        help="Measure only CPU time, not blocking or I/O time.",
    )
    parser.add_argument("--cpu-percent-threshold", type=float, help="CPU reporting threshold.")
    parser.add_argument("--cpu-sampling-rate", type=float, help="CPU sampling rate in seconds.")
    parser.add_argument("--allocation-sampling-window", type=int, help="Allocation sampling window in bytes.")
    parser.add_argument("--malloc-threshold", type=int, help="Minimum allocations to report.")
    parser.add_argument("--program-path", help="Directory that contains the code to profile.")
    parser.add_argument("--off", action="store_true", help="Start with profiling disabled.")
    parser.add_argument(
        "--view",
        choices=("none", "cli", "html", "standalone"),
        default="standalone",
        help="Optional post-run rendering step.",
    )
    parser.add_argument(
        "--reduced",
        action="store_true",
        help="When used with `--view cli`, only show active lines.",
    )
    parser.add_argument(
        "--extra-scalene-arg",
        action="append",
        default=[],
        help="Repeatable escape hatch for advanced Scalene flags not exposed here.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cwd = Path(args.cwd).resolve()
    if not cwd.exists():
        raise RuntimeError(f"Working directory does not exist: {cwd}")

    target = Path(args.target)
    if not target.is_absolute():
        target = (cwd / target).resolve()
    if not target.exists():
        raise RuntimeError(f"Target script does not exist: {target}")

    output_dir = Path(args.output_dir).resolve() if args.output_dir else _default_output_dir(cwd)
    output_dir.mkdir(parents=True, exist_ok=True)

    runner = _resolve_runner(args.runner, cwd)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    label = _slugify(args.label or f"{target.stem}-{timestamp}")
    json_path = output_dir / f"{label}.json"
    manifest_path = output_dir / f"{label}.manifest.json"

    command = _build_run_command(args, runner, json_path, target)
    result = _run_command(command, cwd)
    if result.returncode != 0:
        raise RuntimeError(f"Scalene run failed with exit code {result.returncode}.")

    program_args = list(args.program_args)
    if program_args and program_args[0] == "--":
        program_args = program_args[1:]

    artifacts = _materialize_view(args, runner, json_path, output_dir, label)
    artifacts["manifest"] = str(manifest_path)
    _write_manifest(
        manifest_path,
        runner=runner,
        cwd=cwd,
        target=target,
        command=command,
        artifacts=artifacts,
        program_args=program_args,
    )

    print("[scalene-profiler] artifacts:")
    for name, value in artifacts.items():
        print(f"  - {name}: {value}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"[scalene-profiler] error: {exc}", file=sys.stderr)
        raise SystemExit(1)
