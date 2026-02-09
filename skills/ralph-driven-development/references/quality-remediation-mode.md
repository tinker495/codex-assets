# Quality Remediation Mode

Mode C is for fixing quality-gate failures (not feature delivery).

## Entry Conditions

- User asks to fix complexity failures directly.
- Tool output includes `xenon FAIL` and/or `radon` C+ offenders.

## Baseline

```bash
uv run radon cc src -s -n C
uv run xenon --max-absolute B --max-modules A --max-average A src
```

## Repair Sequence

1. Fix block offenders first (C/D blocks).
2. Re-run baseline commands.
3. If module-rank failures remain, reduce module average complexity:
   - flatten branch-heavy helpers
   - split mixed responsibilities
   - remove duplicate condition paths
4. Re-run baseline commands again.

## Completion Criteria

- `radon cc src -n C` returns no offenders.
- `xenon` exits with success code under target thresholds.
- Required lints/tests for touched area pass.

## Reporting Contract

- list fixed offenders
- list remaining offenders (if blocked)
- include exact commands run and pass/fail result
