---
name: agents-md-builder
description: Create or update repository AGENTS.md files with actionable, repo-specific instructions for AI coding agents. Use when a user asks to write, improve, standardize, or audit AGENTS.md (or equivalent agent-instruction documents), especially for build/test commands, coding rules, directory conventions, and collaboration workflow.
---

# AGENTS.md Builder

## Overview

Create high-signal AGENTS.md instructions that another coding agent can execute immediately in the target repository.
Focus on concrete commands, paths, constraints, and decision rules. Avoid generic policy text.
Every generated AGENTS file must start with the exact first line: `# AGENTS.md`.

## Mandatory Requirements (Claude-aligned)

- Always include concrete build, lint/format, and test commands.
- Include at least one targeted single-test command when the toolchain supports it.
- Include a high-level architecture section that explains multi-file flows and boundaries.
- Validate the generated `AGENTS.md` header with exact match (`# AGENTS.md` only on line 1, no suffix/prefix).
- Read and incorporate important constraints from:
  - `README*`
  - existing `AGENTS.md`
  - `CLAUDE.md` (if present)
  - `GEMINI.md` (if present)
  - `.cursor/rules/*` or `.cursorrules`
  - `.github/copilot-instructions.md`
  - CI workflow files when present
- Run a cross-agent alignment pass when `CLAUDE.md` and/or `GEMINI.md` exists:
  - Align command surface (setup/lint/test/targeted test commands)
  - Align non-negotiable constraints (naming, path rules, forbidden edits, workflow gates)
  - Resolve conflicts by preferring repository evidence (`Makefile`, CI, pyproject, executable scripts)
- If `AGENTS.md` already exists, suggest specific improvements before (or alongside) applying edits.
- Avoid repetition and avoid obvious generic guidance.
- Do not enumerate every file/component that is easily discoverable.
- Do not invent unsupported sections (for example, "Common Development Tasks", "Tips for Development", "Support and Documentation") unless those sections exist in repository evidence.
- If data is missing, mark it in an `Assumptions` section instead of guessing.

## Workflow

1. Collect repository context.
- Detect languages, package managers, build/test/lint tools, and key folders.
- Read existing docs if present: `README*`, `CONTRIBUTING*`, existing `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, CI config.
- Check for agent-rule files: `.cursor/rules/*`, `.cursorrules`, `.github/copilot-instructions.md`.
- Infer conservatively when data is missing and mark assumptions explicitly.

2. Choose output mode.
- Create mode: add a new root `AGENTS.md` using `assets/AGENTS.template.md` as baseline.
- Improve mode: keep valid project-specific guidance and rewrite only weak or ambiguous sections.
- Improvement-first behavior: when AGENTS already exists, provide a concise improvement proposal before finalizing edits.
- Compact mode: provide required sections only when the user requests brevity.

3. Write the document.
- Use imperative wording and unambiguous rules.
- Prefer exact commands (for example `go test ./...`, `npm run lint`) over tool names alone.
- Include repository-relative paths and boundaries between subprojects.
- Include at least one single-test command example when supported.
- Add a high-level architecture section that captures cross-file interactions and major boundaries.
- Encode constraints that prevent unsafe edits (generated files, schema migrations, secrets).

4. Validate before delivery.
- Run the checklist in `references/quality-checklist.md`.
- Run the cross-agent alignment checks in `references/alignment-sources.md` when `CLAUDE.md` or `GEMINI.md` exists.
- Confirm each command exists in the repository or label it as an assumption.
- Confirm the final `AGENTS.md` first line is exactly `# AGENTS.md`.
- Remove contradictions and duplicate guidance.
- Keep sections short and scannable.

## Section Requirements

Read `references/sections-guide.md` and include at minimum:
- Scope and priorities
- Setup and environment assumptions
- Build, test, and lint commands (plus single-test command when available)
- High-level architecture and structure
- Editing rules and style constraints
- Verification expectations before handoff
- Commit/PR or delivery workflow when relevant

## Customization Rules

- Align with existing project conventions unless the user explicitly requests changes.
- Trust repository evidence over generic best practices.
- Avoid adding sections that are not backed by repository context.
- Group commands by path when subprojects use different toolchains.
- Prefer concise architecture summaries over exhaustive directory dumps.

## Output Behavior

- Write to repository root by default when the user asks to "make AGENTS.md."
- Patch existing files in place when the user asks to improve/refactor AGENTS.md.
- Add an `Assumptions` section when critical details cannot be verified.
- If AGENTS already exists, include concrete improvement suggestions in the response.

## Resources

- Use `assets/AGENTS.template.md` as a reusable starter.
- Use `references/sections-guide.md` for section-level guidance.
- Use `references/quality-checklist.md` for final validation.
- Use `references/alignment-sources.md` for `CLAUDE.md`/`GEMINI.md` alignment rules.
