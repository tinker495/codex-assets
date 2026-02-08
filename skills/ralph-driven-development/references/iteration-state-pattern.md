# Iteration State Pattern

Use repository-local state files for Ralph iterations.

## Mode A (PRD loop)

- Source of truth: `prd.json`
- Progress ledger: `progress.txt`

## Mode B (ordered spec runner)

- Completion ledger: `docs/done.md`
- Execution logs: `docs/logs/agent-run.log`

## Rules

1. Keep ledgers append-only.
2. Do not mark completion without objective evidence.
3. Resume by reading existing state first, then process the next pending story/spec.
