# JAxtar Quality Profile

Optional specialization profile.
Apply this only when the target repository is JAxtar.

## Environment

1. Activate Python 3.12 environment before checks.
2. Run commands from repo root.

## Quality Gates

Primary checks:

```bash
pytest -q
pre-commit run --all-files
```

Focused checks for story scope:

```bash
pytest tests/test_diffusion_drop_analysis.py
pytest -k "diffusion and not slow"
```

## Iteration Heuristics for JAxtar

1. Keep JAX-traced code pure and side-effect free.
2. Prefer `jax.lax.while_loop`/`jax.lax.scan` in traced loops.
3. Avoid Python mutable data structures inside JIT paths.
4. Use explicit dtypes and avoid accidental host<->device transfers.
5. Preserve deterministic RNG handling with `jax.random.PRNGKey` and splits.

## Story Templates for JAxtar

- Algorithm slice: "Update one search operator and its tests."
- Heuristic slice: "Adjust one heuristic scoring path and benchmark impact."
- Utility slice: "Modify one batch utility and validate callsites."

## Completion Evidence

Mark `passes: true` only with:

1. Relevant tests passing.
2. Lint/format checks passing for touched files.
3. Short note in `progress.txt` documenting JAX-specific risks or decisions.
