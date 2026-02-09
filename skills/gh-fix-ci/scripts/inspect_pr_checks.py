#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from shutil import which
from typing import Any, Iterable, NamedTuple, Sequence

FAILURE_CONCLUSIONS = {
    "failure",
    "cancelled",
    "timed_out",
    "action_required",
}

FAILURE_STATES = {
    "failure",
    "error",
    "cancelled",
    "timed_out",
    "action_required",
}

FAILURE_BUCKETS = {"fail"}

FAILURE_MARKERS = (
    "error",
    "fail",
    "failed",
    "traceback",
    "exception",
    "assert",
    "panic",
    "fatal",
    "timeout",
    "segmentation fault",
)

DEFAULT_MAX_LINES = 160
DEFAULT_CONTEXT_LINES = 30
PENDING_LOG_MARKERS = (
    "still in progress",
    "log will be available when it is complete",
)


class TargetPR(NamedTuple):
    repo_slug: str
    pr: str
    url: str | None = None
    source: str = "unknown"


class GhResult:
    def __init__(self, returncode: int, stdout: str, stderr: str):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def run_gh_command(args: Sequence[str], cwd: Path, gh_repo: str | None = None) -> GhResult:
    cmd = ["gh"]
    if gh_repo:
        cmd.extend(["-R", gh_repo])
    cmd.extend(args)
    process = subprocess.run(
        cmd,
        cwd=cwd,
        text=True,
        capture_output=True,
    )
    return GhResult(process.returncode, process.stdout, process.stderr)


def run_gh_command_raw(
    args: Sequence[str], cwd: Path, gh_repo: str | None = None
) -> tuple[int, bytes, str]:
    cmd = ["gh"]
    if gh_repo:
        cmd.extend(["-R", gh_repo])
    cmd.extend(args)
    process = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
    )
    stderr = process.stderr.decode(errors="replace")
    return process.returncode, process.stdout, stderr


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect failing GitHub PR checks, fetch GitHub Actions logs, and extract a "
            "failure snippet."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--repo", default=".", help="Path inside the target Git repository.")
    parser.add_argument(
        "--pr", default=None, help="PR number or URL (defaults to current branch PR)."
    )
    parser.add_argument(
        "--gh-repo",
        default=None,
        help=(
            "GitHub repository slug (owner/repo) used for PR/check lookup. "
            "When omitted, auto-resolves current-repo PR then fork-upstream PR."
        ),
    )
    parser.add_argument("--max-lines", type=int, default=DEFAULT_MAX_LINES)
    parser.add_argument("--context", type=int, default=DEFAULT_CONTEXT_LINES)
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text output.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = find_git_root(Path(args.repo))
    if repo_root is None:
        print("Error: not inside a Git repository.", file=sys.stderr)
        return 1

    if not ensure_gh_available(repo_root):
        return 1

    target = resolve_target_pr(args.pr, args.gh_repo, repo_root)
    if target is None:
        return 1

    checks = fetch_checks(target.pr, repo_root, target.repo_slug)
    if checks is None:
        return 1

    failing = [c for c in checks if is_failing(c)]
    if not failing:
        if args.json:
            print(
                json.dumps(
                    {
                        "repo": target.repo_slug,
                        "pr": target.pr,
                        "prUrl": target.url,
                        "resolutionSource": target.source,
                        "results": [],
                    },
                    indent=2,
                )
            )
        else:
            print(f"{target.repo_slug} PR #{target.pr}: no failing checks detected.")
        return 0

    results = []
    for check in failing:
        results.append(
            analyze_check(
                check,
                repo_root=repo_root,
                repo_slug=target.repo_slug,
                max_lines=max(1, args.max_lines),
                context=max(1, args.context),
            )
        )

    if args.json:
        print(
            json.dumps(
                {
                    "repo": target.repo_slug,
                    "pr": target.pr,
                    "prUrl": target.url,
                    "resolutionSource": target.source,
                    "results": results,
                },
                indent=2,
            )
        )
    else:
        render_results(target.repo_slug, target.pr, results)

    return 1


def find_git_root(start: Path) -> Path | None:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=start,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        return None
    return Path(result.stdout.strip())


def ensure_gh_available(repo_root: Path) -> bool:
    if which("gh") is None:
        print("Error: gh is not installed or not on PATH.", file=sys.stderr)
        return False
    result = run_gh_command(["auth", "status"], cwd=repo_root)
    if result.returncode == 0:
        return True
    message = (result.stderr or result.stdout or "").strip()
    print(message or "Error: gh not authenticated.", file=sys.stderr)
    return False


def resolve_target_pr(
    pr_value: str | None, gh_repo: str | None, repo_root: Path
) -> TargetPR | None:
    if pr_value:
        return resolve_explicit_pr(pr_value, gh_repo, repo_root)

    direct = resolve_current_repo_pr(repo_root, gh_repo)
    if direct is not None:
        return direct

    if gh_repo:
        print(
            f"Error: no open PR found for current branch in {gh_repo}.",
            file=sys.stderr,
        )
        return None

    upstream = resolve_upstream_pr_for_fork(repo_root)
    if upstream is not None:
        return upstream

    print(
        "Error: unable to resolve a PR from current branch in current repo or upstream fork parent.",
        file=sys.stderr,
    )
    return None


def resolve_explicit_pr(
    pr_value: str, gh_repo: str | None, repo_root: Path
) -> TargetPR | None:
    url_match = re.search(r"github\.com/([^/]+/[^/]+)/pull/(\d+)", pr_value)
    if url_match:
        return TargetPR(
            repo_slug=url_match.group(1),
            pr=url_match.group(2),
            url=pr_value,
            source="explicit-url",
        )

    if not pr_value.isdigit():
        print(
            "Error: --pr must be a PR number or GitHub PR URL.",
            file=sys.stderr,
        )
        return None

    repo_slug = gh_repo or fetch_repo_slug(repo_root)
    if not repo_slug:
        print(
            "Error: unable to resolve target repository for --pr number input.",
            file=sys.stderr,
        )
        return None
    return TargetPR(repo_slug=repo_slug, pr=pr_value, source="explicit-number")


def resolve_current_repo_pr(repo_root: Path, gh_repo: str | None) -> TargetPR | None:
    fields = "number,url"
    result = run_gh_command(["pr", "view", "--json", fields], cwd=repo_root, gh_repo=gh_repo)
    if result.returncode != 0:
        return None
    try:
        data = json.loads(result.stdout or "{}")
    except json.JSONDecodeError:
        return None
    number = data.get("number")
    if not number:
        return None
    url = str(data.get("url") or "")
    repo_slug = gh_repo or parse_repo_from_pr_url(url) or fetch_repo_slug(repo_root)
    if not repo_slug:
        return None
    return TargetPR(repo_slug=repo_slug, pr=str(number), url=url or None, source="current-repo")


def resolve_upstream_pr_for_fork(repo_root: Path) -> TargetPR | None:
    repo_info = fetch_repo_info(repo_root)
    if not repo_info:
        return None
    if not bool(repo_info.get("isFork")):
        return None

    current_slug = str(repo_info.get("nameWithOwner") or "")
    current_owner = current_slug.split("/", 1)[0] if "/" in current_slug else ""
    parent_slug = parse_parent_slug(repo_info)
    if not current_owner or not parent_slug:
        return None

    branch = current_branch(repo_root)
    if not branch:
        return None

    prs = fetch_upstream_pr_candidates(repo_root, parent_slug, current_owner, branch)
    if not isinstance(prs, list) or not prs:
        return None

    prs = [p for p in prs if isinstance(p, dict) and p.get("number")]
    if not prs:
        return None
    prs.sort(key=lambda p: str(p.get("updatedAt") or ""), reverse=True)
    selected = prs[0]
    return TargetPR(
        repo_slug=parent_slug,
        pr=str(selected["number"]),
        url=str(selected.get("url") or "") or None,
        source="fork-upstream-head-branch",
    )


def fetch_upstream_pr_candidates(
    repo_root: Path, parent_slug: str, current_owner: str, branch: str
) -> list[dict[str, Any]] | None:
    fields = "number,url,updatedAt"
    primary = run_gh_command(
        [
            "pr",
            "list",
            "--state",
            "open",
            "--head",
            f"{current_owner}:{branch}",
            "--json",
            fields,
        ],
        cwd=repo_root,
        gh_repo=parent_slug,
    )
    if primary.returncode == 0:
        try:
            primary_list = json.loads(primary.stdout or "[]")
        except json.JSONDecodeError:
            primary_list = []
        if isinstance(primary_list, list) and primary_list:
            return primary_list

    fallback = run_gh_command(
        [
            "pr",
            "list",
            "--state",
            "open",
            "--search",
            f"head:{branch} author:{current_owner}",
            "--json",
            fields,
        ],
        cwd=repo_root,
        gh_repo=parent_slug,
    )
    if fallback.returncode != 0:
        return None
    try:
        fallback_list = json.loads(fallback.stdout or "[]")
    except json.JSONDecodeError:
        return None
    return fallback_list if isinstance(fallback_list, list) else None


def fetch_checks(pr_value: str, repo_root: Path, repo_slug: str) -> list[dict[str, Any]] | None:
    primary_fields = ["name", "state", "conclusion", "detailsUrl", "startedAt", "completedAt"]
    result = run_gh_command(
        ["pr", "checks", pr_value, "--json", ",".join(primary_fields)],
        cwd=repo_root,
        gh_repo=repo_slug,
    )
    if result.returncode != 0:
        message = "\n".join(filter(None, [result.stderr, result.stdout])).strip()
        available_fields = parse_available_fields(message)
        if available_fields:
            fallback_fields = [
                "name",
                "state",
                "bucket",
                "link",
                "startedAt",
                "completedAt",
                "workflow",
            ]
            selected_fields = [field for field in fallback_fields if field in available_fields]
            if not selected_fields:
                print("Error: no usable fields available for gh pr checks.", file=sys.stderr)
                return None
            result = run_gh_command(
                ["pr", "checks", pr_value, "--json", ",".join(selected_fields)],
                cwd=repo_root,
                gh_repo=repo_slug,
            )
            if result.returncode != 0:
                message = (result.stderr or result.stdout or "").strip()
                print(message or "Error: gh pr checks failed.", file=sys.stderr)
                return None
        else:
            print(message or "Error: gh pr checks failed.", file=sys.stderr)
            return None
    try:
        data = json.loads(result.stdout or "[]")
    except json.JSONDecodeError:
        print("Error: unable to parse checks JSON.", file=sys.stderr)
        return None
    if not isinstance(data, list):
        print("Error: unexpected checks JSON shape.", file=sys.stderr)
        return None
    return data


def is_failing(check: dict[str, Any]) -> bool:
    conclusion = normalize_field(check.get("conclusion"))
    if conclusion in FAILURE_CONCLUSIONS:
        return True
    state = normalize_field(check.get("state") or check.get("status"))
    if state in FAILURE_STATES:
        return True
    bucket = normalize_field(check.get("bucket"))
    return bucket in FAILURE_BUCKETS


def analyze_check(
    check: dict[str, Any],
    repo_root: Path,
    repo_slug: str,
    max_lines: int,
    context: int,
) -> dict[str, Any]:
    url = check.get("detailsUrl") or check.get("link") or ""
    run_id = extract_run_id(url)
    job_id = extract_job_id(url)
    base: dict[str, Any] = {
        "name": check.get("name", ""),
        "detailsUrl": url,
        "runId": run_id,
        "jobId": job_id,
    }

    if run_id is None:
        base["status"] = "external"
        base["note"] = "No GitHub Actions run id detected in detailsUrl."
        return base

    metadata = fetch_run_metadata(run_id, repo_root, repo_slug)
    log_text, log_error, log_status = fetch_check_log(
        run_id=run_id,
        job_id=job_id,
        repo_root=repo_root,
        repo_slug=repo_slug,
    )

    if log_status == "pending":
        base["status"] = "log_pending"
        base["note"] = log_error or "Logs are not available yet."
        if metadata:
            base["run"] = metadata
        return base

    if log_error:
        base["status"] = "log_unavailable"
        base["error"] = log_error
        if metadata:
            base["run"] = metadata
        return base

    snippet = extract_failure_snippet(log_text, max_lines=max_lines, context=context)
    base["status"] = "ok"
    base["run"] = metadata or {}
    base["logSnippet"] = snippet
    base["logTail"] = tail_lines(log_text, max_lines)
    return base


def extract_run_id(url: str) -> str | None:
    if not url:
        return None
    for pattern in (r"/actions/runs/(\d+)", r"/runs/(\d+)"):
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def extract_job_id(url: str) -> str | None:
    if not url:
        return None
    match = re.search(r"/actions/runs/\d+/job/(\d+)", url)
    if match:
        return match.group(1)
    match = re.search(r"/job/(\d+)", url)
    if match:
        return match.group(1)
    return None


def fetch_run_metadata(run_id: str, repo_root: Path, repo_slug: str) -> dict[str, Any] | None:
    fields = [
        "conclusion",
        "status",
        "workflowName",
        "name",
        "event",
        "headBranch",
        "headSha",
        "url",
    ]
    result = run_gh_command(
        ["run", "view", run_id, "--json", ",".join(fields)],
        cwd=repo_root,
        gh_repo=repo_slug,
    )
    if result.returncode != 0:
        return None
    try:
        data = json.loads(result.stdout or "{}")
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    return data


def fetch_check_log(
    run_id: str,
    job_id: str | None,
    repo_root: Path,
    repo_slug: str,
) -> tuple[str, str, str]:
    log_text, log_error = fetch_run_log(run_id, repo_root, repo_slug)
    if not log_error:
        return log_text, "", "ok"

    if is_log_pending_message(log_error) and job_id:
        job_log, job_error = fetch_job_log(job_id, repo_root, repo_slug)
        if job_log:
            return job_log, "", "ok"
        if job_error and is_log_pending_message(job_error):
            return "", job_error, "pending"
        if job_error:
            return "", job_error, "error"
        return "", log_error, "pending"

    if is_log_pending_message(log_error):
        return "", log_error, "pending"

    return "", log_error, "error"


def fetch_run_log(run_id: str, repo_root: Path, repo_slug: str) -> tuple[str, str]:
    result = run_gh_command(["run", "view", run_id, "--log"], cwd=repo_root, gh_repo=repo_slug)
    if result.returncode != 0:
        error = (result.stderr or result.stdout or "").strip()
        return "", error or "gh run view failed"
    return result.stdout, ""


def fetch_job_log(job_id: str, repo_root: Path, repo_slug: str) -> tuple[str, str]:
    endpoint = f"/repos/{repo_slug}/actions/jobs/{job_id}/logs"
    returncode, stdout_bytes, stderr = run_gh_command_raw(
        ["api", endpoint], cwd=repo_root, gh_repo=repo_slug
    )
    if returncode != 0:
        message = (stderr or stdout_bytes.decode(errors="replace")).strip()
        return "", message or "gh api job logs failed"
    if is_zip_payload(stdout_bytes):
        return "", "Job logs returned a zip archive; unable to parse."
    return stdout_bytes.decode(errors="replace"), ""


def fetch_repo_slug(repo_root: Path) -> str | None:
    result = run_gh_command(["repo", "view", "--json", "nameWithOwner"], cwd=repo_root)
    if result.returncode != 0:
        return None
    try:
        data = json.loads(result.stdout or "{}")
    except json.JSONDecodeError:
        return None
    name_with_owner = data.get("nameWithOwner")
    if not name_with_owner:
        return None
    return str(name_with_owner)


def fetch_repo_info(repo_root: Path) -> dict[str, Any] | None:
    result = run_gh_command(
        ["repo", "view", "--json", "nameWithOwner,isFork,parent"],
        cwd=repo_root,
    )
    if result.returncode != 0:
        return None
    try:
        data = json.loads(result.stdout or "{}")
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    return data


def parse_parent_slug(repo_info: dict[str, Any]) -> str | None:
    parent = repo_info.get("parent")
    if not isinstance(parent, dict):
        return None
    name_with_owner = parent.get("nameWithOwner")
    if name_with_owner:
        return str(name_with_owner)
    owner = parent.get("owner")
    name = parent.get("name")
    login = owner.get("login") if isinstance(owner, dict) else None
    if login and name:
        return f"{login}/{name}"
    return None


def current_branch(repo_root: Path) -> str | None:
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=repo_root,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        return None
    branch = result.stdout.strip()
    if not branch or branch == "HEAD":
        return None
    return branch


def parse_repo_from_pr_url(url: str) -> str | None:
    match = re.search(r"github\.com/([^/]+/[^/]+)/pull/\d+", url)
    if not match:
        return None
    return match.group(1)


def normalize_field(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()


def parse_available_fields(message: str) -> list[str]:
    if "Available fields:" not in message:
        return []
    fields: list[str] = []
    collecting = False
    for line in message.splitlines():
        if "Available fields:" in line:
            collecting = True
            continue
        if not collecting:
            continue
        field = line.strip()
        if not field:
            continue
        fields.append(field)
    return fields


def is_log_pending_message(message: str) -> bool:
    lowered = message.lower()
    return any(marker in lowered for marker in PENDING_LOG_MARKERS)


def is_zip_payload(payload: bytes) -> bool:
    return payload.startswith(b"PK")


def extract_failure_snippet(log_text: str, max_lines: int, context: int) -> str:
    lines = log_text.splitlines()
    if not lines:
        return ""

    marker_index = find_failure_index(lines)
    if marker_index is None:
        return "\n".join(lines[-max_lines:])

    start = max(0, marker_index - context)
    end = min(len(lines), marker_index + context)
    window = lines[start:end]
    if len(window) > max_lines:
        window = window[-max_lines:]
    return "\n".join(window)


def find_failure_index(lines: Sequence[str]) -> int | None:
    for idx in range(len(lines) - 1, -1, -1):
        lowered = lines[idx].lower()
        if any(marker in lowered for marker in FAILURE_MARKERS):
            return idx
    return None


def tail_lines(text: str, max_lines: int) -> str:
    if max_lines <= 0:
        return ""
    lines = text.splitlines()
    return "\n".join(lines[-max_lines:])


def render_results(repo_slug: str, pr_number: str, results: Iterable[dict[str, Any]]) -> None:
    results_list = list(results)
    print(f"{repo_slug} PR #{pr_number}: {len(results_list)} failing checks analyzed.")
    for result in results_list:
        print("-" * 60)
        print(f"Check: {result.get('name', '')}")
        if result.get("detailsUrl"):
            print(f"Details: {result['detailsUrl']}")
        run_id = result.get("runId")
        if run_id:
            print(f"Run ID: {run_id}")
        job_id = result.get("jobId")
        if job_id:
            print(f"Job ID: {job_id}")
        status = result.get("status", "unknown")
        print(f"Status: {status}")

        run_meta = result.get("run", {})
        if run_meta:
            branch = run_meta.get("headBranch", "")
            sha = (run_meta.get("headSha") or "")[:12]
            workflow = run_meta.get("workflowName") or run_meta.get("name") or ""
            conclusion = run_meta.get("conclusion") or run_meta.get("status") or ""
            print(f"Workflow: {workflow} ({conclusion})")
            if branch or sha:
                print(f"Branch/SHA: {branch} {sha}")
            if run_meta.get("url"):
                print(f"Run URL: {run_meta['url']}")

        if result.get("note"):
            print(f"Note: {result['note']}")

        if result.get("error"):
            print(f"Error fetching logs: {result['error']}")
            continue

        snippet = result.get("logSnippet") or ""
        if snippet:
            print("Failure snippet:")
            print(indent_block(snippet, prefix="  "))
        else:
            print("No snippet available.")
    print("-" * 60)


def indent_block(text: str, prefix: str = "  ") -> str:
    return "\n".join(f"{prefix}{line}" for line in text.splitlines())


if __name__ == "__main__":
    raise SystemExit(main())
