#!/usr/bin/env python3
"""
Fetch all PR conversation comments + reviews + review threads (inline threads)
for the PR associated with the current git branch, by shelling out to:

  gh api graphql

Supports fork-aware PR resolution:
- current repo PR first
- upstream parent PR lookup when current repo is a fork and no local PR exists
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, NamedTuple

QUERY = """\
query(
  $owner: String!,
  $repo: String!,
  $number: Int!,
  $commentsCursor: String,
  $reviewsCursor: String,
  $threadsCursor: String
) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $number) {
      number
      url
      title
      state

      comments(first: 100, after: $commentsCursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          body
          createdAt
          updatedAt
          author { login }
        }
      }

      reviews(first: 100, after: $reviewsCursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          state
          body
          submittedAt
          author { login }
        }
      }

      reviewThreads(first: 100, after: $threadsCursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          isResolved
          isOutdated
          path
          line
          diffSide
          startLine
          startDiffSide
          originalLine
          originalStartLine
          resolvedBy { login }
          comments(first: 100) {
            nodes {
              id
              body
              createdAt
              updatedAt
              author { login }
            }
          }
        }
      }
    }
  }
}
"""


class TargetPR(NamedTuple):
    repo_slug: str
    pr: int
    url: str | None = None
    source: str = "unknown"


def _run(cmd: list[str], stdin: str | None = None, cwd: Path | None = None) -> str:
    p = subprocess.run(cmd, input=stdin, capture_output=True, text=True, cwd=cwd)
    if p.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{p.stderr}")
    return p.stdout


def _run_json(cmd: list[str], stdin: str | None = None, cwd: Path | None = None) -> dict[str, Any]:
    out = _run(cmd, stdin=stdin, cwd=cwd)
    try:
        return json.loads(out)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse JSON from command output: {e}\nRaw:\n{out}") from e


def gh_cmd(args: list[str], gh_repo: str | None = None) -> list[str]:
    cmd = ["gh"]
    if gh_repo:
        cmd.extend(["-R", gh_repo])
    cmd.extend(args)
    return cmd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch PR comments/reviews/threads with fork-aware PR resolution.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--repo", default=".", help="Path inside the target Git repository.")
    parser.add_argument(
        "--pr",
        default=None,
        help="PR number or URL (defaults to current branch PR with fork-aware upstream fallback).",
    )
    parser.add_argument(
        "--gh-repo",
        default=None,
        help="GitHub repository slug (owner/repo) for PR lookup override.",
    )
    return parser.parse_args()


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


def _ensure_gh_authenticated(repo_root: Path) -> None:
    try:
        _run(gh_cmd(["auth", "status"]), cwd=repo_root)
    except RuntimeError:
        print("run `gh auth login` to authenticate the GitHub CLI", file=sys.stderr)
        raise RuntimeError(
            "gh auth status failed; run `gh auth login` to authenticate the GitHub CLI"
        ) from None


def fetch_repo_slug(repo_root: Path) -> str | None:
    try:
        data = _run_json(gh_cmd(["repo", "view", "--json", "nameWithOwner"]), cwd=repo_root)
    except RuntimeError:
        return None
    slug = data.get("nameWithOwner")
    return str(slug) if slug else None


def fetch_repo_info(repo_root: Path) -> dict[str, Any] | None:
    try:
        data = _run_json(
            gh_cmd(["repo", "view", "--json", "nameWithOwner,isFork,parent"]),
            cwd=repo_root,
        )
    except RuntimeError:
        return None
    return data if isinstance(data, dict) else None


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


def parse_pr_url(pr_value: str) -> tuple[str, int] | None:
    match = re.search(r"github\.com/([^/]+/[^/]+)/pull/(\d+)", pr_value)
    if not match:
        return None
    return match.group(1), int(match.group(2))


def resolve_explicit_pr(pr_value: str, gh_repo: str | None, repo_root: Path) -> TargetPR | None:
    parsed = parse_pr_url(pr_value)
    if parsed:
        repo_slug, number = parsed
        return TargetPR(repo_slug=repo_slug, pr=number, url=pr_value, source="explicit-url")

    if not pr_value.isdigit():
        return None

    repo_slug = gh_repo or fetch_repo_slug(repo_root)
    if not repo_slug:
        return None
    return TargetPR(repo_slug=repo_slug, pr=int(pr_value), source="explicit-number")


def resolve_current_repo_pr(repo_root: Path, gh_repo: str | None) -> TargetPR | None:
    try:
        pr = _run_json(
            gh_cmd(["pr", "view", "--json", "number,url"], gh_repo=gh_repo),
            cwd=repo_root,
        )
    except RuntimeError:
        return None

    number = pr.get("number")
    if not number:
        return None

    url = str(pr.get("url") or "")
    repo_slug = gh_repo
    if not repo_slug and url:
        parsed = parse_pr_url(url)
        repo_slug = parsed[0] if parsed else None
    if not repo_slug:
        repo_slug = fetch_repo_slug(repo_root)
    if not repo_slug:
        return None

    return TargetPR(repo_slug=repo_slug, pr=int(number), url=url or None, source="current-repo")


def resolve_upstream_pr_for_fork(repo_root: Path) -> TargetPR | None:
    info = fetch_repo_info(repo_root)
    if not info or not bool(info.get("isFork")):
        return None

    current_slug = str(info.get("nameWithOwner") or "")
    current_owner = current_slug.split("/", 1)[0] if "/" in current_slug else ""
    parent_slug = parse_parent_slug(info)
    branch = current_branch(repo_root)
    if not current_owner or not parent_slug or not branch:
        return None

    prs = fetch_upstream_pr_candidates(repo_root, parent_slug, current_owner, branch)

    if not isinstance(prs, list) or not prs:
        return None

    candidates = [p for p in prs if isinstance(p, dict) and p.get("number")]
    if not candidates:
        return None

    candidates.sort(key=lambda p: str(p.get("updatedAt") or ""), reverse=True)
    chosen = candidates[0]
    return TargetPR(
        repo_slug=parent_slug,
        pr=int(chosen["number"]),
        url=str(chosen.get("url") or "") or None,
        source="fork-upstream-head-branch",
    )


def fetch_upstream_pr_candidates(
    repo_root: Path, parent_slug: str, current_owner: str, branch: str
) -> list[dict[str, Any]] | None:
    fields = "number,url,updatedAt"
    try:
        primary = _run_json(
            gh_cmd(
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
                gh_repo=parent_slug,
            ),
            cwd=repo_root,
        )
    except RuntimeError:
        primary = []

    if isinstance(primary, list) and primary:
        return primary

    try:
        fallback = _run_json(
            gh_cmd(
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
                gh_repo=parent_slug,
            ),
            cwd=repo_root,
        )
    except RuntimeError:
        return None

    return fallback if isinstance(fallback, list) else None


def resolve_target_pr(pr_value: str | None, gh_repo: str | None, repo_root: Path) -> TargetPR | None:
    if pr_value:
        return resolve_explicit_pr(pr_value, gh_repo, repo_root)

    direct = resolve_current_repo_pr(repo_root, gh_repo)
    if direct is not None:
        return direct

    if gh_repo:
        return None

    return resolve_upstream_pr_for_fork(repo_root)


def gh_api_graphql(
    owner: str,
    repo: str,
    number: int,
    comments_cursor: str | None = None,
    reviews_cursor: str | None = None,
    threads_cursor: str | None = None,
) -> dict[str, Any]:
    cmd = [
        "gh",
        "api",
        "graphql",
        "-F",
        "query=@-",
        "-F",
        f"owner={owner}",
        "-F",
        f"repo={repo}",
        "-F",
        f"number={number}",
    ]
    if comments_cursor:
        cmd += ["-F", f"commentsCursor={comments_cursor}"]
    if reviews_cursor:
        cmd += ["-F", f"reviewsCursor={reviews_cursor}"]
    if threads_cursor:
        cmd += ["-F", f"threadsCursor={threads_cursor}"]

    return _run_json(cmd, stdin=QUERY)


def fetch_all(owner: str, repo: str, number: int) -> dict[str, Any]:
    conversation_comments: list[dict[str, Any]] = []
    reviews: list[dict[str, Any]] = []
    review_threads: list[dict[str, Any]] = []

    comments_cursor: str | None = None
    reviews_cursor: str | None = None
    threads_cursor: str | None = None

    pr_meta: dict[str, Any] | None = None

    while True:
        payload = gh_api_graphql(
            owner=owner,
            repo=repo,
            number=number,
            comments_cursor=comments_cursor,
            reviews_cursor=reviews_cursor,
            threads_cursor=threads_cursor,
        )

        if "errors" in payload and payload["errors"]:
            raise RuntimeError(f"GitHub GraphQL errors:\n{json.dumps(payload['errors'], indent=2)}")

        pr = payload["data"]["repository"]["pullRequest"]
        if pr_meta is None:
            pr_meta = {
                "number": pr["number"],
                "url": pr["url"],
                "title": pr["title"],
                "state": pr["state"],
                "owner": owner,
                "repo": repo,
            }

        c = pr["comments"]
        r = pr["reviews"]
        t = pr["reviewThreads"]

        conversation_comments.extend(c.get("nodes") or [])
        reviews.extend(r.get("nodes") or [])
        review_threads.extend(t.get("nodes") or [])

        comments_cursor = c["pageInfo"]["endCursor"] if c["pageInfo"]["hasNextPage"] else None
        reviews_cursor = r["pageInfo"]["endCursor"] if r["pageInfo"]["hasNextPage"] else None
        threads_cursor = t["pageInfo"]["endCursor"] if t["pageInfo"]["hasNextPage"] else None

        if not (comments_cursor or reviews_cursor or threads_cursor):
            break

    assert pr_meta is not None
    return {
        "pull_request": pr_meta,
        "conversation_comments": conversation_comments,
        "reviews": reviews,
        "review_threads": review_threads,
    }


def main() -> None:
    args = parse_args()
    repo_root = find_git_root(Path(args.repo))
    if repo_root is None:
        raise RuntimeError("not inside a Git repository")

    _ensure_gh_authenticated(repo_root)

    target = resolve_target_pr(args.pr, args.gh_repo, repo_root)
    if target is None:
        raise RuntimeError(
            "unable to resolve PR from current branch (current repo or upstream parent)."
        )

    owner, repo = target.repo_slug.split("/", 1)
    result = fetch_all(owner, repo, target.pr)
    result["resolution"] = {
        "repo": target.repo_slug,
        "pr": target.pr,
        "source": target.source,
        "url": target.url,
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
