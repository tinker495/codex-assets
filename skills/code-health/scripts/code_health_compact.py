"""Compact code health reporter for agentic consumption.

Parses tool outputs and emits concise, structured summaries.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


def run(cmd: list[str], check: bool = True) -> str:
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if check and result.returncode != 0 and result.returncode != 2:
        # Some tools exit 2 for threshold failures (xenon)
        raise subprocess.CalledProcessError(
            returncode=result.returncode, cmd=cmd, output=result.stdout, stderr=result.stderr
        )
    return result.stdout + result.stderr


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


def parse_vulture_output(text: str, top_n: int = 10) -> list[str]:
    lines = [ln for ln in text.strip().splitlines() if ln.strip()]
    return lines[:top_n]


def parse_radon_cc(text: str, top_n: int = 10) -> list[str]:
    # Filter lines with grades C, D, E, F and take top N
    lines = text.strip().splitlines()
    result = []
    for ln in lines:
        if re.search(r"\s[CDEF]\s", ln):
            result.append(ln)
        if len(result) >= top_n:
            break
    return result


def parse_radon_mi(text: str, top_n: int = 10) -> list[str]:
    lines = text.strip().splitlines()
    # MI lines are already sorted by the tool
    return lines[:top_n]


def print_section(title: str, lines: list[str]) -> None:
    if not lines:
        print(f"\n{title}: (none)")
        return
    print(f"\n{title}:")
    for ln in lines:
        print(f"  {ln}")


def tracked_python_targets() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "--", "*.py"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return ["."]
    targets = [
        line.strip()
        for line in result.stdout.splitlines()
        if line.strip() and not line.startswith("tests/")
    ]
    return targets or ["."]


def run_python_module(module: str, args: list[str], check: bool = True) -> str:
    if shutil.which("uv"):
        cmd = ["uv", "run", "python", "-m", module, *args]
    else:
        cmd = [sys.executable, "-m", module, *args]
    return run(cmd, check=check)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Code health compact reporter")
    parser.add_argument("--mode", choices=["summary", "full"], default="summary")
    parser.add_argument("--top", type=int, default=10)
    parser.add_argument("--jscpd-json", type=Path, default=Path("report/jscpd-report.json"))
    args = parser.parse_args()

    # Header
    print("=" * 50)
    print(f"CODE HEALTH ({args.mode.upper()})")
    print("=" * 50)

    # JSCPD summary
    jscpd_data = parse_jscpd_json(args.jscpd_json)
    print("\n[DUPLICATION]")
    print(f"  Files scanned: {jscpd_data['files']}")
    print(f"  Clones found: {jscpd_data['clones']}")
    print(f"  Duplicated lines: {jscpd_data['dup_lines']} ({jscpd_data['pct']}%)")

    targets = tracked_python_targets()

    # Vulture
    vulture_conf = "80" if args.mode == "summary" else "60"
    vulture_out = run_python_module(
        "vulture",
        [
            *targets,
            "--min-confidence",
            vulture_conf,
            "--sort-by-size",
            "--exclude",
            "*/.venv/*,*/venv/*,*/node_modules/*,*/dist/*,*/build/*,*/.tox/*,*/.mypy_cache/*,*/.pytest_cache/*,*/__pycache__/*",
        ],
    )
    vulture_lines = parse_vulture_output(vulture_out, args.top)
    print_section(f"[DEAD CODE] (confidence >= {vulture_conf}%, top {args.top})", vulture_lines)

    # Radon CC
    radon_cc_out = run_python_module("radon", ["cc", "-s", "-o", "SCORE", *targets])
    radon_cc_lines = parse_radon_cc(radon_cc_out, args.top)
    grade = "C" if args.mode == "summary" else "A"
    print_section(f"[COMPLEXITY] (cyclomatic >= {grade}, top {args.top})", radon_cc_lines)

    # Radon MI
    radon_mi_out = run_python_module("radon", ["mi", "-s", "--sort", *targets])
    radon_mi_lines = parse_radon_mi(radon_mi_out, args.top)
    print_section(f"[MAINTAINABILITY] (lowest MI, top {args.top})", radon_mi_lines)

    # Xenon (threshold check)
    xenon_out = run_python_module(
        "xenon",
        ["--max-absolute", "B", "--max-average", "A", "--max-modules", "A", *targets],
        check=False,
    )
    xenon_ok = "PASS" if "thresholds exceeded" not in xenon_out.lower() and xenon_out.strip() == "" else "FAIL"
    print("\n[XENON THRESHOLDS]")
    print(f"  Status: {xenon_ok}")
    print("  Limits: absolute=B, average=A, modules=A")

    print("\n" + "=" * 50)


if __name__ == "__main__":
    main()
