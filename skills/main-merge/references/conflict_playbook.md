# Conflict Playbook

Use this playbook when `git merge origin/main` reports conflicts.

## Fast Classification

| Conflict type | Typical signs | Preferred action |
| --- | --- | --- |
| Import/order noise | only import block changed | Keep minimal superset, then run formatter/lint |
| Signature mismatch | function args or return shape diverged | Preserve current branch intent, adapt callers to latest main contract |
| Deleted vs modified | file deleted in one side, edited in other | Verify runtime references with `rg -n`; keep deletion only if truly unused |
| Config/schema drift | enum/constants/schema edited in both sides | Merge with backward compatibility where possible; update docs/specs immediately |
| Test fixture drift | fixture names/data changed | Update fixtures to match merged runtime behavior, not vice versa |

## Resolution Loop

1. List unresolved files:

```bash
git diff --name-only --diff-filter=U
```

2. For each file, inspect conflict blocks and surrounding symbol usage:

```bash
rg -n "<symbol_name>" src tests docs
```

3. Resolve in file, then stage:

```bash
git add <file>
```

4. Run focused checks for touched behavior:

```bash
# example
pytest -q tests/path/to/affected_test.py -k "<keyword>"
```

5. Continue merge after all unresolved files are staged:

```bash
git merge --continue
```

If the shell is non-interactive and git cannot open an editor, run:

```bash
GIT_EDITOR=true git merge --continue
```

## Guardrails

- Do not use destructive git commands.
- Do not force-pick one side for every file without symbol-level review.
- If intent is ambiguous after evidence checks, ask one targeted question.
