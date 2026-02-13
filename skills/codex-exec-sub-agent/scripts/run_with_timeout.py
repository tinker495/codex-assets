#!/usr/bin/env python3
import os
import subprocess
import sys
import time


def main() -> int:
    timeout_sec = int(sys.argv[1])
    prompt_path = sys.argv[2]
    jsonl_path = sys.argv[3]
    model = sys.argv[4]
    profile = sys.argv[5]
    worker_cwd = sys.argv[6]
    skip_git_repo_check = sys.argv[7] == "1"
    codex_home_override = sys.argv[8]
    use_json = sys.argv[9] == "1"
    append_mode = sys.argv[10] == "1"
    start = time.monotonic()

    cmd = ["codex", "exec"]
    if use_json:
        cmd.append("--json")
    cmd.extend(["--model", model])
    if profile:
        cmd.extend(["--profile", profile])
    if worker_cwd:
        cmd.extend(["--cd", worker_cwd])
    if skip_git_repo_check:
        cmd.append("--skip-git-repo-check")
    cmd.append("-")

    env = os.environ.copy()
    if codex_home_override:
        env["CODEX_HOME"] = codex_home_override

    log_mode = "ab" if append_mode else "wb"
    with open(prompt_path, "rb") as prompt_stream, open(jsonl_path, log_mode) as jsonl_stream:
        proc = subprocess.Popen(
            cmd,
            stdin=prompt_stream,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=env,
        )

        while True:
            line = proc.stdout.readline() if proc.stdout is not None else b""
            if line:
                sys.stdout.buffer.write(line)
                sys.stdout.buffer.flush()
                jsonl_stream.write(line)
                jsonl_stream.flush()

            if proc.poll() is not None:
                if proc.stdout is not None:
                    rest = proc.stdout.read()
                    if rest:
                        sys.stdout.buffer.write(rest)
                        sys.stdout.buffer.flush()
                        jsonl_stream.write(rest)
                        jsonl_stream.flush()
                return proc.returncode

            if time.monotonic() - start > timeout_sec:
                proc.kill()
                timeout_line = (
                    '{"type":"error","error":"sub-agent timeout","timeout_sec":'
                    + str(timeout_sec)
                    + "}\n"
                ).encode("utf-8")
                sys.stdout.buffer.write(timeout_line)
                sys.stdout.buffer.flush()
                jsonl_stream.write(timeout_line)
                jsonl_stream.flush()
                return 124


if __name__ == "__main__":
    raise SystemExit(main())
