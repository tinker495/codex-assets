# PR Workflow Reference

## Publishable Korean PR body

A generated PR body is not done until it can be pasted into GitHub without cleanup. Use this structure unless a repository-specific template overrides it:

```markdown
## PR Description: <한국어 제목>

### Overview
<2-3 sentences: previous problem, branch intent, user-visible or architecture impact.>

### 주요 변경사항 (Key Changes)

#### 카테고리별 Net Change
- Feature: +N
- Refactor: +N
- Test: +N
- Document: +N
- Tooling: +N
- Bugfix: +N

#### 카테고리별 Before -> After
| Category | Before | After | Evidence |
|----------|--------|-------|----------|
| Feature | <baseline behavior> | <new behavior> | <files/commits> |
| Refactor | <old structure> | <new structure> | <files/commits> |
| Test | <old coverage> | <new coverage> | <files/commits> |
| Document | <old docs> | <new docs> | <files/commits> |
| Tooling | <old tooling> | <new tooling> | <files/commits> |
| Bugfix | <defect/limit> | <fix/result> | <files/commits> |

### Breaking Changes
- None, or list removed APIs, renamed symbols, signature/config changes, and migration guidance.

### 테스트 (Testing)
- `<command>`: passed/failed/blocked, with short evidence.

### 코드 헬스 요약 (Code Health)
- Status, standard test status, duplication, complexity, dead code, maintainability, coverage hotspots, and diff summary.

### 리뷰 포인트 (Review Focus)
1. `<file:line-range>` — <specific reviewer concern>

### Checklist
- [ ] 모든 테스트 통과
- [ ] Lint/Format 검사 통과
- [ ] Breaking changes 문서화 완료
```

Rules:
- Title and body are Korean by default.
- If current-branch changes include `CONTEXT.md` or `docs/adr/*.md`, read them before drafting and anchor the Overview, decisions, constraints, and review focus on those docs first.
- Use branch history, commit subjects, diff stats, changed files, code-health, and validation evidence to fill any parts not covered by CONTEXT/ADR.
- Avoid unsupported claims; every body claim should trace to CONTEXT/ADR, commits, diff evidence, or validation output.
- Remove placeholder, draft-only, and automation-meta wording before publish.
- If evidence is weak, say what branch/diff evidence supports and what remains unverified.

## Checklist semantics

Use `scripts/evaluate_pr_checklist.py` when possible.

Required statuses:
- `passed`: verified by command output or structured artifact.
- `failed`: command ran and failed.
- `blocked`: required evidence could not be collected or a prerequisite failed.
- `not_run`: not attempted yet; publish is blocked for required items.
- `not_required`: explicitly out of scope.

Standard test item:
- `code_health.standard_test_status=passed` satisfies it.
- `standard_test_status=failed` fails it unless an exact rerun passes and is recorded as a manual override.
- `standard_test_status=not_run` blocks it until a replacement test command is run.

Nonpassing publish:
- Never hide failed/blocked required items.
- Use `--allow-nonpassing` only with explicit user approval and include the rationale in the final report.

## Stacked PR playbook

1. Identify branch stack candidates from current branch name, upstream, open PRs, CONTEXT/ADR changes when present, commit subjects, and recent base branches.
2. For each plausible base, compare fork point, commit count, file count, and diff shape.
3. Prefer the base that yields the narrowest branch-local diff matching the user’s stated stack.
4. Record base/head evidence in the PR body or final report.
5. Before publish, ensure `gh pr create --base <base> --head <head>` matches the proven topology.

## Script examples

Generate artifacts only:

```bash
python3 <skill-dir>/scripts/launch_pr_workflow.py \
  --repo-root . \
  --base origin/main \
  --pr-title "한국어 PR 제목" \
  --artifacts-dir .codex_tmp/pr-workflow/current
```

Run a repo-specific real-data gate:

```bash
python3 <skill-dir>/scripts/launch_pr_workflow.py \
  --repo-root . \
  --pr-title "한국어 PR 제목" \
  --require-full-dataset \
  --full-dataset-cmd "make test-real-data"
```

Create or update after approval:

```bash
python3 <skill-dir>/scripts/create_pr_from_workflow.py \
  --repo-root . \
  --workflow-json .codex_tmp/pr-workflow/current/pr_workflow.json \
  --body-markdown .codex_tmp/pr-workflow/current/pr_brief.md \
  --push-branch \
  --execute
```

## Troubleshooting

- Missing `collect_branch_info.py`: use git fallback evidence (`git log`, `git diff --stat`, `git diff --numstat`, `git merge-base`).
- `gh` TTY errors: rerun with `GH_FORCE_TTY=0 GIT_TERMINAL_PROMPT=0 GH_PAGER=cat`.
- Existing open PR: update title/body from the Markdown artifact; do not create a duplicate.
- Generator emits a weak title/body: pass `--pr-title`, manually polish `pr_brief.md`, then publish that artifact.
- Long-running stage: poll `launch.status.json`, `run_pr_workflow.status.json`, or `create_pr.status.json`.
