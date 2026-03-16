#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile


SCRIPT_PATH = Path(__file__).with_name("todo_inventory.py")


def run_json(cwd: Path, *args: str) -> dict[str, object]:
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), *args, "--json"],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def assert_git_aware_scan_skips_ignored_files() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        write_text(root / ".gitignore", "ignored/\n")
        write_text(root / "src/app.py", "# TODO: keep tracked\nprint('ok')\n")
        write_text(root / "ignored/generated.py", "# TODO: ignored by auto scan\nprint('ignored')\n")
        subprocess.run(["git", "add", ".gitignore", "src/app.py"], cwd=root, check=True)

        auto_scan = run_json(root, ".", "--mode", "scan")
        assert auto_scan["summary"]["scan_basis"] == "git"
        assert auto_scan["summary"]["current_todo_count"] == 1
        assert auto_scan["current_todos"] == [
            {
                "path": "src/app.py",
                "line": 1,
                "text": "# TODO: keep tracked",
                "source": "current",
            }
        ]

        filesystem_scan = run_json(root, ".", "--mode", "scan", "--scan-basis", "filesystem")
        assert filesystem_scan["summary"]["scan_basis"] == "filesystem"
        assert filesystem_scan["summary"]["current_todo_count"] == 2
        assert {item["path"] for item in filesystem_scan["current_todos"]} == {
            "ignored/generated.py",
            "src/app.py",
        }

        diff_scan = run_json(root, ".", "--mode", "diff")
        assert diff_scan["summary"]["diff_status"] == "available"
        assert diff_scan["summary"]["added_todo_count"] == 1
        assert diff_scan["added_todos_in_diff"] == [
            {
                "path": "src/app.py",
                "line": 1,
                "text": "# TODO: keep tracked",
                "source": "diff-staged",
            }
        ]


def assert_auto_falls_back_to_filesystem_outside_git() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        write_text(root / "module.py", "# TODO: filesystem fallback\n")

        scan = run_json(root, ".", "--mode", "scan")
        assert scan["summary"]["scan_basis"] == "filesystem"
        assert scan["summary"]["current_todo_count"] == 1
        assert scan["current_todos"] == [
            {
                "path": "module.py",
                "line": 1,
                "text": "# TODO: filesystem fallback",
                "source": "current",
            }
        ]


def main() -> None:
    assert_git_aware_scan_skips_ignored_files()
    assert_auto_falls_back_to_filesystem_outside_git()
    print("todo_inventory regression checks passed")


if __name__ == "__main__":
    main()
