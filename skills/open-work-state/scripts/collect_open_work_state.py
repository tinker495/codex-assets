#!/usr/bin/env python3
"""Collect a read-only GitHub open issue/PR work-state snapshot.

The script intentionally depends only on Python's standard library and the
GitHub CLI (`gh`). It writes a raw JSON artifact plus a compact Markdown brief.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

Json = dict[str, Any]


class GhError(RuntimeError):
    def __init__(self, command: list[str], stderr: str, stdout: str = "") -> None:
        self.command = command
        self.stderr = stderr.strip()
        self.stdout = stdout.strip()
        super().__init__(self._message())

    def _message(self) -> str:
        detail = self.stderr or self.stdout or "no output"
        return f"command failed: {' '.join(self.command)}\n{detail}"


def gh(args: list[str], *, cwd: Path | None = None) -> str:
    env = os.environ.copy()
    env.setdefault("GH_FORCE_TTY", "0")
    env.setdefault("GH_PAGER", "cat")
    env.setdefault("GIT_TERMINAL_PROMPT", "0")
    command = ["gh", *args]
    result = subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise GhError(command, result.stderr, result.stdout)
    return result.stdout


def gh_json(args: list[str], *, cwd: Path | None = None) -> Any:
    output = gh(args, cwd=cwd).strip()
    if not output:
        return None
    return json.loads(output)


def gh_api(path: str, *, paginate: bool = False) -> Any:
    args = ["api"]
    if paginate:
        args.extend(["--paginate", "--slurp"])
    args.append(path)
    return gh_json(args)


def flatten_pages(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        flattened: list[Any] = []
        for item in value:
            if isinstance(item, list):
                flattened.extend(item)
            else:
                flattened.append(item)
        return flattened
    return [value]


def parse_repo(repo: str) -> tuple[str, str]:
    if "/" not in repo:
        raise ValueError(f"repo must be owner/name, got {repo!r}")
    owner, name = repo.split("/", 1)
    if not owner or not name:
        raise ValueError(f"repo must be owner/name, got {repo!r}")
    return owner, name


def detect_repo(cwd: Path) -> str:
    data = gh_json(["repo", "view", "--json", "nameWithOwner"], cwd=cwd)
    repo = data.get("nameWithOwner") if isinstance(data, dict) else None
    if not repo:
        raise RuntimeError("failed to detect GitHub repository via gh repo view")
    return str(repo)


def git_status(cwd: Path) -> dict[str, str]:
    def run_git(args: list[str]) -> str:
        result = subprocess.run(
            ["git", *args],
            cwd=str(cwd),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if result.returncode != 0:
            return result.stderr.strip()
        return result.stdout.strip()

    return {
        "inside_work_tree": run_git(["rev-parse", "--is-inside-work-tree"]),
        "status_short_branch": run_git(["status", "--short", "--branch"]),
        "head": run_git(["rev-parse", "--short", "HEAD"]),
        "branch": run_git(["branch", "--show-current"]),
    }


def collect_issue(repo: str, issue: Json) -> Json:
    number = issue["number"]
    comments = flatten_pages(
        gh_api(f"/repos/{repo}/issues/{number}/comments?per_page=100", paginate=True)
    )
    return {"issue": issue, "comments": comments}


def collect_check_runs(repo: str, sha: str | None) -> list[Json]:
    if not sha:
        return []
    pages = flatten_pages(
        gh_api(f"/repos/{repo}/commits/{sha}/check-runs?per_page=100", paginate=True)
    )
    runs: list[Json] = []
    for page in pages:
        if isinstance(page, dict) and isinstance(page.get("check_runs"), list):
            runs.extend(page["check_runs"])
        elif isinstance(page, dict):
            runs.append(page)
    return runs


def collect_pr_view(repo: str, number: int) -> Json:
    fields = [
        "number",
        "title",
        "url",
        "isDraft",
        "headRefName",
        "baseRefName",
        "reviewDecision",
        "mergeStateStatus",
        "statusCheckRollup",
        "closingIssuesReferences",
        "latestReviews",
        "reviewRequests",
        "updatedAt",
    ]
    return gh_json(["pr", "view", str(number), "--repo", repo, "--json", ",".join(fields)])


def collect_review_threads(owner: str, name: str, number: int) -> Json:
    query = """
    query($owner: String!, $name: String!, $number: Int!, $cursor: String) {
      repository(owner: $owner, name: $name) {
        pullRequest(number: $number) {
          reviewThreads(first: 100, after: $cursor) {
            nodes {
              id
              isResolved
              isOutdated
              path
              line
              startLine
              comments(first: 50) {
                nodes {
                  author { login }
                  body
                  createdAt
                  url
                }
              }
            }
            pageInfo { hasNextPage endCursor }
          }
        }
      }
    }
    """
    threads: list[Json] = []
    cursor = ""
    while True:
        args = [
            "api",
            "graphql",
            "-f",
            f"query={query}",
            "-f",
            f"owner={owner}",
            "-f",
            f"name={name}",
            "-F",
            f"number={number}",
        ]
        if cursor:
            args.extend(["-f", f"cursor={cursor}"])
        data = gh_json(args)
        pr = data.get("data", {}).get("repository", {}).get("pullRequest")
        if not pr:
            return {"threads": threads, "error": "pullRequest not found in GraphQL response"}
        review_threads = pr.get("reviewThreads") or {}
        threads.extend(review_threads.get("nodes") or [])
        page_info = review_threads.get("pageInfo") or {}
        if not page_info.get("hasNextPage"):
            return {"threads": threads}
        cursor = page_info.get("endCursor") or ""
        if not cursor:
            return {"threads": threads, "error": "missing GraphQL endCursor"}


def collect_pr(repo: str, owner: str, name: str, pr: Json) -> Json:
    number = pr["number"]
    detail = gh_api(f"/repos/{repo}/pulls/{number}")
    gh_pr_view: Json | None
    try:
        gh_pr_view = collect_pr_view(repo, number)
    except Exception:  # noqa: BLE001 - REST data remains the fallback source.
        gh_pr_view = None
    head_sha = (detail.get("head") or {}).get("sha") if isinstance(detail, dict) else None
    issue_comments = flatten_pages(
        gh_api(f"/repos/{repo}/issues/{number}/comments?per_page=100", paginate=True)
    )
    reviews = flatten_pages(gh_api(f"/repos/{repo}/pulls/{number}/reviews?per_page=100", paginate=True))
    review_comments = flatten_pages(
        gh_api(f"/repos/{repo}/pulls/{number}/comments?per_page=100", paginate=True)
    )
    commits = flatten_pages(gh_api(f"/repos/{repo}/pulls/{number}/commits?per_page=100", paginate=True))
    statuses = gh_api(f"/repos/{repo}/commits/{head_sha}/status") if head_sha else None
    check_runs = collect_check_runs(repo, head_sha)
    try:
        review_threads = collect_review_threads(owner, name, number)
    except Exception as exc:  # noqa: BLE001 - artifact should preserve partial data.
        review_threads = {"threads": [], "error": str(exc)}
    return {
        "pull_request": pr,
        "detail": detail,
        "gh_pr_view": gh_pr_view,
        "issue_comments": issue_comments,
        "reviews": reviews,
        "review_comments": review_comments,
        "commits": commits,
        "combined_status": statuses,
        "check_runs": check_runs,
        "review_threads": review_threads,
    }


def labels(item: Json) -> str:
    raw_labels = item.get("labels") or []
    names = [str(label.get("name")) for label in raw_labels if isinstance(label, dict) and label.get("name")]
    return ", ".join(names) if names else "-"


def assignees(item: Json) -> str:
    raw_assignees = item.get("assignees") or []
    names = [str(user.get("login")) for user in raw_assignees if isinstance(user, dict) and user.get("login")]
    return ", ".join(names) if names else "-"


def latest_review_state(reviews: list[Json]) -> str:
    latest_by_user: dict[str, str] = {}
    for review in reviews:
        user = (review.get("user") or {}).get("login") or "unknown"
        state = str(review.get("state") or "").upper()
        if state in {"APPROVED", "CHANGES_REQUESTED", "COMMENTED", "DISMISSED"}:
            latest_by_user[user] = state
    states = set(latest_by_user.values())
    if "CHANGES_REQUESTED" in states:
        return "CHANGES_REQUESTED"
    if "APPROVED" in states:
        return "APPROVED"
    if "COMMENTED" in states:
        return "COMMENTED"
    return "NONE"


def check_state(pr_data: Json) -> str:
    status_rollup = (pr_data.get("gh_pr_view") or {}).get("statusCheckRollup") or []
    if status_rollup:
        states = [
            str(item.get("conclusion") or item.get("state") or item.get("status") or "unknown").lower()
            for item in status_rollup
            if isinstance(item, dict)
        ]
        bad = {"failure", "failed", "cancelled", "timed_out", "action_required", "error"}
        if any(value in bad for value in states):
            return "failing"
        if any(value in {"queued", "in_progress", "requested", "pending", "waiting"} for value in states):
            return "pending"
        if states and all(value in {"success", "passed", "skipped", "neutral"} for value in states):
            return "passing"
    runs = pr_data.get("check_runs") or []
    if not runs:
        combined = pr_data.get("combined_status") or {}
        return str(combined.get("state") or "unknown")
    conclusions = [str(run.get("conclusion") or run.get("status") or "unknown") for run in runs]
    bad = {"failure", "cancelled", "timed_out", "action_required"}
    if any(value in bad for value in conclusions):
        return "failing"
    if any(value in {"queued", "in_progress", "requested", "pending"} for value in conclusions):
        return "pending"
    if all(value in {"success", "skipped", "neutral"} for value in conclusions):
        return "passing"
    return "mixed"


def unresolved_thread_count(pr_data: Json) -> int | str:
    review_threads = pr_data.get("review_threads") or {}
    if review_threads.get("error"):
        return "unknown"
    threads = review_threads.get("threads") or []
    return sum(1 for thread in threads if not thread.get("isResolved"))


def md_escape(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ").strip()


def issue_mentions(text: str) -> list[str]:
    import re

    return sorted(set(re.findall(r"#\d+", text or "")), key=lambda item: int(item[1:]))


def render_markdown(snapshot: Json) -> str:
    repo = snapshot["repo"]
    lines = [
        f"# Open Work State — {repo}",
        "",
        f"Captured: `{snapshot['captured_at']}`",
        f"Repo URL: {snapshot.get('repo_info', {}).get('html_url', '-')}",
        "",
        "## Counts",
        "",
        f"- Open issues: {len(snapshot['issues'])}",
        f"- Open PRs: {len(snapshot['pull_requests'])}",
        f"- Collector errors: {len(snapshot['errors'])}",
        "",
        "## Open pull requests",
        "",
        "| PR | Title | Head → Base | Draft | Review | Checks | Merge | Threads | Linked issues | Updated | URL |",
        "|---|---|---|---:|---|---|---|---:|---|---|---|",
    ]
    for pr_data in snapshot["pull_requests"]:
        pr = pr_data.get("detail") or pr_data.get("pull_request") or {}
        gh_pr_view = pr_data.get("gh_pr_view") or {}
        number = pr.get("number")
        title = md_escape(gh_pr_view.get("title") or pr.get("title") or "")
        head = md_escape(gh_pr_view.get("headRefName") or (pr.get("head") or {}).get("ref") or "?")
        base = md_escape(gh_pr_view.get("baseRefName") or (pr.get("base") or {}).get("ref") or "?")
        draft = "yes" if gh_pr_view.get("isDraft", pr.get("draft")) else "no"
        review = gh_pr_view.get("reviewDecision") or latest_review_state(pr_data.get("reviews") or [])
        checks = check_state(pr_data)
        merge = md_escape(gh_pr_view.get("mergeStateStatus") or pr.get("mergeable_state") or pr.get("mergeable") or "unknown")
        threads = unresolved_thread_count(pr_data)
        closing_refs = gh_pr_view.get("closingIssuesReferences") or []
        closing_numbers = [
            f"#{item.get('number')}"
            for item in closing_refs
            if isinstance(item, dict) and item.get("number")
        ]
        if closing_numbers:
            linked = ", ".join(closing_numbers)
        else:
            text = "\n".join(
                str(value or "")
                for value in [pr.get("title"), pr.get("body"), (pr.get("head") or {}).get("ref")]
            )
            linked = ", ".join(issue_mentions(text)) or "-"
        updated = md_escape(gh_pr_view.get("updatedAt") or pr.get("updated_at") or "")
        url = gh_pr_view.get("url") or pr.get("html_url") or ""
        lines.append(
            f"| #{number} | {title} | `{head}` → `{base}` | {draft} | {review} | {checks} | {merge} | {threads} | {linked} | {updated} | {url} |"
        )

    lines.extend([
        "",
        "## Open issues",
        "",
        "| Issue | Title | Labels | Assignees | Comments | Updated | URL |",
        "|---|---|---|---|---:|---|---|",
    ])
    for issue_data in snapshot["issues"]:
        issue = issue_data.get("issue") or {}
        lines.append(
            "| #{number} | {title} | {labels} | {assignees} | {comments} | {updated} | {url} |".format(
                number=issue.get("number"),
                title=md_escape(issue.get("title") or ""),
                labels=md_escape(labels(issue)),
                assignees=md_escape(assignees(issue)),
                comments=len(issue_data.get("comments") or []),
                updated=md_escape(issue.get("updated_at") or ""),
                url=issue.get("html_url") or "",
            )
        )

    lines.extend([
        "",
        "## Collector errors",
        "",
    ])
    if snapshot["errors"]:
        for error in snapshot["errors"]:
            lines.append(f"- `{md_escape(error.get('scope'))}`: {md_escape(error.get('error'))}")
    else:
        lines.append("- none")

    lines.extend([
        "",
        "## Artifact notes",
        "",
        "- This Markdown is a compact index. Use `open-work-state.json` as the complete source for bodies, comments, reviews, check runs, and review-thread details.",
        "- Linkage is inferred from PR text/branch mentions unless GitHub explicitly records closing references in the raw artifact.",
    ])
    return "\n".join(lines) + "\n"


def collect_snapshot(repo: str, cwd: Path) -> Json:
    owner, name = parse_repo(repo)
    errors: list[Json] = []
    repo_info: Json = {}
    try:
        repo_info = gh_api(f"/repos/{repo}")
    except Exception as exc:  # noqa: BLE001 - preserve partial snapshot.
        errors.append({"scope": "repo_info", "error": str(exc)})

    raw_issues = flatten_pages(gh_api(f"/repos/{repo}/issues?state=open&per_page=100", paginate=True))
    issues = [item for item in raw_issues if isinstance(item, dict) and "pull_request" not in item]
    pulls = flatten_pages(gh_api(f"/repos/{repo}/pulls?state=open&per_page=100", paginate=True))

    collected_issues: list[Json] = []
    for issue in issues:
        try:
            collected_issues.append(collect_issue(repo, issue))
        except Exception as exc:  # noqa: BLE001
            errors.append({"scope": f"issue#{issue.get('number')}", "error": str(exc)})
            collected_issues.append({"issue": issue, "comments": []})

    collected_prs: list[Json] = []
    for pr in pulls:
        try:
            collected_prs.append(collect_pr(repo, owner, name, pr))
        except Exception as exc:  # noqa: BLE001
            errors.append({"scope": f"pr#{pr.get('number')}", "error": str(exc)})
            collected_prs.append({"pull_request": pr})

    return {
        "captured_at": dt.datetime.now(dt.UTC).isoformat(),
        "repo": repo,
        "repo_info": repo_info,
        "git": git_status(cwd),
        "issues": collected_issues,
        "pull_requests": collected_prs,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect open GitHub issue/PR work-state artifacts.")
    parser.add_argument("--repo", help="GitHub repository in owner/name form. Defaults to gh repo view.")
    parser.add_argument("--out", default=".codex_tmp/open-work-state", help="Output directory.")
    parser.add_argument("--cwd", default=".", help="Repository root used for gh/git detection.")
    args = parser.parse_args()

    cwd = Path(args.cwd).resolve()
    repo = args.repo or detect_repo(cwd)
    out_dir = Path(args.out)
    if not out_dir.is_absolute():
        out_dir = cwd / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    snapshot = collect_snapshot(repo, cwd)
    json_path = out_dir / "open-work-state.json"
    md_path = out_dir / "open-work-state.md"
    json_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(snapshot), encoding="utf-8")
    print(f"wrote {md_path}")
    print(f"wrote {json_path}")
    if snapshot["errors"]:
        print(f"collector_errors={len(snapshot['errors'])}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
