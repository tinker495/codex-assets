# AGENTS.md Quality Checklist

Run this checklist before delivering AGENTS.md updates.

## Accuracy

- Confirm commands match the repository toolchain.
- Confirm paths are valid and repository-relative.
- Confirm language/framework references match actual project files.
- Label uncertain items in an `Assumptions` section.

## Clarity

- Use imperative sentences.
- Keep each rule specific and testable.
- Remove vague phrases ("appropriately", "as needed", "best practices").
- Avoid duplicated instructions across sections.

## Completeness

- Include scope/priorities.
- Include setup assumptions.
- Include build/test/lint commands.
- Include editing constraints that prevent common breakage.
- Include minimum verification steps before handoff.

## Consistency

- Ensure no conflict with existing project docs.
- Ensure command examples use consistent shell style.
- Ensure terminology is consistent across sections.

## Practicality

- Prefer shortest command that proves correctness.
- Separate mandatory checks from optional checks.
- Keep file concise; trim low-value background text.
