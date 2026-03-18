from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any


class ChecklistStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    BLOCKED = "blocked"
    NOT_RUN = "not_run"
    NOT_REQUIRED = "not_required"


class CodeHealthStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"


_MANUAL_ITEM_STATUSES = {
    ChecklistStatus.PASSED.value,
    ChecklistStatus.FAILED.value,
    ChecklistStatus.BLOCKED.value,
    ChecklistStatus.NOT_RUN.value,
}


@dataclass(frozen=True)
class CodeHealthResult:
    status: CodeHealthStatus
    standard_test_status: ChecklistStatus
    failure: dict[str, Any] | None
    source_path: Path


def _parse_manual_status(value: str) -> ChecklistStatus:
    if value not in _MANUAL_ITEM_STATUSES:
        allowed = ", ".join(sorted(_MANUAL_ITEM_STATUSES))
        raise ValueError(f"Unsupported checklist status: {value!r}. Allowed: {allowed}")
    return ChecklistStatus(value)


def _load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text())
    except FileNotFoundError as exc:
        raise ValueError(f"Code-health JSON not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Code-health JSON is invalid: {path}") from exc


def load_code_health_result(path: Path) -> CodeHealthResult:
    payload = _load_json(path)
    raw_status = payload.get("status")
    raw_standard_test = payload.get("standard_test_status")
    failure = payload.get("failure")

    try:
        status = CodeHealthStatus(raw_status)
    except ValueError as exc:
        raise ValueError(f"Unsupported code-health status: {raw_status!r}") from exc

    try:
        standard_test_status = ChecklistStatus(raw_standard_test)
    except ValueError as exc:
        raise ValueError(f"Unsupported standard_test_status: {raw_standard_test!r}") from exc

    if status is CodeHealthStatus.FAILED and failure is not None and not isinstance(failure, dict):
        raise ValueError("`failure` must be an object or null in code-health JSON")

    return CodeHealthResult(
        status=status,
        standard_test_status=standard_test_status,
        failure=failure,
        source_path=path,
    )


def _make_item(
    *,
    name: str,
    status: ChecklistStatus,
    required: bool,
    source: str,
    detail: str,
) -> dict[str, Any]:
    return {
        "name": name,
        "status": status.value,
        "required": required,
        "source": source,
        "detail": detail,
    }


def _summarize_code_health_failure(failure: dict[str, Any] | None) -> str:
    if failure is None:
        return "code-health failure metadata unavailable"
    step = failure.get("step", "unknown")
    command = " ".join(failure.get("command", ()))
    returncode = failure.get("returncode", "unknown")
    return f"step={step}; returncode={returncode}; command={command}"


def evaluate_standard_test(result: CodeHealthResult) -> dict[str, Any]:
    if result.standard_test_status is ChecklistStatus.PASSED:
        detail = "coverage-backed pytest completed successfully via code-health"
    elif result.standard_test_status is ChecklistStatus.FAILED:
        detail = _summarize_code_health_failure(result.failure)
    elif result.standard_test_status is ChecklistStatus.NOT_RUN:
        detail = "coverage lane was skipped, so the standard test item still requires explicit verification"
    else:
        raise ValueError(f"Unexpected standard_test_status in code-health JSON: {result.standard_test_status.value}")

    status = result.standard_test_status
    if status is ChecklistStatus.NOT_RUN:
        status = ChecklistStatus.BLOCKED

    return _make_item(
        name="standard_test",
        status=status,
        required=True,
        source=f"code_health_json:{result.source_path}",
        detail=detail,
    )


def evaluate_standard_test_override(
    *,
    result: CodeHealthResult,
    override_status: ChecklistStatus,
    override_detail: str | None,
) -> dict[str, Any]:
    normalized_status = ChecklistStatus.BLOCKED if override_status is ChecklistStatus.NOT_RUN else override_status
    detail = override_detail or (
        "manual standard-test override applied "
        f"over code-health standard_test_status={result.standard_test_status.value}"
    )
    return _make_item(
        name="standard_test",
        status=normalized_status,
        required=True,
        source=f"manual_override:standard_test over code_health_json:{result.source_path}",
        detail=detail,
    )


def evaluate_lint_format(lint_status: ChecklistStatus, format_status: ChecklistStatus) -> dict[str, Any]:
    states = {lint_status, format_status}
    if ChecklistStatus.FAILED in states:
        overall = ChecklistStatus.FAILED
    elif ChecklistStatus.BLOCKED in states or ChecklistStatus.NOT_RUN in states:
        overall = ChecklistStatus.BLOCKED
    else:
        overall = ChecklistStatus.PASSED

    return _make_item(
        name="lint_format",
        status=overall,
        required=True,
        source="manual_flags:lint,format",
        detail=f"lint={lint_status.value}, format={format_status.value}",
    )


def evaluate_breaking_changes(status: ChecklistStatus) -> dict[str, Any]:
    normalized = ChecklistStatus.BLOCKED if status is ChecklistStatus.NOT_RUN else status
    return _make_item(
        name="breaking_changes",
        status=normalized,
        required=True,
        source="manual_flag:breaking_changes",
        detail=f"breaking_changes={status.value}",
    )


def evaluate_full_dataset(*, required: bool, status: ChecklistStatus) -> dict[str, Any]:
    if not required:
        return _make_item(
            name="full_dataset",
            status=ChecklistStatus.NOT_REQUIRED,
            required=False,
            source="default_policy",
            detail="full-dataset verification is optional unless explicitly required",
        )

    normalized = ChecklistStatus.BLOCKED if status is ChecklistStatus.NOT_RUN else status
    return _make_item(
        name="full_dataset",
        status=normalized,
        required=True,
        source="manual_flag:full_dataset",
        detail=f"full_dataset={status.value}",
    )


def evaluate_overall(items: list[dict[str, Any]]) -> tuple[str, list[str], list[str]]:
    failed_items = [item["name"] for item in items if item["required"] and item["status"] == ChecklistStatus.FAILED.value]
    blocked_items = [
        item["name"]
        for item in items
        if item["required"] and item["status"] in {ChecklistStatus.BLOCKED.value, ChecklistStatus.NOT_RUN.value}
    ]
    if failed_items:
        return ChecklistStatus.FAILED.value, failed_items, blocked_items
    if blocked_items:
        return ChecklistStatus.BLOCKED.value, failed_items, blocked_items
    return ChecklistStatus.PASSED.value, failed_items, blocked_items


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate PR checklist items from code-health metadata")
    parser.add_argument("--code-health-json", type=Path, required=True)
    parser.add_argument("--standard-test-override", default=None, choices=sorted(_MANUAL_ITEM_STATUSES))
    parser.add_argument("--standard-test-override-detail", default="")
    parser.add_argument("--lint", default=ChecklistStatus.NOT_RUN.value, choices=sorted(_MANUAL_ITEM_STATUSES))
    parser.add_argument("--format", default=ChecklistStatus.NOT_RUN.value, choices=sorted(_MANUAL_ITEM_STATUSES))
    parser.add_argument("--breaking-changes", default=ChecklistStatus.NOT_RUN.value, choices=sorted(_MANUAL_ITEM_STATUSES))
    parser.add_argument("--full-dataset", default=ChecklistStatus.NOT_RUN.value, choices=sorted(_MANUAL_ITEM_STATUSES))
    parser.add_argument("--require-full-dataset", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()

    code_health = load_code_health_result(args.code_health_json)
    standard_test_override = (
        _parse_manual_status(args.standard_test_override) if args.standard_test_override is not None else None
    )
    lint_status = _parse_manual_status(args.lint)
    format_status = _parse_manual_status(args.format)
    breaking_changes_status = _parse_manual_status(args.breaking_changes)
    full_dataset_status = _parse_manual_status(args.full_dataset)

    items = [
        (
            evaluate_standard_test_override(
                result=code_health,
                override_status=standard_test_override,
                override_detail=args.standard_test_override_detail.strip() or None,
            )
            if standard_test_override is not None
            else evaluate_standard_test(code_health)
        ),
        evaluate_lint_format(lint_status, format_status),
        evaluate_breaking_changes(breaking_changes_status),
        evaluate_full_dataset(required=args.require_full_dataset, status=full_dataset_status),
    ]
    overall_status, failed_items, blocked_items = evaluate_overall(items)

    payload = {
        "overall_status": overall_status,
        "failed_items": failed_items,
        "blocked_items": blocked_items,
        "items": {item["name"]: item for item in items},
        "inputs": {
            "code_health_json": str(args.code_health_json),
            "standard_test_override": standard_test_override.value if standard_test_override is not None else None,
            "standard_test_override_detail": args.standard_test_override_detail,
            "require_full_dataset": args.require_full_dataset,
            "lint": lint_status.value,
            "format": format_status.value,
            "breaking_changes": breaking_changes_status.value,
            "full_dataset": full_dataset_status.value,
        },
    }
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
