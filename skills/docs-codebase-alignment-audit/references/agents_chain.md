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

1. Root -> Local entrypoint check
- Root `AGENTS.md` should reference at least the major local entrypoints used in active work.

2. Docs index -> Local AGENTS inventory check
- `docs/index.md` Local AGENTS section should include every discovered local AGENTS path.

3. Parent -> Child AGENTS check
- Parent AGENTS files should list relevant direct child AGENTS where child-specific rules exist.

4. SSOT contract check
- `docs/_meta/docs-contract.md` (or equivalent) should include `src/**/AGENTS.md` in As-Is SSOT when local AGENTS are active.

## Fix Scope

- Fix missing paths/list entries only.
- Do not rewrite unrelated prose or policy sections.
- Keep ordering stable unless sorted order is an existing convention.
