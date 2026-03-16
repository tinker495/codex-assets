#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text())
    except FileNotFoundError as exc:
        raise ValueError(f"Input JSON not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Input JSON is invalid: {path}") from exc


def as_dict(value: Any, *, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be an object")
    return value


def as_list(value: Any, *, name: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{name} must be a list")
    return value


def title_from_payload(payload: dict[str, Any]) -> str:
    branch_context = as_dict(payload.get("branch_context"), name="branch_context")
    branch = branch_context.get("branch", "unknown-branch")
    return f"TODO: 한국어 PR 제목 작성 ({branch})"


def checkbox(status: str) -> str:
    return "[x]" if status == "passed" else "[ ]"


def render_category_metrics(category_metrics: dict[str, Any]) -> list[str]:
    order = ["Feature", "Refactor", "Test", "Document", "Tooling", "Bugfix"]
    lines: list[str] = []
    for category in order:
        metrics = as_dict(category_metrics.get(category, {}), name=f"category_metrics.{category}")
        lines.append(f"- {category}: {metrics.get('net', 0):+}")
    return lines


def render_category_table(category_metrics: dict[str, Any], runtime_bucket: str) -> list[str]:
    order = ["Feature", "Refactor", "Test", "Document", "Tooling", "Bugfix"]
    lines = [
        "| Category | Before | After | Evidence |",
        "|----------|--------|-------|----------|",
    ]
    for category in order:
        metrics = as_dict(category_metrics.get(category, {}), name=f"category_metrics.{category}")
        files = ", ".join(as_list(metrics.get("files", []), name=f"category_metrics.{category}.files")[:3]) or "-"
        added = int(metrics.get("added", 0))
        deleted = int(metrics.get("deleted", 0))
        net = int(metrics.get("net", 0))
        if category == runtime_bucket:
            before = "기준 브랜치 대비 현재 변경 없음"
            after = f"런타임 경로 변경 {len(as_list(metrics.get('files', []), name=f'category_metrics.{category}.files'))}건 (휴리스틱 {category})"
        elif category == "Test":
            before = "관련 회귀 테스트 초안 미반영"
            after = f"테스트 경로 변경 {len(as_list(metrics.get('files', []), name=f'category_metrics.{category}.files'))}건"
        elif category == "Document":
            before = "문서 변경 없음"
            after = "문서 경로 변경 반영" if metrics.get("files") else "문서 변경 없음"
        elif category == "Tooling":
            before = "도구/스크립트 변경 없음"
            after = "도구/스크립트 변경 반영" if metrics.get("files") else "도구/스크립트 변경 없음"
        else:
            before = "자동 분류상 변경 없음"
            after = "자동 분류상 변경 없음"
        lines.append(f"| {category} | {before} | {after} | +{added}/-{deleted} (net {net:+}) · {files} |")
    return lines


def render_code_health_summary(code_health: dict[str, Any]) -> list[str]:
    duplication = as_dict(code_health.get("duplication", {}), name="code_health.duplication")
    lines = [
        f"- Status: {code_health.get('status', 'unknown')}",
        f"- Standard test status: {code_health.get('standard_test_status', 'unknown')}",
        (
            f"- Duplication: {duplication.get('pct', 'unknown')}% "
            f"({duplication.get('clones', 'unknown')} clones, {duplication.get('dup_lines', 'unknown')} duplicated lines)"
        ),
        f"- Xenon: {code_health.get('xenon_status', 'unknown')}",
    ]
    failure = code_health.get("failure")
    if isinstance(failure, dict):
        command = " ".join(as_list(failure.get("command", []), name="code_health.failure.command"))
        lines.append(
            f"- Failure evidence: step={failure.get('step', 'unknown')} / returncode={failure.get('returncode', 'unknown')} / command={command}"
        )
    return lines


def render_checklist(checklist_items: dict[str, Any]) -> list[str]:
    order = ["standard_test", "lint_format", "breaking_changes", "full_dataset"]
    labels = {
        "standard_test": "모든 테스트 통과",
        "lint_format": "Lint/Format 검사 통과",
        "breaking_changes": "Breaking changes 문서화 완료",
        "full_dataset": "Full dataset 테스트 통과",
    }
    lines: list[str] = []
    for key in order:
        item = as_dict(checklist_items.get(key, {}), name=f"checklist.items.{key}")
        if item.get("status") == "not_required":
            lines.append(f"- {labels[key]}: not required ({item.get('detail', '-')})")
            continue
        lines.append(f"- {checkbox(str(item.get('status')))} {labels[key]} — {item.get('status')} ({item.get('detail', '-')})")
    return lines


def build_markdown(payload: dict[str, Any], *, title: str) -> str:
    branch_context = as_dict(payload.get("branch_context"), name="branch_context")
    code_health = as_dict(payload.get("code_health"), name="code_health")
    checklist = as_dict(payload.get("checklist"), name="checklist")
    checklist_items = as_dict(checklist.get("items"), name="checklist.items")
    pr_body_inputs = as_dict(payload.get("pr_body_inputs"), name="pr_body_inputs")
    narrative_hints = as_dict(pr_body_inputs.get("narrative_hints", {}), name="pr_body_inputs.narrative_hints")
    category_metrics = as_dict(pr_body_inputs.get("category_metrics"), name="pr_body_inputs.category_metrics")
    runtime_bucket = str(pr_body_inputs.get("runtime_bucket", "Feature"))
    breaking_changes = as_dict(payload.get("breaking_changes"), name="breaking_changes")
    commands = as_dict(payload.get("commands"), name="commands")

    commit_log = as_list(branch_context.get("commit_log", []), name="branch_context.commit_log")
    file_list = as_list(branch_context.get("file_list", []), name="branch_context.file_list")

    lines: list[str] = []
    lines.append(f"## PR Description: {title}")
    lines.append("")
    lines.append("### Overview")
    lines.append(
        f"이 초안은 `{branch_context.get('branch', 'unknown')}` 브랜치가 `{branch_context.get('base', 'unknown')}` 대비 "
        f"{branch_context.get('commit_count', 0)}개 커밋, {branch_context.get('files_changed', 0)}개 파일을 변경한 결과를 바탕으로 자동 생성했습니다."
    )
    lines.append(
        f"자동 체크리스트 상태는 `{checklist.get('overall_status', 'unknown')}`이며, "
        f"표준 테스트 판정은 `code-health.standard_test_status={code_health.get('standard_test_status', 'unknown')}`를 우선 사용했습니다."
    )
    problem_statement = narrative_hints.get("problem_statement")
    solution_statement = narrative_hints.get("solution_statement")
    if isinstance(problem_statement, str) and problem_statement.strip():
        lines.append(f"- 배경(자동 추론): {problem_statement.strip()}")
    if isinstance(solution_statement, str) and solution_statement.strip():
        lines.append(f"- 변경 방향(자동 추론): {solution_statement.strip()}")
    if narrative_hints.get("needs_manual_completion"):
        lines.append(str(narrative_hints.get("manual_prompt") or "TODO: 브랜치 배경 문제를 한두 문장으로 보강해 주세요."))
    lines.append("부정확할 수 있는 카테고리/리뷰 포인트는 TODO 표식을 남겼으니 PR 생성 전 최종 보정이 필요합니다.")
    lines.append("")
    lines.append("### 주요 변경사항 (Key Changes)")
    lines.append("")
    lines.append("#### 카테고리별 Net Change (자동 초안)")
    lines.extend(render_category_metrics(category_metrics))
    lines.append("")
    lines.append("#### 카테고리별 Before → After (자동 초안)")
    lines.extend(render_category_table(category_metrics, runtime_bucket))
    lines.append("")
    lines.append("#### 자동 수집 근거")
    lines.append(f"- Diff stat: {branch_context.get('diff_stat', '-')}")
    lines.append(f"- Runtime bucket heuristic: {runtime_bucket}")
    lines.append(f"- Commit log: {', '.join(commit_log) if commit_log else '-'}")
    lines.append(f"- Changed files: {', '.join(file_list[:8]) if file_list else '-'}")
    lines.append("")
    lines.append("### Breaking Changes")
    if breaking_changes.get("suspected_breaking_changes"):
        deleted_files = as_list(breaking_changes.get("deleted_files", []), name="breaking_changes.deleted_files")
        renamed_files = as_list(breaking_changes.get("renamed_files", []), name="breaking_changes.renamed_files")
        lines.append(f"- 자동 힌트: {breaking_changes.get('summary', '-')}")
        if deleted_files:
            lines.append(f"- 삭제 파일: {', '.join(deleted_files)}")
        if renamed_files:
            rename_summary = ", ".join(
                f"{as_dict(item, name='breaking_changes.renamed_files[]').get('from')} → {as_dict(item, name='breaking_changes.renamed_files[]').get('to')}"
                for item in renamed_files
            )
            lines.append(f"- rename 힌트: {rename_summary}")
    else:
        lines.append("- 자동 힌트상 삭제/rename 기반 breaking change는 감지되지 않았습니다.")
    lines.append("")
    lines.append("### 테스트 (자동 수집)")
    standard_test = as_dict(checklist_items.get("standard_test", {}), name="checklist.items.standard_test")
    lines.append(
        f"- 표준 테스트: {standard_test.get('status', 'unknown')} / {standard_test.get('detail', '-')}"
    )
    full_dataset = as_dict(checklist_items.get("full_dataset", {}), name="checklist.items.full_dataset")
    lines.append(
        f"- Full dataset: {full_dataset.get('status', 'unknown')} / {full_dataset.get('detail', '-')}"
    )
    lines.append("")
    lines.append("### 코드 헬스 요약 (자동 수집)")
    lines.extend(render_code_health_summary(code_health))
    lines.append("")
    lines.append("### 실행 명령 요약")
    for name in ["code_health", "lint", "format", "full_dataset"]:
        command = as_dict(commands.get(name, {}), name=f"commands.{name}")
        lines.append(f"- {name}: status={command.get('status', 'unknown')} / returncode={command.get('returncode', 'unknown')}")
    lines.append("")
    lines.append("### 리뷰 포인트 (초안)")
    if file_list:
        for index, path in enumerate(file_list[:3], start=1):
            lines.append(f"{index}. **`{path}`** — TODO: 변경 목적과 리스크를 수동 보강")
    else:
        lines.append("1. **TODO** — 변경 파일이 없거나 자동 수집에 실패했습니다.")
    lines.append("")
    lines.append("### Checklist")
    lines.extend(render_checklist(checklist_items))
    lines.append("")
    lines.append("### TODO")
    lines.append("- 한국어 PR 제목을 최종 확정")
    lines.append("- Feature/Refactor/Bugfix 카테고리 휴리스틱 분류를 실제 변경 의도에 맞게 보정")
    lines.append("- 리뷰 포인트를 파일별 실제 관심사로 교체")
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a PR markdown draft from run_pr_workflow JSON")
    parser.add_argument("--input-json", type=Path, required=True)
    parser.add_argument("--output-markdown", type=Path, required=True)
    parser.add_argument("--title", default="")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    payload = load_json(args.input_json)
    title = args.title.strip() or title_from_payload(payload)
    markdown = build_markdown(payload, title=title)
    args.output_markdown.parent.mkdir(parents=True, exist_ok=True)
    args.output_markdown.write_text(markdown)
    print(str(args.output_markdown))


if __name__ == "__main__":
    main()
