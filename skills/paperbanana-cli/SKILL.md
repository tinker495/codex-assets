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
   - Methodology diagram: use `generate`.
   - Statistical plot: use `plot`.
   - Comparative scoring: use `evaluate`.
3. Execute through the wrapper script:
   - `bash scripts/run_paperbanana.sh <subcommand> ...`
4. Report:
   - Exact command used.
   - Output file path (`--output` if provided, otherwise PaperBanana auto path).
   - Any validation caveats (missing caption/context/reference).

## Task Commands

### Generate Diagram

```bash
bash scripts/run_paperbanana.sh generate \
  --input <method_txt> \
  --caption "<figure_caption>" \
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
- `references/usage.md`: verified command/flag reference aligned with the local install at `/Users/mrx-ksjung/project/paperbanana`.
