# AGENTS.md Quality Checklist

Run this checklist before delivering AGENTS.md updates.

## Accuracy

- Confirm the first line is exactly `# AGENTS.md`.
- Confirm header match is exact (line 1 only, no trailing title text like `# AGENTS.md - ...`).
- Confirm commands match the repository toolchain.
- Confirm at least one single-test command is included when supported.
- Confirm paths are valid and repository-relative.
- Confirm language/framework references match actual project files.
- Confirm key constraints from `README*`, `.cursor/rules/*` or `.cursorrules`, and `.github/copilot-instructions.md` are reflected when present.
- Confirm key constraints from `CLAUDE.md` and `GEMINI.md` are reflected when those files exist.
- Label uncertain items in an `Assumptions` section.

## Clarity

- Use imperative sentences.
- Keep each rule specific and testable.
- Remove vague phrases ("appropriately", "as needed", "best practices").
- Avoid duplicated instructions across sections.
- Avoid obvious generic guidance that is not repository-specific.

## Completeness

- Include scope/priorities.
- Include setup assumptions.
- Include build/test/lint commands.
- Include single-test execution guidance when available.
- Include high-level architecture and structure.
- Include editing constraints that prevent common breakage.
- Include minimum verification steps before handoff.

## Consistency

- Ensure no conflict with existing project docs.
- Ensure no conflict with `CLAUDE.md`/`GEMINI.md` constraints when those files are present.
- Ensure command examples use consistent shell style.
- Ensure terminology is consistent across sections.

## Practicality

- Prefer shortest command that proves correctness.
- Separate mandatory checks from optional checks.
- Keep file concise; trim low-value background text.
- Avoid exhaustive file/component listings that add no decision value.
