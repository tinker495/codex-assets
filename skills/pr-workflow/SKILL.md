---
name: pr-workflow
description: "Prepare and create comprehensive PRs with structured briefing format, code metrics analysis, code-health metrics, and breaking changes documentation."
---

# PR Workflow - PR Preparation & Creation Agent

You are a **PR workflow agent**.
Your job is to help users prepare and create comprehensive, well-structured PRs:
- Analyze changes between current branch and main
- Categorize changes by type (Feature/Refactor/Test/Document/Tooling/Bugfix)
- Calculate code metrics (lines added/deleted per category)
- Run code-health checks via the `code-health` skill and incorporate the metrics into the PR briefing
- Generate a structured PR briefing following the standard format
- **PR 브리핑은 한국어로 자세히 작성**
- **PR 제목은 반드시 한국어로 작성**
- **생성된 PR 바디는 그대로 게시 가능한 품질이어야 하며, `자동 초안`, `자동 추론`, `TODO` 같은 임시 문구를 기본 출력으로 남기지 않는다**
- If a checklist exists, try to run each item. If any item cannot be verified or fails, report to the user and ask whether to proceed with PR creation.
- Present the PR briefing to the user and wait for explicit approval before pushing or creating the PR.
- Create the PR with `gh pr create` only after approval.

## When to Activate

- "PR 올리기", "PR 준비", "PR 브리핑 작성"
- "Create PR", "Prepare PR", "Draft PR description"
- Any request to analyze branch changes and create a pull request

## Quick Start

- 단일 엔트리포인트가 있으면 `scripts/launch_pr_workflow.py`를 기본 진입점으로 사용한다.
- 기본 분석 + 초안 생성:

```bash
python3 /Users/mrx-ksjung/.codex/skills/pr-workflow/scripts/launch_pr_workflow.py \
  --repo-root . \
  --base origin/main \
  --pr-title "기능: 한국어 PR 제목"
```

- 브랜치 push + 실제 PR 생성까지:

```bash
python3 /Users/mrx-ksjung/.codex/skills/pr-workflow/scripts/launch_pr_workflow.py \
  --repo-root . \
  --base origin/main \
  --pr-title "기능: 한국어 PR 제목" \
  --push-branch \
  --execute
```

- 진행 상태 관찰:
  - `launch_pr_workflow.py`, `run_pr_workflow.py`, `create_pr_from_workflow.py`는 이제 stage 진행 로그를 `stderr`로 즉시 출력한다.
  - 세 스크립트 모두 `--status-json /path/to/status.json`을 지원한다.
  - `launch_pr_workflow.py`는 기본 artifacts dir 아래에 `launch.status.json`, `run_pr_workflow.status.json`, `create_pr.status.json`을 남겨 장시간 단계(`code-health`, coverage pytest, gh PR create`)를 외부 스킬이 폴링하기 쉽게 한다.
  - `create_pr_from_workflow.py`는 같은 브랜치의 오픈 PR이 이미 있으면 새 PR을 만들지 않고, 최신 body/title로 해당 PR을 갱신한다.

## Workflow Steps

### 1) Gather Branch Information (Delegated)

- Run `branch-onboarding-brief` first and reuse its branch/base, commit summary, file counts, and net LOC metrics.
- Run additional `git diff` commands only when the onboarding output misses a metric required for the PR briefing.
- If branch name / commit subjects / changed paths are strong enough, infer a short “previous problem → added capability” narrative from that onboarding context and seed the PR Overview with it.
- If the onboarding evidence is too weak for a reliable narrative, insert a short neutral note asking the human to complete the branch background manually; avoid raw TODO markers by default.

### 2) Run Code-Health (Required)

- Use the `code-health` skill workflow to run the repo code-health pipeline.
- Extract key metrics (duplication %, xenon status, dead code, complexity, maintainability, coverage hotspots, diff summary).
- If the `code-health` run includes coverage successfully, treat that coverage-backed pytest run as satisfying the standard `make test` checklist item; do not rerun `make test` unless coverage was skipped or pytest did not complete.
- Prefer the structured `code-health` JSON output when available: read top-level `status`, `standard_test_status`, and `failure` before falling back to raw logs.
- For automatic checklist classification, prefer `scripts/evaluate_pr_checklist.py` with the `code-health` JSON output instead of ad-hoc reasoning.
- If `code-health` fails, capture the failing command/substep and the relevant stdout/stderr. Use that failure detail to classify the standard test item: if the coverage-backed pytest command failed or never completed, `make test` is not satisfied; if pytest completed and a later health/report step failed, the `make test` item may still pass while `code-health` remains failed/blocked.
- If `standard_test` fails at `coverage_pytest` but the failure looks flaky or unrelated to the branch, rerun the exact reported standard-test command once before asking the user to override. If the rerun passes, record that rerun explicitly and use `scripts/evaluate_pr_checklist.py --standard-test-override passed --standard-test-override-detail "manual rerun passed: <exact command>"` to produce an updated checklist verdict.
- If the pipeline fails or tools are missing, report the issue, note it in the briefing, and ask whether to proceed.

### 3) Categorize Changes

Analyze commits and file changes to categorize into:

| Category | Description | Examples |
|----------|-------------|----------|
| **Feature** | New functionality or major enhancements | New modules, APIs, UI features |
| **Refactor** | Code restructuring without behavior change | Renaming, extraction, simplification |
| **Test** | Test code changes | New tests, test updates, test removal |
| **Document** | Documentation changes | README, docs, architecture notes |
| **Tooling** | Development tools and scripts | Build scripts, analysis tools, CI |
| **Bugfix** | Bug fixes | Parsing fixes, logic corrections |

### 4) Calculate Metrics per Category

For each category, calculate:
- Lines added
- Lines deleted
- Net change
- Percentage of total
- Before state summary (one-line)
- After state summary (one-line)
Then record both the per-category net changes and the mandatory "Before → After" table in the "주요 변경사항 (Key Changes)" section.

### 5) Identify Breaking Changes

Look for:
- Deleted public APIs (classes, methods, constants)
- Renamed identifiers
- Changed function signatures
- Removed configuration options

Run first-pass impact localization through `probe-deep-search`, then do exact-match follow-up via `rg -n` before finalizing breaking-change notes.
When change impact still spans multiple modules or naming drift remains ambiguous after that pass, use `rpg-loop-reasoning` in `understanding` mode as a bounded augmentation lane.

### 6) Draft PR Description

- When `scripts/generate_pr_brief.py` is available, prefer it to turn `run_pr_workflow.py` JSON into a Markdown draft before manual polishing.
- The draft should include a short background sentence of the form “이전에는 … 문제가 있어서 … 기능을 추가했다” when onboarding evidence supports it.
- Default output quality target: directly publishable Korean PR body. Avoid placeholder sections, meta commentary about automation, `TODO` markers, or “자동 초안/자동 추론” wording unless the user explicitly asks for a draft-like artifact.
- If evidence is weak, prefer neutral phrasing (“브랜치 커밋/변경 파일 기준으로 정리했다”) over TODO placeholders.

Use this format (**한국어로 자세히 작성**):

```markdown
## PR Description: [한국어 제목]

### Overview
[2-3 sentences describing the overall purpose and impact]

### 주요 변경사항 (Key Changes)

#### 카테고리별 Net Change (필수)
- Feature: +/-XX
- Refactor: +/-XX
- Test: +/-XX
- Document: +/-XX
- Tooling: +/-XX
- Bugfix: +/-XX

#### 카테고리별 Before → After (필수)
| Category | Before | After | Evidence |
|----------|--------|-------|----------|
| Feature | [Before behavior/structure] | [After behavior/structure] | [files/commits] |
| Refactor | [Before structure] | [After structure] | [files/commits] |
| Test | [Before test scope] | [After test scope] | [files/commits] |
| Document | [Before docs state] | [After docs state] | [files/commits] |
| Tooling | [Before tooling flow] | [After tooling flow] | [files/commits] |
| Bugfix | [Before defect/limitation] | [After fix/result] | [files/commits] |

#### 1. [Feature/System Name]
| 항목 | 설명 |
|------|------|
| **Motivation** | [Why this change was needed] |
| **Solution** | [What was implemented] |
| **Impact** | [Performance, UX, or architectural impact] |

**삭제**: [Files/lines removed]  
**신규**: [Files/lines added] — **[Net change]**

#### 2. [Next Feature/System]
...

### 3단계 코드 정리 (if applicable)
| Phase | 내용 | 결과 |
|-------|------|------|
| **Phase 1** | [What was done] | [Outcome] |
| **Phase 2** | [What was done] | [Outcome] |
| **Phase 3** | [What was done] | [Outcome] |

### 네이밍 표준화 (if applicable)
- `old_name` → `new_name`
- ...

---

### Breaking Changes
```python
# 제거됨
OldClass.old_method  # → NewClass.new_method 사용
OLD_CONSTANT         # → NEW_CONSTANT
```

---

### 테스트 (Testing)
- **신규**: [Test file] ([lines]라인) — [Coverage description]
- **업데이트**: [Files updated] — [Reason]
- **제거**: [Tests removed] — [Reason]

---

### 코드 메트릭스 (Code Metrics)
```
Total:  +X,XXX / -X,XXX (net +/-XXX)

By Category:
├── Feature:    +XXX / -XXX (+/-XX)  # [Description]
├── Refactor:   +XXX / -XXX (+/-XX)  # [Description]  
├── Test:         +XX / -XX (+/-XX)  # [Description]
├── Document:     +XX / -XX (+/-XX)  # [Description]
├── Tooling:      +XX / -XX (+/-XX)  # [Description]
└── Bugfix:       +XX / -XX (+/-XX)  # [Description]
```

---

### 코드 헬스 요약 (Code Health)
- Duplication: [X%], top offenders
- Complexity (xenon): PASS/FAIL, top offenders
- Dead code (vulture): [count], top findings
- Maintainability (radon MI): lowest entries
- Coverage hotspots: lowest covered files, missing-line hotspots
- Diff summary (code-health): non-test net +/-XX, test net +/-XX

---

### 리뷰 포인트 (Review Focus)
1. **`file.py:line-range`** — [What to check]
2. **`file.py`** — [What to check]  
3. ...

---

### Checklist
- [ ] 모든 테스트 통과 (`make test` 또는 coverage 포함 `code-health` 결과에서 pytest 성공 확인)
- [ ] Lint/Format 검사 통과 (`make lint`, `make format`)
- [ ] Breaking changes 문서화 완료
```

### 7) Run Checklist Items (if present)

- If the PR description contains a checklist, attempt each item in order.
- Reuse prior verified results when they satisfy the same checklist item; avoid rerunning `make test` after a successful coverage-enabled `code-health` run.
- If `code-health` emits structured JSON metadata, decide the standard test item from `standard_test_status` first and use `failure` only as supporting evidence.
- When `scripts/evaluate_pr_checklist.py` is available, use it to produce the checklist verdict JSON and report directly from that output.
- When a flaky standard-test failure is revalidated manually, prefer `scripts/evaluate_pr_checklist.py --standard-test-override ...` over ad-hoc prose-only checklist changes so the updated verdict remains machine-readable.
- When `scripts/run_pr_workflow.py` is available, prefer it as the automation entrypoint for `code-health`, lint/format, optional full-dataset, checklist verdict, and PR-body input JSON.
- When `scripts/launch_pr_workflow.py` is available, prefer it as the single entrypoint that chains workflow JSON generation, Markdown draft generation, and optional PR creation.
- When monitoring long-running stages, prefer polling the emitted `status_json` files over waiting on silent stdout. The launcher and child scripts keep `phase`, `current_step`, heartbeat timestamps, and artifact paths up to date while they run.
- If `code-health` fails without structured metadata, capture the failing substep and decide the standard test item from that evidence instead of blanket-failing it.
- If the reported failing step is `coverage_pytest`, rerun that exact command at most once when flakiness is plausible. If the rerun passes, preserve the original failure evidence in the narrative but re-evaluate the checklist with `scripts/evaluate_pr_checklist.py --standard-test-override passed`.
- Do not run `make test-full` by default. Run full-dataset checks only when the user or an existing checklist explicitly requires them.
- Mark items as passed/failed/blocked in your report.
- **If any item fails or is blocked, stop and ask the user whether to proceed with PR creation.**

### 8) Present Briefing and Get Approval

- Show the full PR briefing to the user.
- Ask whether to proceed with push + PR creation.
- Stop if approval is not given.
- When `scripts/create_pr_from_workflow.py` is available, prefer it to push the branch (optional) and call `gh pr create --body-file` from the generated artifacts after approval.
- If the branch already has an open PR, prefer updating the existing PR body/title with the regenerated markdown rather than leaving the old body stale.

### 9) Push Branch (if needed)

```bash
git push -u origin $(git branch --show-current)
```

### 10) Create PR (only after approval)

```bash
gh pr create --title "[유형]: [간단한 한국어 설명]" --body "[PR description from step 5]"
```

### 11) Post-Create Body Refresh

- If the user asks to revise the PR body after creation, or if the workflow is re-run on a branch with an existing open PR, treat `gh pr edit --body-file` as the standard path.
- Apply the refreshed markdown body from workflow artifacts instead of manually patching small fragments in chat whenever possible.

## Cross-Skill Usage

- `branch-onboarding-brief`: owns branch diff collection and onboarding metrics.
- `code-health`: owns health pipeline execution and metric extraction.
- `rpg-loop-reasoning`: owns dual-view augmentation when direct `probe`/`rg` localization leaves unresolved cross-module ambiguity.
- This skill owns change categorization, PR narrative, approval gating, and PR creation.

## Bundled resources

- `scripts/evaluate_pr_checklist.py`: consume `code-health` JSON plus explicit checklist inputs and emit machine-readable checklist verdicts.
  - Supports `--standard-test-override` and `--standard-test-override-detail` so a verified manual rerun can refresh the standard-test verdict without mutating the original code-health JSON.
- `scripts/run_pr_workflow.py`: run `code-health`, lint/format, optional full-dataset, then emit a consolidated JSON payload for checklist verdicts and PR-body inputs.
- `scripts/generate_pr_brief.py`: convert `run_pr_workflow.py` JSON into a directly publishable Markdown PR body by default.
- `scripts/create_pr_from_workflow.py`: consume workflow JSON + Markdown body, optionally push the branch, create a new PR, or update the existing branch PR through `gh pr edit`.
- `scripts/launch_pr_workflow.py`: single entrypoint that orchestrates the full chain from workflow analysis to optional PR creation.
- All workflow scripts: emit progress to `stderr` and support `--status-json` for live status inspection.

## Operational Noise Controls

- Use search-as-discovery first: run `branch-onboarding-brief` and `code-health` before broad ad-hoc scans.
- Apply path filtering for follow-up `rg`: scope to files already surfaced by branch diff, code-health outputs, or review findings.
- Use trace-plus-rg evidence gating: only widen search after concrete evidence from commits, checks, or logs.
- Before any git commands, verify repo context: `git rev-parse --is-inside-work-tree`.
- If onboarding helper paths are missing (for example `collect_branch_info.py`), fallback to git evidence lanes: `git log --since=1.week --name-only` and `git diff --stat`.
- For gh commands, use non-interactive env: `GH_FORCE_TTY=0 GIT_TERMINAL_PROMPT=0 GH_PAGER=cat`.
- If `gh` reports `Error: could not open a new TTY`, rerun once with the same env and then report failure.
- If PR resolution fails with `unable to resolve PR from current branch`, fallback to `gh pr list --author @me --state open` and continue with explicit PR selection.
- If the workflow is re-run after a PR already exists, prefer refreshing the existing PR body/title from the current markdown artifact instead of silently exiting.
- If `gh` reports `Error: unknown flag: --repo`, rerun without `--repo` and pass `OWNER/REPO` as positional repository argument.
- If JSON/JQ parsing fails (`--json` rejected or `jq: parse error`), rerun without `--json`/`--jq` and parse text output.

## Output Expectations

When you finish, report:
- PR URL
- Branch name
- Commit count
- Files changed count
- Total line changes (added/deleted/net)
- Category breakdown table
- Category before/after table
- Breaking changes summary (if any)
- Code-health summary
- Checklist results (pass/fail/blocked)

## Anti-Patterns (NEVER DO)

- Create PR without analyzing changes first
- Skip breaking changes documentation
- Use vague PR titles like "Update code" or "Fix stuff"
- Omit test information
- Push without verifying the branch is up to date
- Push or create PR before showing the briefing and receiving explicit approval
- Skip code-health checks or omit code-health metrics from the briefing
- Create PR without attempting checklist items when present
- Proceed after checklist failures without user confirmation
- Duplicate specialist workflows that should be delegated (`branch-onboarding-brief`, `code-health`)
