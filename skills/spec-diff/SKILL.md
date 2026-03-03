---
name: spec-diff
description: Use when _TOBE.md and _ASIS.md both exist for a module and you need to identify drift between spec and code. Triggered by "스펙이랑 코드가 얼마나 다른지 비교해", "drift 확인", "스펙 drift", or when preparing refactoring scope decisions after reverse-doc completion.
---

# Spec Diff: Tobe vs As-Is Drift 리포트

## Overview

Tobe 스펙 문서(`_TOBE.md`)와 As-Is 문서(`_ASIS.md`)를 비교하여 **어디가 일치하고, 어디가 drift했는지** 리포트를 생성한다. 각 drift에 대해 처리 선택지를 제시한다. 코드를 직접 읽거나 수정하지 않는다.

## When to Use

- `_TOBE.md`와 `_ASIS.md`가 같은 모듈에 대해 존재할 때
- 리팩토링 범위를 정하기 전에 스펙과 코드의 괴리를 파악할 때
- 에이전트가 코딩한 결과가 스펙에서 얼마나 벗어났는지 추적할 때
- "스펙이랑 코드가 얼마나 다른지 비교해", "drift 확인" 요청 시

**When NOT to use:**
- `_TOBE.md` 또는 `_ASIS.md`가 없을 때 (먼저 doc-separator / reverse-doc 실행)
- 코드를 직접 분석할 때 (→ reverse-doc)
- 혼합 문서를 분리할 때 (→ doc-separator)
- "어느 쪽이 맞다"는 판단이 필요할 때 (이 스킬은 차이만 기술한다)

## Drift 분류 체계 (Quick Reference)

| 카테고리 | 의미 | 권장 조치 |
|---------|------|----------|
| `[MATCH]` | 스펙과 코드 일치 | 없음 |
| `[DRIFT-HARMLESS]` | 다르지만 기능 영향 없음 (변수명, 순서, 추가 로깅) | 스펙을 코드에 맞춰 업데이트 |
| `[DRIFT-FUNCTIONAL]` | 동작이 다름. 결과 영향 가능 (다른 알고리즘, 빠진 조건) | 테스트로 영향 확인 → 코드 수정 or 스펙 업데이트 |
| `[DRIFT-STRUCTURAL]` | 구조가 다름 (클래스 계층, 모듈 분리, 입출력 타입) | 인터페이스 재정의. 핵심이면 리팩토링 |
| `[MISSING-IN-CODE]` | 스펙에 있으나 미구현 | 필요성 판단 후 구현 or 스펙에서 제거 |
| `[MISSING-IN-SPEC]` | 코드에 있으나 스펙에 없음 (에이전트 임의 추가) | 스펙에 추가 or 코드에서 제거 |

**Drift 심각도**: STRUCTURAL 2개 이상 또는 FUNCTIONAL 5개 이상이면 HIGH.

## 출력 형식: `{module_name}_DRIFT.md`

```markdown
# {모듈명} - Drift 리포트

> 생성일: {날짜}
> Tobe 기준: {_TOBE.md 파일경로}
> As-Is 기준: {_ASIS.md 파일경로}

## 요약

| 카테고리 | 건수 |
|---------|------|
| MATCH | N |
| DRIFT-HARMLESS | N |
| DRIFT-FUNCTIONAL | N |
| DRIFT-STRUCTURAL | N |
| MISSING-IN-CODE | N |
| MISSING-IN-SPEC | N |

**Drift 심각도**: {LOW / MEDIUM / HIGH / CRITICAL}

## 상세 항목

### [카테고리] 항목명
- Tobe: {스펙 기술}
- As-Is: {코드 실제}
- 영향: {예상 영향 또는 "없음"}
- 권장: {선택지 제시}

(모든 항목에 대해 반복)

## 우선 처리 대상
(STRUCTURAL, FUNCTIONAL 중 영향 범위 큰 것부터)

## 다음 단계 제안
(리포트 기반 구체적 액션 아이템)
```

## 워크플로우

1. Tobe 문서와 As-Is 문서를 모두 읽는다.
2. **기능 기준**으로 매칭한다 (이름이 아니라 동작으로 대응).
3. 추상도가 다르면 As-Is 함수들을 Tobe의 추상 기능에 **그룹핑**해서 비교. 그룹핑 불가한 함수는 `[MISSING-IN-SPEC]`.
4. 각 단위를 6개 카테고리로 분류한다.
5. 분류 결과를 Drift 리포트로 작성한다.
6. 우선 처리 대상을 영향 범위 기준으로 정렬한다.

## Common Mistakes

| 실수 | 올바른 방법 |
|------|------------|
| "코드가 틀렸다" (판단) | 차이를 기술하고 선택지를 제시 |
| 이름 기준 매칭 | 기능 기준 매칭 ("feasibility checker" = `validate_placement()`) |
| 판단 불가한 것을 억지 분류 | `[판단필요]` 태그로 사람에게 넘김 |
| 코드를 직접 읽음 | As-Is 문서만 참조 |
| 모든 drift를 "고칠 문제"로 취급 | 동작하는 코드의 drift는 스펙 업데이트가 맞을 수 있음 |
