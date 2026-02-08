# AGENTS.md Section Guide

Use this guide to decide what to include and how detailed each section should be.
Prefer repository-specific facts over generic instructions.

## Recommended Order

1. Scope
2. Repository Map
3. Setup
4. Commands
5. Editing Rules
6. Verification
7. Delivery Workflow
8. Assumptions (only when needed)

## Section Details

### Scope

State what the file governs and what it does not.
Include priorities (for example: correctness over speed, minimal diffs, preserve behavior).

### Repository Map

List high-value directories and ownership boundaries.
Include only folders that affect implementation decisions.

### Setup

State runtime/toolchain assumptions and how to initialize dependencies.
Include version constraints when known.

### Commands

Provide copy-pasteable commands for:
- Build
- Test
- Lint/format
- Targeted test execution when useful

Group commands by subproject if needed, with explicit paths.

### Editing Rules

Capture constraints such as:
- Do not edit generated files directly
- Keep API compatibility
- Follow migration ordering rules
- Preserve logging/telemetry conventions

### Verification

Define minimum checks before handoff.
Specify which commands are mandatory and which are optional in constrained environments.

### Delivery Workflow

Describe commit/PR expectations when relevant:
- Commit style
- Required summary contents
- Risk callouts or rollback notes

### Assumptions

Use only when key facts are missing.
Write each assumption as a concrete statement to confirm.

## Anti-Patterns

- Broad statements without commands or paths
- Contradictory rules across sections
- Sections that repeat README text without adding agent-specific guidance
- Non-actionable wording such as "follow best practices"
