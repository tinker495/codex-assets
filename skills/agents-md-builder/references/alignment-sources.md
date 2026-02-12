# Cross-Agent Alignment Sources

Use this reference only when `CLAUDE.md` and/or `GEMINI.md` exists in the target repository.

## Source Priority

Apply this precedence when guidance conflicts:

1. Executable repository evidence (`Makefile`, scripts, CI workflow commands)
2. Toolchain config (`pyproject.toml`, package manager config, lock files)
3. Existing root `AGENTS.md`
4. `CLAUDE.md` / `GEMINI.md`
5. Generic defaults

## Alignment Scope

Reconcile the following into the final `AGENTS.md`:

- Command surface: setup, lint/format, full test, single-test targeting.
- Hard constraints: forbidden directories/files, generated artifacts policy, naming conventions.
- Workflow gates: minimum verification before handoff, CI parity checks.
- Search/debug preferences: required tools and fallback sequence.

## Fast Check Matrix

For each row, confirm if present in sibling docs and reflected in `AGENTS.md`:

- Setup bootstrap command
- Lint command
- Format check command
- Default test command
- Single-test command example
- Forbidden edit zones / protected paths
- Mandatory verification gate
- Required search flow (if documented)

## Conflict Rule

When sibling docs disagree:

- Keep only commands that are executable in repository evidence.
- Keep stricter safety rules unless contradicted by executable evidence.
- Record unresolved ambiguity in `Assumptions` with concrete file references.
