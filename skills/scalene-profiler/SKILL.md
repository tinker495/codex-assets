---
name: scalene-profiler
description: "Use when a user wants detailed Python runtime profiling with Scalene: line-level CPU/native/system hotspots, memory growth or leaks, copy-volume hotspots, or optional GPU profiling. Best for repeatable profiling of Python scripts in a uv-managed repo with reusable JSON, CLI, and standalone HTML artifacts."
---

# Scalene Profiler

## Overview

Use this skill to collect real runtime evidence before suggesting performance fixes. It wraps Scalene into a repeatable workflow that leaves behind reusable JSON, terminal, and HTML artifacts instead of one-off console output.

Prefer this skill when the task is about runtime hotspots, memory growth, leak suspicion, copy-heavy data movement, or CPU vs native vs system time breakdowns.

## When to use it

- "이 코드 왜 느리지?" / "어디가 병목인지 보여줘"
- line-level CPU hotspot investigation
- memory allocation or leak suspicion
- copy-volume investigation across Python/library boundaries
- optional GPU profiling on supported systems
- uv-managed repo where profiling should run inside the project dependency environment

Do not use this skill for pure static analysis or speculative micro-optimization without a reproducible runtime path.

## Workflow

1. Pick a reproducible Python entry script.
   - Prefer a small driver over a whole interactive session.
   - In this repo, likely candidates are `src/stowage/__main__.py` or `src/tui/app.py`.
2. Choose the runner.
   - Use `--runner uv` (or leave `--runner auto`) when the target depends on the repo's `uv` environment.
   - Use `--runner scalene` for simple standalone scripts when the global `scalene` binary is enough.
3. Run the bundled helper:
   - Fast CPU pass:
     - `python scripts/run_scalene_profile.py --cpu-only --view cli <target.py> -- <program args>`
   - Full artifact pass:
     - `python scripts/run_scalene_profile.py --view standalone --profile-only src/stowage,src/tui <target.py> -- <program args>`
4. Read the artifacts and identify the hottest lines/functions.
5. Tighten the scope and rerun:
   - `--profile-only`
   - `--profile-exclude`
   - `--stacks`
   - `--profile-interval`
   - `@profile` on a suspect function
6. Report exact artifact paths plus the hottest lines/functions and what each metric implies.

## Bundled helper

Use `scripts/run_scalene_profile.py` as the default execution surface.

What it does:

- chooses a Scalene runner (`auto`, `uv`, `scalene`, or `module`)
- writes artifacts to a writable output directory
- stores raw JSON plus an optional CLI/HTML/standalone rendering
- writes a manifest JSON with the exact command and artifact paths
- exposes an `--extra-scalene-arg` escape hatch for advanced Scalene flags

Default output directory preference:

1. `$CODEX_HOME/shared/scalene-profiles`
2. `<cwd>/.codex_tmp/scalene-profiles`
3. `/tmp/scalene-profiles`

## Common recipes

### 1. Cheap first pass

```bash
python /Users/mrx-ksjung/.codex/skills/scalene-profiler/scripts/run_scalene_profile.py \
  --runner auto \
  --cpu-only \
  --view cli \
  src/stowage/__main__.py
```

### 2. Shareable deep-dive artifact

```bash
python /Users/mrx-ksjung/.codex/skills/scalene-profiler/scripts/run_scalene_profile.py \
  --runner uv \
  --view standalone \
  --profile-only src/stowage,src/tui \
  src/stowage/__main__.py
```

### 3. Memory + copy-volume focused rerun

```bash
python /Users/mrx-ksjung/.codex/skills/scalene-profiler/scripts/run_scalene_profile.py \
  --runner uv \
  --memory \
  --stacks \
  --profile-exclude tests,.venv \
  --view standalone \
  path/to/driver.py
```

## Interpretation rules

- High **Python** time: optimize Python logic first.
- High **native** time: the cost is likely inside an extension or external library.
- High **system** time: investigate I/O, sleep, waiting, or process coordination.
- High **net memory**: inspect allocation growth and object lifetime.
- High **Copy (MB/s)**: look for needless conversions or duplicated buffers.
- Leak warnings are leads, not proof. Confirm them with a focused rerun.

## Interactive / noisy programs

- For Textual/TUI or long-running flows, prefer a minimal driver that reproduces the slow path.
- If startup noise dominates, use `--off` and follow the background on/off workflow described in `references/scalene-playbook.md`.

## References

- Read `references/scalene-playbook.md` for the official-command summary, option guidance, and repo-specific notes.
