# AGENTS.md

## Scope

- Apply these instructions to this repository unless a deeper `AGENTS.md` overrides them.
- Prioritize: [correctness | minimal diffs | backward compatibility | delivery speed].

## Setup

- Runtime/toolchain: [examples: Go 1.23, Node 22, Python 3.12]
- Install dependencies:
  - `[command]`
  - `[command]`

## Commands

- Build:
  - `[command]`
- Test:
  - `[command]`
- Single test:
  - `[command]`
- Lint/Format:
  - `[command]`

If multiple subprojects exist, provide commands per path:
- `path/to/subproject-a`: `[build/test/lint commands]`
- `path/to/subproject-b`: `[build/test/lint commands]`

## High-Level Architecture

- [Describe major modules and how requests/data flow across multiple files.]
- [Call out boundaries and ownership between subprojects/services.]
- [Include only architecture that affects implementation decisions.]

## Editing Rules

- Do not edit generated artifacts directly. Regenerate via `[command]`.
- Follow migration order: `[rule]`.
- Keep public interfaces backward compatible unless requested otherwise.
- Preserve existing logging/telemetry/error handling patterns.

## Verification Before Handoff

- Run mandatory checks:
  - `[command]`
  - `[command]`
- If checks cannot run locally, state why and list risk areas.

## Delivery Workflow

- Keep changes scoped to the requested task.
- Summarize touched files and behavioral impact.
- Highlight risks, tradeoffs, and follow-up checks.

## Assumptions

- [Assumption 1 to confirm]
- [Assumption 2 to confirm]
