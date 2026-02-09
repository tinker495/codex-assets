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
