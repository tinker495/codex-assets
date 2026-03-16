---
name: todo-inventory
description: Inventory code TODO markers and summarize newly added TODOs in the current git diff. Use when asked to list TODOs left in a repo, audit deferred follow-up work, check whether this session added new TODOs, or prepare wrap-up and handoff notes with explicit TODO status.
metadata:
  short-description: Inventory remaining and newly added TODOs
---

# Todo Inventory

## Use Cases

- "이 레포에 남은 TODO 좀 정리해줘"
- "이번 diff에서 새로 추가된 TODO만 보여줘"
- "세션 마무리 전에 TODO 현황 요약해줘"

## Success Criteria

- Triggering: Triggers on requests to list remaining TODOs, audit deferred follow-up markers, or summarize TODO status for wrap-up and handoff. Does not trigger on general bug fixing or broad code review requests with no TODO focus.
- Functionality: Produces a scoped TODO inventory, reports TODOs newly added in the current diff when git metadata is available, and surfaces skipped files instead of silently hiding them.
- Baseline improvement: Replaces ad hoc `rg TODO` and manual diff inspection with one deterministic scan and a compact summary.

## Overview

Use this skill to inventory remaining `TODO` markers in source/config files and to report TODOs newly introduced in the current git diff. The scan includes comment-style TODOs and explicit string-literal placeholders such as `"TODO: ..."`, `"### TODO"`, or `"1. **TODO** ..."`. Prefer the bundled script for deterministic output and use `--json` when another skill, report, or automation needs structured data.

## Workflow

1. Define the scan scope.
- Default to the repository or directory the user is working in.
- If the request is about a specific package, module, or changed file set, pass that narrower root path to the script instead of scanning the whole repo.

2. Run the inventory script.
- Default command:
  ```bash
  python3 ~/.codex/skills/todo-inventory/scripts/todo_inventory.py <root>
  ```
- For machine-readable output:
  ```bash
  python3 ~/.codex/skills/todo-inventory/scripts/todo_inventory.py <root> --json
  ```
- To report only TODOs newly added in the current git diff:
  ```bash
  python3 ~/.codex/skills/todo-inventory/scripts/todo_inventory.py <root> --mode diff
  ```
- To widen scanning beyond code/config files and include all text files under the root:
  ```bash
  python3 ~/.codex/skills/todo-inventory/scripts/todo_inventory.py <root> --all-text
  ```

3. Interpret the results conservatively.
- `Current TODOs` means TODO markers presently found under the scan root.
- `Added TODOs In Current Diff` means TODO markers introduced by staged or unstaged changes in the current git working tree.
- If git metadata is unavailable, report that diff-based TODO status could not be computed instead of guessing.
- If files were skipped because they are binary or non-UTF-8, mention that explicitly when it affects confidence.

4. Report in a compact shape.
- Summary:
  - current TODO count
  - files containing TODOs
  - newly added TODO count in diff
  - skipped-file count
- Then list concrete items as `path:line text`.
- For wrap-up use, separate:
  - remaining TODOs
  - newly added TODOs in diff
  - TODO status unavailable or reported-without-inline-TODO when applicable

## Guardrails

- Do not silently expand from scoped paths to the entire repo.
- Do not treat `FIXME`, `TBD`, or generic prose mentions like `"TODO Inventory"` as `TODO` unless the user explicitly asks for broader markers.
- Do not infer ownership or prioritization from the presence of a TODO comment alone; only inventory and summarize.
- Do not hide skipped files. Surface them so the caller can decide whether to rerun with a different scope.

## Session Wrap-Up Handoff

When `session-wrap-up` or another reporting skill needs TODO status, provide:
- scan root used
- current TODO count and concrete list
- newly added TODO count from the current diff
- skipped files with reason
- any important caveat such as "not a git repo" or "diff unavailable"

## Testing Notes

- Trigger on obvious TODO inventory requests.
- Trigger on paraphrases about deferred follow-up markers or wrap-up TODO status.
- Avoid triggering on unrelated debugging or implementation-only requests.
- Test `--mode both` and `--mode diff` in a git repo.
- Test one non-repo directory to confirm diff-unavailable behavior is explicit.

## Resources

### scripts/

- `scripts/todo_inventory.py`: inventory current TODO markers and newly added TODOs in the current git diff with text or JSON output.
