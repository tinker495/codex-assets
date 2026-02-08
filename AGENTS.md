# AGENTS.md

이 저장소는 **Codex 로컬 데이터의 미러(mirror)** 입니다.
직접 개발/편집 대상이 아니며, 원본은 `~/.codex` 아래에 있습니다.

## Repository Intent
- 목적: Codex 자산 백업 및 GitHub 동기화
- 범위:
  - `skills/` <- `~/.codex/skills`
  - `automations/` <- `~/.codex/automations`

## Non-Negotiable Rules
- `skills/`, `automations/` 내부 파일을 이 저장소에서 직접 수정하지 않는다.
- 미러 내부에서 원본 로직/설정 변경을 시도하지 않는다.
- Codex 내부 설정/상태 파일(`~/.codex` 하위)을 이 저장소 기준으로 직접 조작하라고 지시하지 않는다.
- 기능 변경은 반드시 **원본 경로**에서 수행한 뒤 미러 동기화로 반영한다.

## Source of Truth
- Skills source: `~/.codex/skills`
- Automations source: `~/.codex/automations`
- Mirror repo: `/Users/mrx-ksjung/project/codex-skills`

## Allowed Operations In This Repo
- 동기화 스크립트 실행
  - `./scripts/sync_and_push.sh`
  - `./scripts/install_launch_agent.sh`
  - `./scripts/launch_agent_status.sh`
  - `./scripts/uninstall_launch_agent.sh`
- README/운영문서(루트 문서) 업데이트

## Required Workflow
1. 원본(`~/.codex/skills`, `~/.codex/automations`)에서만 실제 변경 수행
2. 미러 저장소에서 `./scripts/sync_and_push.sh --repo tinker495/codex-assets` 실행
3. GitHub 반영 확인

## Quick Mental Model
```text
~/.codex/skills        ~/.codex/automations
       \                     /
        \                   /
         -> this mirror repo (read-only mirror intent)
                 -> GitHub backup/sync
```
