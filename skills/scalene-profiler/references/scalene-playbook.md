# Scalene Playbook

## Source snapshot

- Official repository README: <https://github.com/plasma-umass/scalene/blob/master/README.md>
- Installed CLI verified in this environment on 2026-03-25:
  - `scalene --help`
  - `scalene run --help`
  - `scalene run --help-advanced`
  - `scalene view --help`
- Installed version observed locally: `2.2.1 (2026.03.22)`

## What Scalene is good at

Scalene is most useful when you need runtime evidence instead of static guesses:

- line-level CPU hotspots
- Python vs native vs system time split
- memory growth and allocation hotspots
- likely memory leak hints
- copy-volume hotspots at Python/library boundaries
- optional GPU time (Scalene docs say NVIDIA-only)
- JSON + CLI + HTML/standalone artifact generation

The README also emphasizes that Scalene is sampling-based, line-level, and typically adds modest overhead compared with many profilers.

## Command model

Scalene uses two top-level commands:

- `run`: collect a profile into JSON
- `view`: render an existing JSON profile in browser, terminal, or HTML

Useful patterns from the docs and local help:

- `scalene run your_prog.py`
- `python3 -m scalene run your_prog.py`
- `scalene view --cli myprofile.json`
- `scalene view --standalone myprofile.json`

## Options that matter most

### Scope control

- `--profile-only a,b,c`: include only matching paths
- `--profile-exclude a,b,c`: exclude matching paths
- `--profile-all`: include everything, not just the target tree
- `--profile-system-libraries`: include stdlib and installed packages

### Detail level

- `--cpu-only`: fastest first pass
- `--memory`: explicit memory profiling flag
- `--gpu`: request GPU profiling
- `--stacks`: collect stack traces
- `--profile-interval N`: emit periodic profile snapshots

### Noise control / sensitivity

- `--use-virtual-time`: ignore blocking and I/O time
- `--cpu-percent-threshold N`: hide low-CPU lines
- `--cpu-sampling-rate N`: trade off fidelity and overhead
- `--allocation-sampling-window N`: change memory sampling granularity
- `--malloc-threshold N`: hide low-allocation lines

## Interpretation hints

- High **Python** time: optimize Python logic first.
- High **native** time: the cost is likely inside an extension or external library.
- High **system** time: suspect I/O, sleeps, blocking, or process coordination.
- Positive **net memory**: memory growth; negative means reclamation.
- High **Copy (MB/s)**: investigate unnecessary conversions or repeated copies.
- Leak detector hits: treat as leads, then verify manually.

## Focused profiling

Scalene supports `@profile` on specific functions. The README explicitly says not to import `profile`; just decorate the target function and run under Scalene.

Use this when a whole-program run is too noisy but you already have a likely hotspot.

## Background / interactive workflows

Local advanced help shows this pattern:

- `scalene run --off prog.py`
- `python3 -m scalene.profile --on --pid <PID>`
- `python3 -m scalene.profile --off --pid <PID>`

Use it when the startup path is noisy or an interactive session only matters after a certain point.

## Repo-specific notes for this workspace

- This repo is `uv`-managed. If the target imports project dependencies, prefer the helper script with `--runner uv`.
- Candidate entry scripts discovered locally:
  - `src/stowage/__main__.py`
  - `src/tui/app.py`
- For Textual/TUI behavior, prefer a small reproducible driver over ad-hoc manual clicking. Profile the minimal scenario that loads data or triggers the expensive planner path.

## Suggested profiling loop

1. Start with `--cpu-only --view cli` for a cheap hotspot scan.
2. Re-run with HTML/standalone output for the narrowed target.
3. Add `--profile-only` / `--profile-exclude` to cut noise.
4. Add `@profile` or `--stacks` only after the first hotspot is clear.
5. Report exact artifact paths and the hottest lines/functions, not vague impressions.
