# PaperBanana Usage Reference

Verified against local project: `/Users/mrx-ksjung/project/paperbanana`

## Core Commands

```bash
paperbanana generate --input <method.txt> --caption "<caption>" --output <target.png> --iterations 3
paperbanana plot --data <data.csv|data.json> --intent "<intent>" --iterations 3
paperbanana evaluate --generated <generated.png> --reference <reference.png> --context <method.txt> --caption "<caption>"
paperbanana setup
```

Skill-local stable wrapper:

```bash
bash scripts/generate_with_stable_output.sh --input <method.txt> --caption "<caption>" --output <target.png> --iterations 3
bash scripts/generate_with_stable_output.sh --input <method.txt> --caption "<caption>" --output <target.png> --iterations 3 --output-resolution 1k --image-profile flash
```

## Common Flags

- `generate`
  - `--input/-i` (required), `--caption/-c` (required), `--output/-o` (optional), `--iterations/-n` (optional)
  - `--output-resolution` (optional: `1k|2k|4k`, default `1k`), `--resolution` (optional alias)
  - `--image-profile` (optional: `flash|pro`), `--flash` (optional shortcut for `--image-profile flash`)
- `plot`
  - `--data/-d` (required), `--intent` (required), `--output/-o` (optional), `--iterations/-n` (optional)
- `evaluate`
  - `--generated/-g` (required), `--reference/-r` (required), `--context` (required), `--caption/-c` (required)

## Image Profile Mapping

- `flash` -> `gemini-2.5-flash-image` (Nano Banana flash)
- `pro` -> `gemini-3-pro-image-preview`
- default -> `pro`
- With `--image-provider openrouter_imagen`, wrapper auto-maps to:
  - `google/gemini-2.5-flash-image` or `google/gemini-3-pro-image-preview`
- Do not combine `--image-profile` with explicit `--image-model`.

## Flash Compatibility Notes

- `gemini-2.5-flash-image` may return `400 INVALID_ARGUMENT` if provider sends `image_size`.
- Current PaperBanana patch avoids `image_size` for Flash and uses `aspect_ratio` + post-generation resize to the requested output resolution.
- If this error reappears, verify the local branch includes the latest provider patch before retrying generation.

## Output Resolution Mapping

- `1k` -> 1024x576 (default)
- `2k` -> 1792x1024
- `4k` -> 3072x1728
- Flash may emit a native size first (for example 1024x1024 or 1344x768), then be normalized to the target resolution during save.

## Output Behavior

- Without `--output`, artifacts are saved under `outputs/run_<timestamp>/...`.
- With `--output`, write directly to the provided path.

## Diagram Threshold Policy

Run `generate` only when diagram value is clear.

- Skip conversion for:
  - TOC/read-order flow
  - basic checklists
  - trivial linear pipelines with no branch/loop
  - code/schema listings
- Convert only if at least two are true:
  - branch exists
  - feedback loop exists
  - 3+ component handoff exists
  - spatial state layout matters (stack/grid/before-after)
- Ambiguous case default: keep text/ASCII and log `below diagram threshold`.

## No Dummy Runs Policy

- Do not run synthetic/dummy `generate` commands just to verify tool health.
- Preflight must stay non-artifact: use `--help` and env checks only.
- Execute `generate` only when user requested a real deliverable and target output path is defined.

## Environment

- Requires `GOOGLE_API_KEY`.
- Wrapper fallback path can be overridden with:
  - `export PAPERBANANA_HOME=/absolute/path/to/paperbanana`
