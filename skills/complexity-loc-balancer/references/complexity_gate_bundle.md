# Complexity Gate Bundle

Use this command bundle at baseline and after each remediation cycle.

## Required Commands

```bash
uv run ruff check src tests
uv run radon cc src -s -n C
uv run xenon --max-absolute B --max-modules A --max-average A src
```

## Optional Targeted Regression Check

Run focused tests for touched modules after each accepted cycle.

Examples:

```bash
uv run pytest tests/routing/test_rotation_history.py -q
uv run pytest tests/tui/test_app.py::test_side_view_click_loads_bay_overlay_without_hanging -q
```

## Gate Interpretation

- `radon` no C+ offenders: block gate pass.
- `xenon` zero failures: module/average gate pass.
- `ruff` pass: basic static quality pass.

Only mark cycle as accepted when all required commands pass and non-test net delta remains `<= 0`.
