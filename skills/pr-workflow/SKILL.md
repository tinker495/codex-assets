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
- If a checklist exists, try to run each item. If any item cannot be verified or fails, report to the user and ask whether to proceed with PR creation.
- Present the PR briefing to the user and wait for explicit approval before pushing or creating the PR.
- Create the PR with `gh pr create` only after approval.

## When to Activate

- "PR 올리기", "PR 준비", "PR 브리핑 작성"
- "Create PR", "Prepare PR", "Draft PR description"
- Any request to analyze branch changes and create a pull request

## Workflow Steps

### 1) Gather Branch Information (Delegated)

- Run `branch-onboarding-brief` first and reuse its branch/base, commit summary, file counts, and net LOC metrics.
- Run additional `git diff` commands only when the onboarding output misses a metric required for the PR briefing.

### 2) Run Code-Health (Required)

- Use the `code-health` skill workflow to run the repo code-health pipeline.
- Extract key metrics (duplication %, xenon status, dead code, complexity, maintainability, coverage hotspots, diff summary).
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

Delegate first-pass impact localization to `grepai-deep-analysis` before finalizing breaking-change notes.
When change impact still spans multiple modules or naming drift remains ambiguous after that pass, use `rpg-loop-reasoning` in `understanding` mode as a bounded augmentation lane.

### 6) Draft PR Description

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
- [ ] 모든 테스트 통과 (`make test`)
- [ ] Lint/Format 검사 통과 (`make lint`, `make format`)
- [ ] Full dataset 테스트 통과 (`make test-full`)
- [ ] Breaking changes 문서화 완료
```

### 7) Run Checklist Items (if present)

- If the PR description contains a checklist, attempt each item in order.
- Mark items as passed/failed/blocked in your report.
- **If any item fails or is blocked, stop and ask the user whether to proceed with PR creation.**

### 8) Present Briefing and Get Approval

- Show the full PR briefing to the user.
- Ask whether to proceed with push + PR creation.
- Stop if approval is not given.

### 9) Push Branch (if needed)

```bash
git push -u origin $(git branch --show-current)
```

### 10) Create PR (only after approval)

```bash
gh pr create --title "[유형]: [간단한 한국어 설명]" --body "[PR description from step 5]"
```

## Cross-Skill Usage

- `branch-onboarding-brief`: owns branch diff collection and onboarding metrics.
- `code-health`: owns health pipeline execution and metric extraction.
- `grepai-deep-analysis`: owns deep evidence protocol and first-pass impact localization for breaking-change analysis.
- `rpg-loop-reasoning`: owns dual-view augmentation when `grepai-deep-analysis` indicates unresolved cross-module ambiguity.
- This skill owns change categorization, PR narrative, approval gating, and PR creation.

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
