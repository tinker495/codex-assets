from __future__ import annotations

import json
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


def _timestamp() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def default_status_path(output_path: Path | None, *, fallback_dir: Path | None, stem: str) -> Path | None:
    if output_path is not None:
        candidate = output_path if output_path.suffix == "" else output_path.with_name(f"{output_path.stem}.status.json")
        return candidate if candidate.suffix else candidate / f"{stem}.status.json"
    if fallback_dir is not None:
        return fallback_dir / f"{stem}.status.json"
    return None


def _line_excerpt(text: str, limit: int = 2000) -> str:
    normalized = text.strip()
    if len(normalized) <= limit:
        return normalized
    return f"{normalized[:limit]}...(truncated)"


@dataclass(frozen=True)
class ProcessOutput:
    returncode: int
    stdout: str
    stderr: str


class StatusTracker:
    def __init__(
        self,
        *,
        status_path: Path | None,
        script_name: str,
        heartbeat_interval_sec: float = 2.0,
        initial_state: dict[str, Any] | None = None,
    ) -> None:
        self.status_path = status_path
        self.script_name = script_name
        self.heartbeat_interval_sec = heartbeat_interval_sec
        self._lock = threading.Lock()
        self._heartbeat_stop = threading.Event()
        self._heartbeat_thread: threading.Thread | None = None
        self.state: dict[str, Any] = {
            "script": script_name,
            "started_at": _timestamp(),
            "updated_at": _timestamp(),
            "status": "running",
            "phase": "initializing",
            "message": "",
            "current_step": None,
            "steps": [],
            "artifacts": {},
        }
        if initial_state:
            self.state.update(initial_state)
        self._write()

    def log(self, message: str) -> None:
        print(f"[{self.script_name}] {message}", file=sys.stderr, flush=True)

    def _write(self) -> None:
        if self.status_path is None:
            return
        self.status_path.parent.mkdir(parents=True, exist_ok=True)
        self.state["updated_at"] = _timestamp()
        self.status_path.write_text(json.dumps(self.state, indent=2))

    def _update_current_step(self, **updates: Any) -> None:
        current_step = self.state.get("current_step")
        if not isinstance(current_step, dict):
            return
        current_step.update(updates)

    def _heartbeat_loop(self, step_name: str) -> None:
        while not self._heartbeat_stop.wait(self.heartbeat_interval_sec):
            with self._lock:
                current_step = self.state.get("current_step")
                if not isinstance(current_step, dict) or current_step.get("name") != step_name:
                    break
                heartbeat_count = int(current_step.get("heartbeat_count", 0)) + 1
                current_step["heartbeat_count"] = heartbeat_count
                current_step["heartbeat_at"] = _timestamp()
                self._write()

    def _stop_heartbeat(self) -> None:
        self._heartbeat_stop.set()
        if self._heartbeat_thread is not None:
            self._heartbeat_thread.join(timeout=1.0)
        self._heartbeat_stop = threading.Event()
        self._heartbeat_thread = None

    def set_phase(self, phase: str, *, message: str = "", **updates: Any) -> None:
        with self._lock:
            self.state["phase"] = phase
            if message:
                self.state["message"] = message
            self.state.update(updates)
            self._write()
        if message:
            self.log(message)

    def set_artifact(self, name: str, value: str | None) -> None:
        with self._lock:
            artifacts = self.state.setdefault("artifacts", {})
            if isinstance(artifacts, dict):
                artifacts[name] = value
            self._write()

    def start_step(self, step_name: str, *, command: list[str] | tuple[str, ...], message: str = "") -> None:
        self._stop_heartbeat()
        with self._lock:
            step_record = {
                "name": step_name,
                "status": "running",
                "command": list(command),
                "started_at": _timestamp(),
                "heartbeat_count": 0,
            }
            self.state["phase"] = "running"
            self.state["message"] = message or f"running {step_name}"
            self.state["current_step"] = step_record
            steps = self.state.setdefault("steps", [])
            if isinstance(steps, list):
                steps.append(step_record)
            self._write()
            self._heartbeat_thread = threading.Thread(
                target=self._heartbeat_loop,
                args=(step_name,),
                daemon=True,
            )
            self._heartbeat_thread.start()
        self.log(message or f"start step: {step_name}")

    def finish_step(
        self,
        step_name: str,
        *,
        returncode: int,
        stdout: str = "",
        stderr: str = "",
        message: str = "",
    ) -> None:
        status = "passed" if returncode == 0 else "failed"
        self._stop_heartbeat()
        with self._lock:
            steps = self.state.get("steps")
            if isinstance(steps, list):
                for step in reversed(steps):
                    if isinstance(step, dict) and step.get("name") == step_name and step.get("status") == "running":
                        step["status"] = status
                        step["returncode"] = returncode
                        step["finished_at"] = _timestamp()
                        step["stdout_excerpt"] = _line_excerpt(stdout)
                        step["stderr_excerpt"] = _line_excerpt(stderr)
                        break
            self._update_current_step(
                status=status,
                returncode=returncode,
                finished_at=_timestamp(),
                stdout_excerpt=_line_excerpt(stdout),
                stderr_excerpt=_line_excerpt(stderr),
            )
            self.state["current_step"] = None
            self.state["message"] = message or f"{step_name} {status}"
            self._write()
        self.log(message or f"finish step: {step_name} ({status})")

    def finish(self, final_status: str, *, message: str = "", **updates: Any) -> None:
        self._stop_heartbeat()
        with self._lock:
            self.state["status"] = final_status
            self.state["phase"] = "completed" if final_status == "passed" else final_status
            if message:
                self.state["message"] = message
            self.state.update(updates)
            self._write()
        if message:
            self.log(message)


def _pump_stream(
    *,
    stream: Any,
    buffer: list[str],
    step_name: str,
    stream_name: str,
    relay: bool,
    tracker: StatusTracker | None,
) -> None:
    try:
        for line in iter(stream.readline, ""):
            buffer.append(line)
            if relay:
                if tracker is not None:
                    tracker.log(f"{step_name} {stream_name}: {line.rstrip()}")
                else:
                    print(f"[{step_name}:{stream_name}] {line.rstrip()}", file=sys.stderr, flush=True)
    finally:
        stream.close()


def run_command_capture(
    *,
    command: list[str],
    cwd: Path,
    env: dict[str, str] | None = None,
    step_name: str,
    tracker: StatusTracker | None = None,
    relay_stdout_to_stderr: bool = False,
    relay_stderr: bool = True,
) -> ProcessOutput:
    if tracker is not None:
        tracker.start_step(step_name, command=command)

    process = subprocess.Popen(
        command,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        bufsize=1,
    )

    stdout_chunks: list[str] = []
    stderr_chunks: list[str] = []
    stdout_thread = threading.Thread(
        target=_pump_stream,
        kwargs={
            "stream": process.stdout,
            "buffer": stdout_chunks,
            "step_name": step_name,
            "stream_name": "stdout",
            "relay": relay_stdout_to_stderr,
            "tracker": tracker,
        },
        daemon=True,
    )
    stderr_thread = threading.Thread(
        target=_pump_stream,
        kwargs={
            "stream": process.stderr,
            "buffer": stderr_chunks,
            "step_name": step_name,
            "stream_name": "stderr",
            "relay": relay_stderr,
            "tracker": tracker,
        },
        daemon=True,
    )
    stdout_thread.start()
    stderr_thread.start()
    returncode = process.wait()
    stdout_thread.join()
    stderr_thread.join()

    stdout = "".join(stdout_chunks)
    stderr = "".join(stderr_chunks)
    if tracker is not None:
        tracker.finish_step(step_name, returncode=returncode, stdout=stdout, stderr=stderr)
    return ProcessOutput(returncode=returncode, stdout=stdout, stderr=stderr)
