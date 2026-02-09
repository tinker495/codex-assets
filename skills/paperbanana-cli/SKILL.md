---
name: paperbanana-cli
description: Run the local PaperBanana installation to generate methodology diagrams, generate statistical plots, and evaluate generated diagrams from any workspace. Use when the user asks for PaperBanana `generate`, `plot`, `evaluate`, NeurIPS-style academic figure generation from text/data, or comparative diagram quality scoring against a human reference.
---

# PaperBanana CLI

## Overview

Execute PaperBanana commands without requiring the current working directory to be `~/project/paperbanana`.
Use this skill as the default operational path for PaperBanana tasks in Codex.

## Workflow

```text
Request -> Preflight -> Route Task -> Run CLI -> Return Output Path + Next Action
```

1. Run preflight checks:
   - `bash scripts/run_paperbanana.sh --help`
   - Confirm `GOOGLE_API_KEY` is available in env or `.env`.
2. Route by intent:
   - Methodology diagram: run **Diagram Eligibility Gate** first, then use `generate` only if it passes.
   - Statistical plot: use `plot`.
   - Comparative scoring: use `evaluate`.
3. Execute through the wrapper script:
   - `bash scripts/run_paperbanana.sh <subcommand> ...`
   - For `generate`, prefer stable wrapper: `bash scripts/generate_with_stable_output.sh ...`
4. Report:
   - Exact command used.
   - Output file path (`--output` if provided, otherwise PaperBanana auto path).
   - Any validation caveats (missing caption/context/reference).

## No Dummy Runs Policy (MANDATORY)

Do not run dummy/smoke generation that creates throwaway artifacts.

1. Allowed preflight:
   - `bash scripts/run_paperbanana.sh --help`
   - Environment checks only (`GOOGLE_API_KEY`, paths).
2. Disallowed:
   - Any synthetic `generate` call only for tool health check.
   - Any placeholder diagram output not requested by user.
3. Execution rule:
   - Run `generate` only when real user target exists (real source text + intended output path).
   - If blocked, report blocker instead of producing a dummy output.

## Diagram Eligibility Gate (MANDATORY)

Apply this gate before any `generate` call.

1. Hard no-go (do **not** diagramize):
   - Table-of-contents order, reading order, onboarding order.
   - Simple numbered checklists without branching.
   - Single linear sequence that adds no spatial/causal insight.
   - Plain schema/type listings and code-like pseudo-structures.
2. Borderline threshold:
   - Generate only when at least **2** complexity signals are present:
     - Branching decisions (if/else paths).
     - Feedback loop or cyclic dependency.
     - Multi-actor handoff across 3+ components.
     - Spatial state mapping (grid/stack/before-after occupancy).
3. Default behavior for ambiguous cases:
   - Prefer keeping existing text/ASCII.
   - Report skipped conversion with one-line reason: `below diagram threshold`.

## Task Commands

### Generate Diagram

```bash
bash scripts/generate_with_stable_output.sh \
  --input <method_txt> \
  --caption "<figure_caption>" \
  --output <target.png> \
  --iterations 3
```

### Generate Plot

```bash
bash scripts/run_paperbanana.sh plot \
  --data <data.csv|data.json> \
  --intent "<visual_intent>" \
  --iterations 3
```

### Evaluate Diagram

```bash
bash scripts/run_paperbanana.sh evaluate \
  --generated <generated.png> \
  --reference <human_reference.png> \
  --context <method_txt> \
  --caption "<figure_caption>"
```

## Input Contract

- `generate`:
  - Required: method text file, caption.
  - Optional: `--output`, `--iterations`.
- `plot`:
  - Required: CSV/JSON data file, intent.
  - Optional: `--output`, `--iterations`.
- `evaluate`:
  - Required: generated image, reference image, method context file, caption.

## Troubleshooting

1. `paperbanana: command not found`
   - Wrapper automatically falls back to `uv run --project /Users/mrx-ksjung/project/paperbanana`.
2. Auth/provider failure
   - Verify `GOOGLE_API_KEY` and rerun `paperbanana setup` if needed.
3. Wrong output location
   - Pass `--output` explicitly.
4. Need detailed flags
   - Read `references/usage.md`.

## Resources

- `scripts/run_paperbanana.sh`: stable CLI entrypoint with fallback behavior.
- `scripts/generate_with_stable_output.sh`: generate wrapper that resolves actual output path and writes deterministically to target file.
- `references/usage.md`: verified command/flag reference aligned with the local install at `/Users/mrx-ksjung/project/paperbanana`.
