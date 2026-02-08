"""Compact diff summary for agentic consumption."""

from __future__ import annotations

import argparse
import re
import subprocess

TEST_RE = re.compile(r"(^|/)(tests?|__tests__)/|\.test\.|\.spec\.")


def get_base_ref() -> str:
    """Resolve base ref: upstream -> origin/HEAD -> main/master."""
    cmds = [
        ["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"],
        ["git", "symbolic-ref", "-q", "--short", "refs/remotes/origin/HEAD"],
    ]
    for cmd in cmds:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            ref = result.stdout.strip()
            if ref:
                return ref
    # Fallback to main/master
    for branch in ["main", "master"]:
        result = subprocess.run(["git", "show-ref", "--verify", "--quiet", f"refs/heads/{branch}"])
        if result.returncode == 0:
            return branch
    return "HEAD"


def resolve_base_ref(base: str | None) -> str:
    if base:
        return base
    return get_base_ref()


def summarize_numstat(numstat: str) -> tuple[int, int, int, int]:
    """Return (add, rem, tadd, trem) from numstat."""
    add = rem = tadd = trem = 0
    for line in numstat.strip().splitlines():
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        a, r = parts[0], parts[1]
        if not a.isdigit() or not r.isdigit():
            continue
        path = "\t".join(parts[2:])
        a_val, r_val = int(a), int(r)
        if TEST_RE.search(path):
            tadd += a_val
            trem += r_val
        else:
            add += a_val
            rem += r_val
    return add, rem, tadd, trem


def parse_numstat_entries(numstat: str) -> list[tuple[str, int, int, bool]]:
    entries: list[tuple[str, int, int, bool]] = []
    for line in numstat.strip().splitlines():
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        a, r = parts[0], parts[1]
        if not a.isdigit() or not r.isdigit():
            continue
        path = "\t".join(parts[2:])
        is_test = bool(TEST_RE.search(path))
        entries.append((path, int(a), int(r), is_test))
    return entries


def summarize_name_status(name_status: str) -> tuple[list[str], list[str], list[str], list[str]]:
    """Return (new_files, del_files, new_test_files, del_test_files) from name-status."""
    new_files: list[str] = []
    del_files: list[str] = []
    new_test_files: list[str] = []
    del_test_files: list[str] = []

    for line in name_status.strip().splitlines():
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        status, path = parts[0], parts[1]
        is_test = bool(TEST_RE.search(path))

        if status == "A":
            if is_test:
                new_test_files.append(path)
            else:
                new_files.append(path)
        elif status == "D":
            if is_test:
                del_test_files.append(path)
            else:
                del_files.append(path)

    return new_files, del_files, new_test_files, del_test_files


def count_untracked() -> tuple[list[str], list[str]]:
    """Return (untracked_files, untracked_test_files)."""
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True,
    )
    files: list[str] = []
    test_files: list[str] = []

    for line in result.stdout.strip().splitlines():
        if not line.startswith("?? "):
            continue
        path = line[3:]
        if not path.endswith(".py"):
            continue
        if TEST_RE.search(path):
            test_files.append(path)
        else:
            files.append(path)

    return files, test_files


def print_diff(
    label: str,
    add: int,
    rem: int,
    tadd: int,
    trem: int,
    new_files: list[str],
    del_files: list[str],
    new_test_files: list[str],
    del_test_files: list[str],
) -> None:
    net = add - rem
    tnet = tadd - trem
    print(f"{label}:")
    print(f"  Non-test: +{add}/-{rem} (net {net:+d})")
    print(f"  Test:     +{tadd}/-{trem} (net {tnet:+d})")

    if new_files:
        print(f"  New files: {len(new_files)}")
        for f in new_files[:5]:
            print(f"    + {f}")
        if len(new_files) > 5:
            print(f"    ... and {len(new_files) - 5} more")

    if del_files:
        print(f"  Deleted files: {len(del_files)}")
        for f in del_files[:5]:
            print(f"    - {f}")
        if len(del_files) > 5:
            print(f"    ... and {len(del_files) - 5} more")

    if new_test_files:
        print(f"  New test files: {len(new_test_files)}")
        for f in new_test_files[:3]:
            print(f"    + {f}")
        if len(new_test_files) > 3:
            print(f"    ... and {len(new_test_files) - 3} more")

    if del_test_files:
        print(f"  Deleted test files: {len(del_test_files)}")
        for f in del_test_files[:3]:
            print(f"    - {f}")
        if len(del_test_files) > 3:
            print(f"    ... and {len(del_test_files) - 3} more")


def print_top_churn(entries: list[tuple[str, int, int, bool]], label: str, top_n: int, is_test: bool) -> None:
    filtered = [entry for entry in entries if entry[3] is is_test]
    if not filtered:
        print(f"{label}: (none)")
        return
    sorted_entries = sorted(filtered, key=lambda e: (-(e[1] + e[2]), e[0]))
    print(f"{label}:")
    for path, add, rem, _ in sorted_entries[:top_n]:
        total = add + rem
        print(f"  {total:5d}  +{add:4d}/-{rem:4d}  {path}")


def git_diff_numstat(base: str | None, staged: bool, all_files: bool) -> str:
    cmd = ["git", "diff", "--numstat"]
    if staged:
        cmd.append("--staged")
    elif base:
        cmd.append(f"{base}...HEAD")
    if not all_files:
        cmd.extend(["--", "*.py"])
    return subprocess.run(cmd, capture_output=True, text=True).stdout


def git_diff_name_status(base: str | None, staged: bool, all_files: bool) -> str:
    cmd = ["git", "diff", "--name-status"]
    if staged:
        cmd.append("--staged")
    elif base:
        cmd.append(f"{base}...HEAD")
    if not all_files:
        cmd.extend(["--", "*.py"])
    return subprocess.run(cmd, capture_output=True, text=True).stdout


def main() -> None:
    parser = argparse.ArgumentParser(description="Compact diff summary")
    parser.add_argument("--base", type=str, default=None)
    parser.add_argument("--top-files", type=int, default=10)
    parser.add_argument("--all-files", action="store_true")
    parser.add_argument("--deep", action="store_true")
    args = parser.parse_args()

    base = resolve_base_ref(args.base)
    all_files = args.all_files

    # Branch diff
    numstat = git_diff_numstat(base, staged=False, all_files=all_files)
    name_status = git_diff_name_status(base, staged=False, all_files=all_files)
    add, rem, tadd, trem = summarize_numstat(numstat)
    new_f, del_f, new_tf, del_tf = summarize_name_status(name_status)
    print_diff(f"Branch ({base}...HEAD)", add, rem, tadd, trem, new_f, del_f, new_tf, del_tf)

    # Staged diff
    numstat = git_diff_numstat(base=None, staged=True, all_files=all_files)
    name_status = git_diff_name_status(base=None, staged=True, all_files=all_files)
    add, rem, tadd, trem = summarize_numstat(numstat)
    new_f, del_f, new_tf, del_tf = summarize_name_status(name_status)
    print_diff("Staged", add, rem, tadd, trem, new_f, del_f, new_tf, del_tf)

    # Working diff
    numstat = git_diff_numstat(base=None, staged=False, all_files=all_files)
    name_status = git_diff_name_status(base=None, staged=False, all_files=all_files)
    add, rem, tadd, trem = summarize_numstat(numstat)
    new_f, del_f, new_tf, del_tf = summarize_name_status(name_status)

    # Untracked files (working directory only)
    untracked, untracked_test = count_untracked()

    print_diff("Working", add, rem, tadd, trem, new_f, del_f, new_tf, del_tf)

    if untracked or untracked_test:
        print("  Untracked:")
        if untracked:
            print(f"    Non-test: {len(untracked)} files")
            for f in untracked[:3]:
                print(f"      ? {f}")
            if len(untracked) > 3:
                print(f"      ... and {len(untracked) - 3} more")
        if untracked_test:
            print(f"    Test: {len(untracked_test)} files")
            for f in untracked_test[:3]:
                print(f"      ? {f}")
            if len(untracked_test) > 3:
                print(f"      ... and {len(untracked_test) - 3} more")

    if args.deep:
        entries = parse_numstat_entries(git_diff_numstat(base, staged=False, all_files=all_files))
        print(f"\nTop churn files ({base}...HEAD, add+del):")
        print_top_churn(entries, "  Non-test", args.top_files, is_test=False)
        print_top_churn(entries, "  Test", args.top_files, is_test=True)


if __name__ == "__main__":
    main()
