#!/usr/bin/env python3
"""Parallel RLM subagent dispatcher using codex-exec-sub-agent runner."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_PARALLEL_CAP = 8
DEFAULT_TIMEOUT_SEC = 600
DEFAULT_RETRIES = 2
LOC_PATTERN = re.compile(r"^.+:[0-9]+-[0-9]+$")
JSONL_PATH_PATTERN = re.compile(r"(/[^\s]+\.jsonl)")
MAX_SUMMARY_LEN = 1200
MAX_LOC_LEN = 512
MAX_QUOTE_LEN = 320
MAX_NOTE_LEN = 400


@dataclass(frozen=True)
class Job:
    job_id: str
    chunk_id: str
    chunk_path: Path
    question: str
    output_path: str
    schema_path: Path
    sandbox: str
    timeout_sec: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run RLM subagent jobs in parallel")
    parser.add_argument("--jobs", required=True, help="Path to jobs.jsonl")
    parser.add_argument("--run-dir", required=True, help="Session run directory")
    parser.add_argument(
        "--parallel",
        type=int,
        default=min(DEFAULT_PARALLEL_CAP, os.cpu_count() or 1),
        help="Parallel worker count",
    )
    parser.add_argument(
        "--timeout-sec",
        type=int,
        default=DEFAULT_TIMEOUT_SEC,
        help="Default timeout per job in seconds",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=DEFAULT_RETRIES,
        help="Retries per job on failure",
    )
    parser.add_argument(
        "--runner-script",
        default=str(Path.home() / ".codex/skills/codex-exec-sub-agent/scripts/run.sh"),
        help="Path to codex-exec-sub-agent run.sh",
    )
    return parser.parse_args()


def read_jobs(jobs_path: Path, default_timeout_sec: int) -> list[Job]:
    if not jobs_path.exists():
        raise ValueError(f"jobs file not found: {jobs_path}")

    required_fields = {
        "job_id",
        "chunk_id",
        "chunk_path",
        "question",
        "output_path",
        "schema_path",
        "sandbox",
    }
    seen: set[str] = set()
    jobs: list[Job] = []

    with jobs_path.open("r", encoding="utf-8") as handle:
        for line_no, raw in enumerate(handle, 1):
            line = raw.strip()
            if not line:
                continue

            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSON at line {line_no}: {exc}") from exc

            if not isinstance(obj, dict):
                raise ValueError(f"line {line_no}: record must be an object")

            missing = sorted(required_fields - set(obj.keys()))
            if missing:
                raise ValueError(f"line {line_no}: missing required fields: {', '.join(missing)}")

            job_id = must_string(obj["job_id"], f"line {line_no} job_id")
            if job_id in seen:
                raise ValueError(f"line {line_no}: duplicate job_id '{job_id}'")
            seen.add(job_id)

            chunk_path = Path(must_string(obj["chunk_path"], f"line {line_no} chunk_path")).expanduser()
            if not chunk_path.exists():
                raise ValueError(f"line {line_no}: chunk_path does not exist: {chunk_path}")
            if not chunk_path.is_file():
                raise ValueError(f"line {line_no}: chunk_path is not a file: {chunk_path}")

            schema_path = Path(must_string(obj["schema_path"], f"line {line_no} schema_path")).expanduser()
            if not schema_path.exists():
                raise ValueError(f"line {line_no}: schema_path does not exist: {schema_path}")
            if not schema_path.is_file():
                raise ValueError(f"line {line_no}: schema_path is not a file: {schema_path}")

            sandbox = must_string(obj["sandbox"], f"line {line_no} sandbox")
            if sandbox != "read-only":
                raise ValueError(
                    f"line {line_no}: sandbox must be 'read-only' for this runner (got '{sandbox}')"
                )

            timeout = obj.get("timeout_sec", default_timeout_sec)
            if not isinstance(timeout, int) or timeout <= 0:
                raise ValueError(f"line {line_no}: timeout_sec must be a positive integer")

            job = Job(
                job_id=job_id,
                chunk_id=must_string(obj["chunk_id"], f"line {line_no} chunk_id"),
                chunk_path=chunk_path.resolve(),
                question=must_string(obj["question"], f"line {line_no} question"),
                output_path=must_string(obj["output_path"], f"line {line_no} output_path"),
                schema_path=schema_path.resolve(),
                sandbox=sandbox,
                timeout_sec=timeout,
            )
            jobs.append(job)

    if not jobs:
        raise ValueError("jobs file is empty")

    return jobs


def must_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def to_output_path(run_dir: Path, output_path: str) -> Path:
    path = Path(output_path).expanduser()
    if not path.is_absolute():
        path = run_dir / path
    return path.resolve()


def build_prompt(job: Job, output_path: Path) -> str:
    return (
        "Use $rlm-subagent.\n"
        "You are processing one chunk-level job in isolation.\n"
        f"Question: {job.question}\n"
        f"chunk_id: {job.chunk_id}\n"
        f"Chunk file path (read this file only): {job.chunk_path}\n"
        f"Output schema path: {job.schema_path}\n"
        "Rules:\n"
        "- Do not inspect unrelated files.\n"
        "- Do not use markdown fences.\n"
        "- Return one JSON object as your final assistant message.\n"
        "- JSON must strictly satisfy the schema.\n"
        "- Always include both `gaps` and `errors` fields as arrays (use [] when empty).\n"
        "- Keep summary concise and evidence grounded.\n"
        "After generating the JSON, do not add extra text.\n"
        f"Intended output file (written by batch runner): {output_path}\n"
    )


def run_once(runner_script: Path, prompt_path: Path, timeout_sec: int) -> tuple[int, str, str, Path | None]:
    cmd = [str(runner_script), "--timeout-sec", str(timeout_sec), "--prompt-file", str(prompt_path)]
    proc = subprocess.run(cmd, capture_output=True, text=True)

    stdout = proc.stdout or ""
    stderr = proc.stderr or ""
    jsonl_path = extract_jsonl_path(stdout)

    return proc.returncode, stdout, stderr, jsonl_path


def extract_jsonl_path(stdout: str) -> Path | None:
    lines = [line.strip() for line in stdout.splitlines() if line.strip()]
    for line in reversed(lines):
        if line.endswith(".jsonl"):
            path = Path(line)
            if path.exists():
                return path

    for match in JSONL_PATH_PATTERN.findall(stdout):
        path = Path(match)
        if path.exists():
            return path

    return None


def extract_agent_message(log_path: Path) -> str | None:
    message: str | None = None

    with log_path.open("r", encoding="utf-8") as handle:
        for raw in handle:
            line = raw.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            if not isinstance(obj, dict):
                continue

            item = obj.get("item")
            if isinstance(item, dict) and item.get("type") == "agent_message":
                text = item.get("text")
                if isinstance(text, str) and text.strip():
                    message = text.strip()

    return message


def parse_json_payload(raw_text: str) -> tuple[dict[str, Any] | None, str | None]:
    text = raw_text.strip()
    if text.startswith("```") and text.endswith("```"):
        text = "\n".join(text.splitlines()[1:-1]).strip()

    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        return None, f"agent message is not valid JSON: {exc}"

    if not isinstance(payload, dict):
        return None, "agent message must decode to a JSON object"

    return payload, None


def clamp_text(value: Any, max_len: int, *, keep_right: bool = False) -> Any:
    if not isinstance(value, str):
        return value
    if len(value) <= max_len:
        return value
    if keep_right:
        return value[-max_len:]
    return value[:max_len]


def normalize_subagent_payload(payload: dict[str, Any]) -> dict[str, Any]:
    if "gaps" not in payload:
        payload["gaps"] = []
    if "errors" not in payload:
        payload["errors"] = []

    payload["summary"] = clamp_text(payload.get("summary"), MAX_SUMMARY_LEN)

    evidence = payload.get("evidence")
    if isinstance(evidence, list):
        for item in evidence:
            if not isinstance(item, dict):
                continue
            if "note" not in item and isinstance(item.get("quote"), str):
                item["note"] = "Direct quote supporting the chunk-level claim."
            item["loc"] = clamp_text(item.get("loc"), MAX_LOC_LEN, keep_right=True)
            item["quote"] = clamp_text(item.get("quote"), MAX_QUOTE_LEN)
            item["note"] = clamp_text(item.get("note"), MAX_NOTE_LEN)

    return payload


def validate_subagent_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    required = {
        "chunk_id",
        "relevant",
        "summary",
        "confidence",
        "evidence",
        "gaps",
        "errors",
    }
    allowed = set(required)

    missing = sorted(required - set(payload.keys()))
    if missing:
        errors.append(f"missing fields: {', '.join(missing)}")

    unknown = sorted(set(payload.keys()) - allowed)
    if unknown:
        errors.append(f"unknown fields: {', '.join(unknown)}")

    chunk_id = payload.get("chunk_id")
    if not isinstance(chunk_id, str) or not chunk_id:
        errors.append("chunk_id must be a non-empty string")

    relevant = payload.get("relevant")
    if not isinstance(relevant, bool):
        errors.append("relevant must be a boolean")

    summary = payload.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        errors.append("summary must be a non-empty string")
    elif len(summary) > MAX_SUMMARY_LEN:
        errors.append(f"summary exceeds max length {MAX_SUMMARY_LEN}")

    confidence = payload.get("confidence")
    if not isinstance(confidence, (int, float)):
        errors.append("confidence must be numeric")
    elif not (0 <= float(confidence) <= 1):
        errors.append("confidence must be between 0 and 1")

    evidence = payload.get("evidence")
    if not isinstance(evidence, list):
        errors.append("evidence must be an array")
    else:
        for idx, item in enumerate(evidence):
            prefix = f"evidence[{idx}]"
            if not isinstance(item, dict):
                errors.append(f"{prefix} must be an object")
                continue
            allowed_e = {"loc", "quote", "note"}
            missing_e = sorted(allowed_e - set(item.keys()))
            if missing_e:
                errors.append(f"{prefix} missing fields: {', '.join(missing_e)}")
            unknown_e = sorted(set(item.keys()) - allowed_e)
            if unknown_e:
                errors.append(f"{prefix} unknown fields: {', '.join(unknown_e)}")

            loc = item.get("loc")
            if not isinstance(loc, str) or not LOC_PATTERN.match(loc):
                errors.append(f"{prefix}.loc must match path:start-end")
            elif len(loc) > MAX_LOC_LEN:
                errors.append(f"{prefix}.loc exceeds max length {MAX_LOC_LEN}")

            quote = item.get("quote")
            if not isinstance(quote, str) or not quote.strip():
                errors.append(f"{prefix}.quote must be a non-empty string")
            elif len(quote) > MAX_QUOTE_LEN:
                errors.append(f"{prefix}.quote exceeds max length {MAX_QUOTE_LEN}")

            note = item.get("note")
            if not isinstance(note, str) or not note.strip():
                errors.append(f"{prefix}.note must be a non-empty string")
            elif len(note) > MAX_NOTE_LEN:
                errors.append(f"{prefix}.note exceeds max length {MAX_NOTE_LEN}")

    for key in ("gaps", "errors"):
        value = payload.get(key)
        if value is None:
            continue
        if not isinstance(value, list) or not all(isinstance(v, str) and v.strip() for v in value):
            errors.append(f"{key} must be an array of non-empty strings")

    return errors


def run_job(
    job: Job,
    run_dir: Path,
    runner_script: Path,
    retries: int,
    prompts_dir: Path,
    logs_dir: Path,
) -> dict[str, Any]:
    output_path = to_output_path(run_dir, job.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    attempt_logs: list[str] = []
    attempt_errors: list[str] = []

    for attempt in range(1, retries + 2):
        prompt = build_prompt(job, output_path)
        prompt_path = prompts_dir / f"{job.job_id}.attempt{attempt}.txt"
        prompt_path.write_text(prompt, encoding="utf-8")

        code, stdout, stderr, upstream_jsonl = run_once(runner_script, prompt_path, job.timeout_sec)

        local_log = logs_dir / f"{job.job_id}.attempt{attempt}.jsonl"
        if upstream_jsonl is not None and upstream_jsonl.exists():
            shutil.copyfile(upstream_jsonl, local_log)
        else:
            local_log.write_text(stdout, encoding="utf-8")
        attempt_logs.append(str(local_log))

        if code != 0:
            reason = f"attempt {attempt}: runner exit code {code}"
            if stderr.strip():
                reason += f"; stderr={stderr.strip()}"
            attempt_errors.append(reason)
            continue

        agent_message = extract_agent_message(local_log)
        if not agent_message:
            attempt_errors.append(f"attempt {attempt}: no agent_message found in JSONL")
            continue

        payload, parse_error = parse_json_payload(agent_message)
        if parse_error:
            attempt_errors.append(f"attempt {attempt}: {parse_error}")
            continue

        payload = normalize_subagent_payload(payload)
        schema_errors = validate_subagent_payload(payload)
        if schema_errors:
            attempt_errors.append(
                f"attempt {attempt}: schema validation failed: {'; '.join(schema_errors)}"
            )
            continue

        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return {
            "job_id": job.job_id,
            "status": "success",
            "attempts": attempt,
            "output_path": str(output_path),
            "log_paths": attempt_logs,
            "errors": [],
        }

    return {
        "job_id": job.job_id,
        "status": "failed",
        "attempts": retries + 1,
        "output_path": str(output_path),
        "log_paths": attempt_logs,
        "errors": attempt_errors,
    }


def write_summary(run_dir: Path, started_at: float, results: list[dict[str, Any]]) -> Path:
    duration_sec = round(time.time() - started_at, 3)
    succeeded = sum(1 for item in results if item["status"] == "success")
    failed = len(results) - succeeded

    summary = {
        "run_dir": str(run_dir),
        "jobs_total": len(results),
        "jobs_succeeded": succeeded,
        "jobs_failed": failed,
        "duration_sec": duration_sec,
        "results": results,
    }

    summary_path = run_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary_path


def main() -> int:
    args = parse_args()

    jobs_path = Path(args.jobs).expanduser().resolve()
    run_dir = Path(args.run_dir).expanduser().resolve()
    runner_script = Path(args.runner_script).expanduser().resolve()

    if args.parallel <= 0:
        print("--parallel must be a positive integer", file=sys.stderr)
        return 1
    if args.retries < 0:
        print("--retries must be >= 0", file=sys.stderr)
        return 1
    if args.timeout_sec <= 0:
        print("--timeout-sec must be > 0", file=sys.stderr)
        return 1

    if not runner_script.exists() or not runner_script.is_file():
        print(f"runner script not found: {runner_script}", file=sys.stderr)
        return 1

    run_dir.mkdir(parents=True, exist_ok=True)
    subresults_dir = run_dir / "subresults"
    logs_dir = run_dir / "logs"
    prompts_dir = run_dir / "prompts"
    subresults_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    prompts_dir.mkdir(parents=True, exist_ok=True)

    try:
        jobs = read_jobs(jobs_path, args.timeout_sec)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    started_at = time.time()

    results: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.parallel) as executor:
        future_map = {
            executor.submit(
                run_job,
                job,
                run_dir,
                runner_script,
                args.retries,
                prompts_dir,
                logs_dir,
            ): job.job_id
            for job in jobs
        }
        for future in concurrent.futures.as_completed(future_map):
            job_id = future_map[future]
            try:
                result = future.result()
            except Exception as exc:  # noqa: BLE001
                result = {
                    "job_id": job_id,
                    "status": "failed",
                    "attempts": args.retries + 1,
                    "output_path": "",
                    "log_paths": [],
                    "errors": [f"internal runner error: {exc}"],
                }
            results.append(result)

    results.sort(key=lambda item: item["job_id"])
    summary_path = write_summary(run_dir, started_at, results)

    succeeded = sum(1 for item in results if item["status"] == "success")
    failed = len(results) - succeeded

    print(f"summary: {summary_path}")
    print(f"jobs_total={len(results)} jobs_succeeded={succeeded} jobs_failed={failed}")

    if failed == 0:
        return 0
    if succeeded > 0:
        return 2
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
