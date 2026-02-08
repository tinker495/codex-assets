---
name: plan-save-load
description: Manage git-aware markdown work plans outside the repository. Use when a user asks to create/save/load a plan, resume prior work, complete and archive a finished plan, inspect active vs archived status, reopen archived plans, keep planning files out of the repo, restore the latest branch plan, separate plans by scenario group, tag plans with issue/ticket IDs, or garbage-collect stale plans from /tmp.
---

# Plan Save Load

Use `scripts/plan_save_load.py` to manage plan markdown files in `/tmp/plan-save-load`.

## Trigger Phrases

- "계획 생성/저장/불러오기"
- "레포 안 더럽히지 말고 플랜 저장"
- "이 브랜치 최신 플랜 다시 열기"
- "PR 코멘트 대응 계획 이어서 진행"
- "핫픽스/디버깅 플랜 복구"
- "티켓 붙여서 플랜 관리"
- "중요 플랜 archive 하고 오래된 것 정리"
- "계획 끝났으니 완료 처리하고 아카이브"
- "아카이브에서 다시 꺼내서 재개"
- "현재 active/archived 상태 확인"
- "티켓 없으면 진행 금지하고 관리"
- "긴급 상황에서 정책 예외 1회 허용"

## Quick Start

1. Create a plan for the current branch.
```bash
python scripts/plan_save_load.py create --repo-dir /path/to/repo --plan-group feature-work
```
2. Save markdown content.
```bash
cat updated_plan.md | python scripts/plan_save_load.py save --repo-dir /path/to/repo --plan-group feature-work --stdin --latest
```
3. Resume latest matching plan.
```bash
python scripts/plan_save_load.py load --repo-dir /path/to/repo --plan-group feature-work --latest
```
4. Complete and archive after work is done.
```bash
python scripts/plan_save_load.py complete --repo-dir /path/to/repo --plan-group feature-work --latest --summary "tests passed and PR merged" --move
```
5. Check active/archived state.
```bash
python scripts/plan_save_load.py status --repo-dir /path/to/repo --plan-group feature-work
```
6. Reopen archived plan if follow-up work appears.
```bash
python scripts/plan_save_load.py reopen --repo-dir /path/to/repo --plan-group feature-work --latest --reason "follow-up regression"
```
7. Enforce ticket discipline for regulated or team handoff work.
```bash
python scripts/plan_save_load.py create --repo-dir /path/to/repo --plan-group hotfix --require-ticket --ticket INC-214
```
8. Use one-time policy exemption only for emergencies.
```bash
python scripts/plan_save_load.py create --repo-dir /path/to/repo --plan-group hotfix --policy-exempt --policy-exempt-reason "ticket pending from incident bridge"
```

## Scenario Playbooks

1. Hotfix incident response
```bash
python scripts/plan_save_load.py create --repo-dir /path/to/repo --plan-group hotfix --ticket INC-214 --issue-id INC-214 --base-branch main
python scripts/plan_save_load.py load --repo-dir /path/to/repo --plan-group hotfix --ticket INC-214 --latest
```
2. Benchmark/performance loops
```bash
python scripts/plan_save_load.py create --repo-dir /path/to/repo --plan-group perf-benchmark --ticket PERF-88
python scripts/plan_save_load.py save --repo-dir /path/to/repo --plan-group perf-benchmark --ticket PERF-88 --stdin --append --latest
```
3. Regression/bisect trace
```bash
python scripts/plan_save_load.py create --repo-dir /path/to/repo --plan-group bisect --ticket REG-531
python scripts/plan_save_load.py list --repo-dir /path/to/repo --plan-group bisect --ticket REG-531
```
4. PR review follow-up and handoff
```bash
python scripts/plan_save_load.py create --repo-dir /path/to/repo --plan-group pr-review --ticket PR-128 --pr-id 128
python scripts/plan_save_load.py complete --repo-dir /path/to/repo --plan-group pr-review --ticket PR-128 --latest --summary "all comments resolved" --move
```
5. Release gate checklist
```bash
python scripts/plan_save_load.py create --repo-dir /path/to/repo --plan-group release-checklist --base-branch main
python scripts/plan_save_load.py complete --repo-dir /path/to/repo --plan-group release-checklist --ticket REL-2026-02 --latest --summary "release checklist done" --move
python scripts/plan_save_load.py gc --all-groups --older-than-days 14 --dry-run
```
6. Postmortem-ready incident timeline
```bash
python scripts/plan_save_load.py create --repo-dir /path/to/repo --plan-group hotfix --ticket INC-301 --issue-id INC-301
python scripts/plan_save_load.py save --repo-dir /path/to/repo --plan-group hotfix --ticket INC-301 --stdin --append --latest
python scripts/plan_save_load.py complete --repo-dir /path/to/repo --plan-group hotfix --ticket INC-301 --latest --summary "incident mitigated and RCA linked" --move
```
7. Experiment campaign closeout (benchmark batch)
```bash
python scripts/plan_save_load.py create --repo-dir /path/to/repo --plan-group perf-benchmark --ticket PERF-102
python scripts/plan_save_load.py complete --repo-dir /path/to/repo --plan-group perf-benchmark --ticket PERF-102 --latest --summary "selected config B" --move
```
8. Reopen after production feedback
```bash
python scripts/plan_save_load.py status --repo-dir /path/to/repo --plan-group pr-review --ticket PR-128
python scripts/plan_save_load.py reopen --repo-dir /path/to/repo --plan-group pr-review --ticket PR-128 --latest --reason "post-release bug report"
```

## Missing Context Checklist

When creating plans, fill these fields early:

- `Issue`/`Ticket`/`PR`
- `Base Branch`
- `Validation Commands`
- `Rollback Plan`
- `Decision Log`
- `Archive Retention` (how long to keep)
- `Reopen Criteria` (when to unarchive/resume)
- `Owner/Handoff` (who continues next)

When completing plans, add:

- completion summary (`--summary`)
- archive policy (`--move` vs copy)
- retention hint (`--retain-days`)
- reference links (PR, issue, postmortem)

## Command Notes

- `--plan-group`: Store files in `/tmp/plan-save-load/<plan-group>/`.
- `--ticket`: Add a stable token to filename and filter matching plans.
- `--require-ticket`: Fail fast unless `--ticket` is provided.
- Policy groups `hotfix`, `release-checklist`, `pr-review` enforce `--ticket` automatically.
- `--policy-exempt`: One-time bypass for policy groups only.
- `--policy-exempt-reason`: Mandatory reason string when policy exemption is used.
- `--latest`: Resolve newest file matching current repo+branch (and optional ticket).
- `complete`: Append completion metadata and archive in one command.
- `status`: Print active/archived counts and latest matching paths.
- `reopen`: Restore archived plan back to active workspace with reopen note.
- `--retain-days`: Store suggested retention period in archive metadata.
- `archive`: Copy or move a plan from `/tmp` to `~/.cache/plan-save-load/archive`.
- `gc`: Remove stale plan files older than N days.

## Rules

- Store plan files outside repositories.
- Do not store secrets, credentials, or raw customer data in plan files.
- Treat `/tmp` as ephemeral; archive long-lived plans.
- Prefer `--ticket` for continuity across rebases/cherry-picks.
- Prefer `--require-ticket` in hotfix/release/review workflows.
- `hotfix`, `release-checklist`, and `pr-review` require a ticket even without `--require-ticket`.
- Use `--policy-exempt` only for urgent temporary gaps and always record the reason.
- Keep filenames and groups sanitized to safe characters only.
