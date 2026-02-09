# PaperBanana Usage Reference

Verified against local project: `/Users/mrx-ksjung/project/paperbanana`

## Core Commands

```bash
paperbanana generate --input <method.txt> --caption "<caption>" --iterations 3
paperbanana plot --data <data.csv|data.json> --intent "<intent>" --iterations 3
paperbanana evaluate --generated <generated.png> --reference <reference.png> --context <method.txt> --caption "<caption>"
paperbanana setup
```

## Common Flags

- `generate`
  - `--input/-i` (required), `--caption/-c` (required), `--output/-o` (optional), `--iterations/-n` (optional)
- `plot`
  - `--data/-d` (required), `--intent` (required), `--output/-o` (optional), `--iterations/-n` (optional)
- `evaluate`
  - `--generated/-g` (required), `--reference/-r` (required), `--context` (required), `--caption/-c` (required)

## Output Behavior

- Without `--output`, artifacts are saved under `outputs/run_<timestamp>/...`.
- With `--output`, write directly to the provided path.

## Environment

- Requires `GOOGLE_API_KEY`.
- Wrapper fallback path can be overridden with:
  - `export PAPERBANANA_HOME=/absolute/path/to/paperbanana`
