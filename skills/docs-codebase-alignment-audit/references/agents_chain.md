# AGENTS Chain Checklist

Use this checklist when a repository uses hierarchical `AGENTS.md` files.

## Target Set

1. Root entrypoint: `AGENTS.md`
2. Docs index hub: `docs/index.md`
3. Local context files: `src/**/AGENTS.md`

Discover local context files with:

```bash
find src -type f -name AGENTS.md | sort
```

## Checks

1. Discovery-contract check
- Read root `AGENTS.md` and the docs contract before deciding whether navigation is explicit-list or command-discovery based.
- Treat the repository's declared mechanism as SSOT. Do not invent a second inventory.

2. Root -> Local entrypoint check
- Root `AGENTS.md` should explain how local instructions are discovered.
- Root `AGENTS.md` should stay map-like and point to deeper docs instead of duplicating full policy text.

3. Docs index check
- If the contract requires explicit inventory, `docs/index.md` should include every discovered local AGENTS path.
- If the contract names `find src -name AGENTS.md` or equivalent as SSOT, verify that discoverability contract instead of copying paths into the index.

4. Parent -> Child AGENTS check
- Require parent-child links only when the repository contract or established local pattern requires them.

5. SSOT contract check
- `docs/_meta/docs-contract.md` (or equivalent) should include `src/**/AGENTS.md` in As-Is SSOT when local AGENTS are active.

6. Progressive disclosure continuity
- `AGENTS.md` should point to `docs/index.md`.
- `docs/index.md` should expose guides/reference/specs and the repository's chosen local-AGENTS discovery route.

## Fix Scope

- Fix missing paths/list entries only.
- Do not rewrite unrelated prose or policy sections.
- Keep ordering stable unless sorted order is an existing convention.
