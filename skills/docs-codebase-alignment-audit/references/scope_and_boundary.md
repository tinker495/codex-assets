# Scope and Boundary Rules

## Scope
- Default working set: `git ls-files docs`
- Prefer tracked Markdown files (`*.md`) for alignment edits.
- Include `AGENTS.md`, `docs/index.md`, and `src/**/AGENTS.md` when the request touches navigation or agent guidance.
- Keep binary assets (`.png`, `.pdf`) untouched unless the user explicitly requests binary regeneration.

## As-Is vs To-Be
- As-Is docs: operational documentation tied to current code layout and commands.
- To-Be docs: forward design/spec documentation that can intentionally diverge from runtime code.
- Prefer `docs/specs/**` as To-Be namespace. Treat legacy `docs/full-plan/**` as To-Be when boundary text says so.

## Classification Heuristics
- If a document explicitly states As-Is/To-Be separation, treat implementation mismatch as expected unless it causes reader confusion.
- Fix broken references in both As-Is and To-Be docs; this is mechanical consistency, not design rewriting.

## Minimal Diff Policy
- Prefer replacing one stale path with one canonical path.
- Avoid broad prose rewrites when only a path/target is wrong.
- Keep root AGENTS map-first; move deep details to linked docs.
- Always re-run baseline checks after edits.

## Intermediate Artifact Policy
- Default location for temporary reports, extracted path lists, and audit snapshots: `/private/tmp`.
- Do not leave transient markdown reports under `docs/` or repository root.
- Create repository files only when the user explicitly asks for persistent in-repo documentation.
