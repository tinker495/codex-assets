---
name: pr-workflow
description: Prepares and publishes GitHub pull requests from local branch evidence, including branch-base validation, Korean PR brief generation, checklist gating, and approval-gated push/create. Use when the user asks for $pr-workflow, PR 올리기, PR 준비, PR 브리핑, stacked PR, gh pr create/edit, or branch-to-PR delivery.
---

# PR Workflow

## Quick start

Resolve `<skill-dir>` to the directory containing this file, then run from the target repository root:

```bash
python3 <skill-dir>/scripts/launch_pr_workflow.py \
  --repo-root . \
  --pr-title "한국어 PR 제목" \
  --status-json .codex_tmp/pr-workflow/status.json
```

This creates branch evidence, code-health/checklist evidence, and a Korean Markdown PR brief without pushing or creating a PR. After explicit publish approval, use:

```bash
python3 <skill-dir>/scripts/launch_pr_workflow.py \
  --repo-root . \
  --pr-title "한국어 PR 제목" \
  --push-branch \
  --execute
```

## Required workflow

1. **Orient branch and base first.** Verify `git rev-parse --is-inside-work-tree`, current branch, dirty state, upstream, fork point, commit count, changed files, and net LOC. Use `branch-onboarding-brief` or `collect_branch_info.py` if available. For stacked PRs, prove the intended base/head topology from diff evidence; do not default to `main` when the branch is stacked.
2. **Run the automation entrypoint.** Prefer `scripts/launch_pr_workflow.py`. Use `run_pr_workflow.py` only when you need separate JSON generation, and `generate_pr_brief.py` only when you already have workflow JSON.
3. **Keep code-health required.** Capture structured code-health JSON when available. Treat `standard_test_status=passed` as satisfying the standard test item; if coverage pytest failed or never ran, the standard test item is not satisfied.
4. **Add repo-specific checks deliberately.** Run extra checks only when the branch or checklist requires them, such as docs checks for docs/AGENTS changes or real-data gates for data-contract branches. Pass the repo-specific full-dataset command explicitly instead of assuming a generic default.
5. **Produce a publish-ready Korean PR.** Title and body are Korean. When `CONTEXT.md` or `docs/adr/` files are added or changed in the branch, read those first and use them as the primary source for the PR body narrative, decisions, and constraints. Then supplement gaps from branch history, commit subjects, diff stats, and changed files. The body must be evidence-backed, directly publishable, and free of placeholder/meta automation wording. If generator output is weak, polish the Markdown artifact before publishing.
6. **Evaluate checklist before publishing.** Prefer `scripts/evaluate_pr_checklist.py` for machine-readable status. Failed or blocked required items stop push/PR creation unless the user explicitly approves a nonpassing publish.
7. **Approval gate external side effects.** Treat generic “PR 올리기” as prepare → brief → validate first. Push, PR creation, and PR body edits happen only after explicit approval for that publish/update step, or when the current user request explicitly says to push/create/update now without another approval pause.
8. **Publish through artifacts.** Prefer `scripts/create_pr_from_workflow.py` or `launch_pr_workflow.py --push-branch --execute`. If an open PR already exists for the branch, update its title/body instead of creating a duplicate.
9. **Report evidence.** Return PR URL or blocker, branch, base, commit/file/LOC counts, checklist result, key validation commands, artifact paths, and remaining risks.

## Script roles

| Script | Use |
|---|---|
| `scripts/launch_pr_workflow.py` | Single entrypoint: workflow JSON, Markdown brief, optional push/create/update. |
| `scripts/run_pr_workflow.py` | Branch evidence, code-health, lint/format, optional full-dataset, checklist JSON. |
| `scripts/evaluate_pr_checklist.py` | Deterministic checklist verdict from code-health JSON plus explicit statuses. |
| `scripts/generate_pr_brief.py` | Markdown PR body from workflow JSON; always polish before publish. |
| `scripts/create_pr_from_workflow.py` | Push branch and create/update PR from workflow JSON + Markdown. |

All workflow scripts emit progress to `stderr` and support `--status-json`; poll status files for long-running stages.

## Failure handling

- If code-health fails, preserve the failing step, command, return code, and excerpts; do not collapse it into a vague failure.
- If coverage-backed pytest looks flaky, extract the failed pytest node id(s) from the failure output/status artifacts and rerun only those failed tests at most once. If node ids are unavailable, rerun the narrowest failed file or directly implicated test slice; do not rerun the whole standard-test command just to check flakiness. Record the override with `evaluate_pr_checklist.py --standard-test-override passed --standard-test-override-detail ...` only if the targeted rerun passes. Use a full standard-test rerun only when failure evidence is truncated or infrastructure-level and no failed node/file can be identified.
- If `gh` authentication or permission fails, stop at that boundary and report the exact command/output.
- Use non-interactive GitHub env for `gh`: `GH_FORCE_TTY=0 GIT_TERMINAL_PROMPT=0 GH_PAGER=cat`.
- If `gh pr create` cannot infer the PR from the current branch, inspect open PRs for the head branch and continue with explicit base/head evidence.

## PR body contract

See [REFERENCE.md](REFERENCE.md) for the required Korean PR body sections, checklist semantics, stacked-PR playbook, and troubleshooting details.
