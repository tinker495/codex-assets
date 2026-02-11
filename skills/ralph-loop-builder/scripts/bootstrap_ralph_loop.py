#!/usr/bin/env python3
"""Bootstrap a purpose-fit Ralph workspace under .codex/."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path


CORE_FILES = ("README.md", "CODEX.md", "prd.json", "progress.txt", "ralph.sh")
DEFAULT_REVIEW_MODEL = "gpt-5.2"
DEFAULT_REVIEW_REASONING = "xhigh"
DEFAULT_FIX_MODEL = "gpt-5.3-codex"
DEFAULT_FIX_REASONING = "high"


def slugify(value: str) -> str:
    lowered = value.strip().lower()
    lowered = re.sub(r"[^a-z0-9]+", "-", lowered)
    lowered = re.sub(r"-{2,}", "-", lowered).strip("-")
    return lowered


def derive_branch_name(base_ref: str) -> str:
    trimmed = base_ref.strip()
    if not trimmed:
        return "main"
    if "/" not in trimmed:
        return trimmed
    return trimmed.rsplit("/", maxsplit=1)[-1]


def build_audit_stories(workspace: str, purpose: str) -> list[dict]:
    entries = [
        ("AUDIT-001", "Scope + Baseline Gate Snapshot", "01-baseline-gates.md"),
        ("AUDIT-002", "Delegation Ownership Clusters", "02-delegation-clusters.md"),
        ("AUDIT-003", "High-Churn Module Focus Review", "03-high-churn-review.md"),
        ("AUDIT-004", "Cross-Module Consolidation Candidates", "04-cross-module-candidates.md"),
        ("AUDIT-005", "One-Cycle Dry-Run Verdict", "05-dry-run-verdict.md"),
        ("AUDIT-006", "Guardrails and Unknowns", "06-guardrail-unknowns.md"),
        ("AUDIT-007", "Final Backlog Index", "07-backlog-index.md"),
        ("AUDIT-008", "Executive Summary and Go/No-Go", "08-exec-summary-go-no-go.md"),
    ]
    stories: list[dict] = []
    for idx, (story_id, title, report_name) in enumerate(entries, start=1):
        stories.append(
            {
                "id": story_id,
                "title": title,
                "description": f"{purpose} 관점의 audit step {idx}.",
                "acceptanceCriteria": [
                    f"Created .codex/{workspace}/audit/{report_name} with ALL findings",
                    "Report includes severity summary and explicit finding counts",
                    "Every finding includes file path, exact lines, category, and code snippet",
                    "Report does not include fix proposals or implementation plans",
                ],
                "priority": idx,
                "passes": False,
                "notes": (
                    "Audit discipline: no code edits, no fix plans, no skipped files in story scope. "
                    f"Objective: {purpose}. Output markdown content for .codex/{workspace}/audit/{report_name}."
                ),
            }
        )
    return stories


def build_delivery_stories(workspace: str, purpose: str) -> list[dict]:
    entries = [
        ("US-001", "Baseline + Story Scope Definition", "01-scope-baseline.md"),
        ("US-002", "Primary Implementation Slice", "02-primary-slice.md"),
        ("US-003", "Secondary Integration Slice", "03-integration-slice.md"),
        ("US-004", "Quality Gate Stabilization", "04-quality-gates.md"),
        ("US-005", "Final Validation and Wrap-Up", "05-final-wrap-up.md"),
        ("US-006", "Refinement and Edge-Case Coverage", "06-edge-case-coverage.md"),
        ("US-007", "Operational Readiness and Docs", "07-operational-readiness.md"),
        ("US-008", "Release Decision and Handoff", "08-release-handoff.md"),
    ]
    stories: list[dict] = []
    for idx, (story_id, title, report_name) in enumerate(entries, start=1):
        stories.append(
            {
                "id": story_id,
                "title": title,
                "description": f"{purpose} delivery step {idx}.",
                "acceptanceCriteria": [
                    f"Created .codex/{workspace}/audit/{report_name} with run evidence",
                    "Implementation status and remaining risks are explicit",
                    "Gate checks and next action are documented",
                ],
                "priority": idx,
                "passes": False,
                "notes": (
                    f"Focus on story scope for {story_id}. "
                    "Keep verification evidence explicit in report output."
                ),
            }
        )
    return stories


def apply_mutation_policy_to_stories(stories: list[dict], read_only: bool) -> None:
    policy_note = (
        "Mutation policy: read-only. Do not apply code changes."
        if read_only
        else "Mutation policy: read-write. Apply code changes only when required by story scope."
    )
    for story in stories:
        existing = story.get("notes")
        if isinstance(existing, str) and existing.strip():
            story["notes"] = f"{policy_note} {existing}"
        else:
            story["notes"] = policy_note


def require_non_empty(value: str, label: str) -> str:
    trimmed = value.strip()
    if not trimmed:
        raise ValueError(f"{label} must be a non-empty string")
    return trimmed


def build_model_policy(
    read_only: bool,
    review_model: str,
    review_reasoning_effort: str,
    fix_model: str,
    fix_reasoning_effort: str,
) -> dict:
    review_profile = {
        "model": require_non_empty(review_model, "review model"),
        "reasoningEffort": require_non_empty(review_reasoning_effort, "review reasoning effort"),
    }
    fix_profile = {
        "model": require_non_empty(fix_model, "fix model"),
        "reasoningEffort": require_non_empty(fix_reasoning_effort, "fix reasoning effort"),
    }
    default_label = "review" if read_only else "fix"
    fallback_label = "fix" if read_only else "review"
    return {
        "profiles": {"review": review_profile, "fix": fix_profile},
        "defaultLabel": default_label,
        "fallbackLabel": fallback_label,
        "defaultProfile": review_profile if read_only else fix_profile,
        "fallbackProfile": fix_profile if read_only else review_profile,
    }


def parse_story_model_overrides(raw_value: str) -> dict[str, dict[str, str]]:
    source = raw_value.strip()
    if not source:
        return {}

    payload_text = source
    source_path = Path(source)
    if source_path.exists():
        if not source_path.is_file():
            raise ValueError(f"--story-model-overrides path is not a file: {source_path}")
        payload_text = source_path.read_text(encoding="utf-8")

    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON for --story-model-overrides: {exc}") from exc

    if not isinstance(payload, dict):
        raise ValueError("--story-model-overrides must be a JSON object keyed by story id")

    overrides: dict[str, dict[str, str]] = {}
    for raw_story_id, raw_profile in payload.items():
        if not isinstance(raw_story_id, str) or not raw_story_id.strip():
            raise ValueError("Story override keys must be non-empty story id strings")
        story_id = raw_story_id.strip()
        if isinstance(raw_profile, str):
            profile = {"model": raw_profile.strip()}
        elif isinstance(raw_profile, dict):
            model = raw_profile.get("model")
            if not isinstance(model, str) or not model.strip():
                raise ValueError(f"{story_id}: override must include non-empty `model`")
            profile = {"model": model.strip()}
            reasoning = raw_profile.get("reasoningEffort", raw_profile.get("reasoning_effort"))
            if reasoning is not None:
                if not isinstance(reasoning, str) or not reasoning.strip():
                    raise ValueError(f"{story_id}: `reasoningEffort` must be a non-empty string")
                profile["reasoningEffort"] = reasoning.strip()
        else:
            raise ValueError(f"{story_id}: override must be an object or string")

        if not profile.get("model"):
            raise ValueError(f"{story_id}: override `model` cannot be blank")
        overrides[story_id] = profile

    return overrides


def apply_story_model_profiles(
    stories: list[dict],
    default_profile: dict[str, str],
    story_model_overrides: dict[str, dict[str, str]],
) -> None:
    indexed = {
        story.get("id"): story
        for story in stories
        if isinstance(story, dict) and isinstance(story.get("id"), str)
    }
    unknown_story_ids = sorted(story_id for story_id in story_model_overrides if story_id not in indexed)
    if unknown_story_ids:
        raise ValueError(
            "Unknown story ids in --story-model-overrides: " + ", ".join(unknown_story_ids)
        )

    for story in stories:
        story_id = story.get("id")
        if not isinstance(story_id, str):
            continue
        profile = dict(default_profile)
        source = "default"
        override = story_model_overrides.get(story_id)
        if override:
            profile.update(override)
            source = "story_override"
        story["modelProfile"] = {
            "model": profile["model"],
            "reasoningEffort": profile.get("reasoningEffort", ""),
            "source": source,
        }


def build_prd(
    workspace: str,
    purpose: str,
    mode: str,
    base_ref: str,
    read_only: bool,
    model_policy: dict,
    story_model_overrides: dict[str, dict[str, str]],
) -> dict:
    if mode == "audit":
        stories = build_audit_stories(workspace, purpose)
        description = "Audit-focused loop for delegation integrity, xenon safety, and branch diff/LOC reduction."
    else:
        stories = build_delivery_stories(workspace, purpose)
        description = "Implementation loop with one-story-at-a-time delivery and quality gates."

    apply_mutation_policy_to_stories(stories=stories, read_only=read_only)

    default_profile = model_policy["defaultProfile"]
    apply_story_model_profiles(
        stories=stories,
        default_profile=default_profile,
        story_model_overrides=story_model_overrides,
    )

    return {
        "project": f"{workspace} Ralph Loop",
        "branchName": derive_branch_name(base_ref),
        "description": (
            f"{description} Mutation policy: {'read-only' if read_only else 'read-write'}. "
            f"Purpose: {purpose}"
        ),
        "workspaceSettings": {
            "mode": mode,
            "readOnly": read_only,
            "baseRef": base_ref,
            "modelPolicy": model_policy,
        },
        "verificationCommands": {
            "typecheck": "echo 'Ralph loop: capture verification evidence per story output'",
            "lint": "echo 'Ralph loop: capture verification evidence per story output'",
            "test": "echo 'Ralph loop: run focused checks required by story notes'",
        },
        "userStories": stories,
    }


def build_progress(stories: list[dict], purpose: str) -> str:
    lines = [
        "# Ralph Progress Log (Codex)",
        f"Started: TODO",
        f"Purpose: {purpose}",
        "Output: .codex/<workspace>/audit/*.md files",
        "---",
        "",
        "## Checklist",
    ]
    for story in stories:
        lines.append(f"- [ ] {story['id']}: {story['title']}")
    lines.extend(["---", ""])
    return "\n".join(lines)


def build_readme(
    workspace: str,
    purpose: str,
    mode: str,
    base_ref: str,
    read_only: bool,
    model_policy: dict,
) -> str:
    default_profile = model_policy["defaultProfile"]
    fallback_profile = model_policy["fallbackProfile"]
    mutation_label = "read-only" if read_only else "read-write"
    return f"""# Ralph Workspace ({workspace})

Purpose: {purpose}
Mode: {mode}
Base Ref: {base_ref}
Mutation Policy: {mutation_label}
Default Model: {default_profile['model']} ({default_profile['reasoningEffort']})
Fallback Model: {fallback_profile['model']} ({fallback_profile['reasoningEffort']})

This workspace is generated by `ralph-loop-builder`.

## Run

```bash
cd .codex/{workspace}
./ralph.sh 20
```

## Outputs

- Reports: `.codex/{workspace}/audit/*.md`
- State: `.codex/{workspace}/prd.json`, `.codex/{workspace}/progress.txt`
- Logs: `.codex/{workspace}/events.log`, `.codex/{workspace}/run.log`
"""


def build_codex_md(
    workspace: str,
    purpose: str,
    base_ref: str,
    mode: str,
    read_only: bool,
    model_policy: dict,
) -> str:
    mutation_guardrail = (
        "DO NOT APPLY CODE CHANGES. Read-only evidence and decision-quality output only."
        if read_only
        else "Implement exactly one story per cycle and keep verification evidence explicit."
    )
    default_profile = model_policy["defaultProfile"]
    fallback_profile = model_policy["fallbackProfile"]
    if mode == "audit":
        return f"""# Ralph Audit Agent Instructions (OpenAI Codex)

## Workspace Context

- Workspace: `.codex/{workspace}`
- Purpose: {purpose}
- Base Ref: `{base_ref}`
- Mode: `{mode}`
- Mutation Policy: `read-only`
- Default profile: `{default_profile['model']}` with `{default_profile['reasoningEffort']}`
- Fallback profile: `{fallback_profile['model']}` with `{fallback_profile['reasoningEffort']}`

---

## Safety Notice (Customize)

If this codebase is production, handles money, or touches sensitive data: treat this audit loop as high-risk.
Run with least privilege, avoid exporting long-lived credentials in shell, and keep this agent in read-only mode.

---

You are an autonomous CODE AUDITOR. Your ONLY job is to find problems and document them.
You DO NOT fix anything.

## Web Research Policy (Use When Appropriate)

This repository may depend on fast-moving tools and specs. Use web research selectively to avoid outdated assumptions.

1. Use web research when validating claims about:
- Next.js / React / Tailwind / Vercel / Netlify behavior or deprecations (especially 2025-2026 changes)
- MCP spec / OpenClaw / other agent frameworks
- Third-party integrations and webhooks (Stripe, Coinbase Commerce, ProxyPics, etc.)
- Any library/API surface likely changed since 2024
2. Do not use web research for timeless basics (JSON, HTTP fundamentals, TypeScript syntax, etc.).
3. Prefer primary sources (official docs, upstream GitHub repos/releases).
4. Validate against the exact version used in this repository first (`package.json`, lockfiles, configs).
5. If web research supports a finding, append **External References** with:
- URL
- Date accessed (use today's runner date)

## Critical Rules

1. **DO NOT FIX ANYTHING** - No code changes, no edits, no patches.
2. **DO NOT PLAN FIXES** - Do not suggest implementation approaches.
3. **DO NOT SKIP SCOPE FILES** - Read every file in the active story scope.
4. **BE DETAILED** - Include file paths, line numbers, code snippets, and severity.

## Your Task

1. Read the PRD at `.codex/{workspace}/prd.json`
2. Pick the highest priority story where `passes: false` (or use the runner-provided story id)
3. Read every file in the selected story scope
4. Scan each file line-by-line for all required issue categories
5. Output the full markdown report content for `.codex/{workspace}/audit/XX-name.md`
6. Do not modify any repository file
7. End turn after one task report

## Allowed Changes (Strict)

Do not modify any files in this repository. Output only.

## What To Look For (Every Task)

### broken-logic
- Code that does not do what it claims to do
- Conditions that are always true or always false
- Functions returning incorrect values
- Off-by-one errors
- Null/undefined not handled
- Race conditions
- Infinite loop risks
- Dead code paths that can never execute

### unfinished
- TODO/FIXME/HACK/XXX comments
- Placeholder early returns
- `throw new Error('not implemented')`
- Empty function bodies
- Commented-out code blocks
- Debug `console.log` left in
- Features claimed in comments but not implemented

### slop
- Copy-paste duplication
- Magic numbers without context
- Unclear names
- Overlong functions (roughly >50 lines)
- Deep nesting (>3 levels)
- Mixed concerns in one function
- Inconsistent patterns vs rest of codebase
- Unused imports/variables/parameters

### dead-end
- Functions defined but never called
- Files never imported
- Components never rendered
- API routes disconnected from call paths
- Types/interfaces never referenced
- Exports with no consumers

### stub
- Hardcoded/mock return data in runtime paths
- API routes returning fake responses
- Placeholder UI content
- Lorem ipsum/sample text left in
- `TODO: implement` with no implementation

### will-break
- Missing async error handling
- Missing try/catch around failing operations
- Missing input validation
- Missing auth checks on protected paths
- Promises without error handling
- Side effects without cleanup
- Memory leak patterns
- State sync hazards

### Comments and JSDoc (Signal, not truth)

- Use comments/JSDoc as intent clues.
- If comments/JSDoc and implementation disagree, record it as a finding.
- Treat runtime behavior as source of truth.

## Output Format

Write report markdown using this structure:

````markdown
```markdown
# [Audit Name] Findings

Audit Date: [timestamp]
Files Examined: [count]
Total Findings: [count]

## Summary by Severity
- Critical: X
- High: X
- Medium: X
- Low: X

---

## Findings

### [SEVERITY] Finding #1: [Short description]

**File:** `path/to/file.ts`
**Lines:** 42-48
**Category:** [broken-logic | unfinished | slop | dead-end | stub | will-break]

**Description:**
[Detailed explanation]

**Code:**
```typescript
// problematic snippet
```

**Why this matters:**
[Impact/risk]
```
````

## Severity Levels

- **CRITICAL**: Will definitely break in production, data loss risk, or security risk
- **HIGH**: Likely bug or major behavior break
- **MEDIUM**: Potential issue, incomplete behavior, or inconsistency
- **LOW**: Code smell or minor debt

## Stop Condition

After documenting all findings for one task:
1. End response
2. Wait for next iteration

If explicitly asked for final completion signal:

```xml
<promise>COMPLETE</promise>
```

## Important Reminders

- No fixes
- No fix plans
- No skipped files in scope
- Include code snippets for every finding
- Include exact line numbers for every finding
- When uncertain, document with evidence
"""
    return f"""# Ralph Instructions ({workspace})

You are an autonomous Ralph operator for this workspace.

## Objective

{purpose}

## Mutation Policy

- Read-only: {str(read_only).lower()}
- Rule: {mutation_guardrail}

## Model Routing

- Default profile: `{default_profile['model']}` with `{default_profile['reasoningEffort']}`
- Fallback profile: `{fallback_profile['model']}` with `{fallback_profile['reasoningEffort']}`
- Story-level override: use `userStories[].modelProfile` from `prd.json` when present.

## Core Rules

1. {mutation_guardrail}
2. Evidence before claims.
3. Keep base ref explicit as `{base_ref}` when reporting diff metrics.
4. Keep xenon state non-regressive across cycles.
5. Keep non-test LOC trend explicit and prefer net reduction.

## Gate Bundle

```bash
uv run ruff check src tests
uv run radon cc src -s -n C
uv run xenon --max-absolute B --max-modules A --max-average A src
python "$CODEX_HOME/skills/code-health/scripts/diff_summary_compact.py" --base {base_ref}
```
"""


def copy_runner(template_dir: Path, target_dir: Path, max_iterations: int) -> None:
    source = template_dir / "ralph.sh"
    destination = target_dir / "ralph.sh"
    if source.exists():
        shutil.copy2(source, destination)
        text = destination.read_text(encoding="utf-8")
        text = re.sub(r"MAX_ITERATIONS=\d+", f"MAX_ITERATIONS={max_iterations}", text, count=1)
        destination.write_text(text, encoding="utf-8")
        destination.chmod(0o755)
        return

    destination.write_text(
        "#!/bin/bash\n"
        "set -euo pipefail\n"
        "echo \"No template ralph.sh found. Copy runner from an existing Ralph workspace first.\"\n"
        "exit 1\n",
        encoding="utf-8",
    )
    destination.chmod(0o755)


def ensure_target_dir(target: Path, force: bool) -> None:
    if target.exists() and any(target.iterdir()) and not force:
        raise FileExistsError(f"Target already exists and is not empty: {target}. Use --force to overwrite.")
    target.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bootstrap a Ralph workspace under .codex/")
    parser.add_argument("--repo-root", default=".", help="Repository root path")
    parser.add_argument("--workspace", required=True, help="Workspace folder name under .codex/")
    parser.add_argument("--purpose", required=True, help="One-line objective for this Ralph loop")
    parser.add_argument("--mode", choices=("audit", "delivery"), default="audit")
    parser.add_argument("--base-ref", default="origin/main")
    parser.add_argument("--template", default=".codex/ralph-audit", help="Template workspace path")
    parser.add_argument("--max-iterations", type=int, default=20)
    mutation_group = parser.add_mutually_exclusive_group()
    mutation_group.add_argument(
        "--read-only",
        dest="read_only",
        action="store_true",
        help="Force read-only workspace policy",
    )
    mutation_group.add_argument(
        "--allow-write",
        dest="read_only",
        action="store_false",
        help="Force read-write workspace policy",
    )
    parser.set_defaults(read_only=None)
    parser.add_argument("--review-model", default=DEFAULT_REVIEW_MODEL)
    parser.add_argument("--review-reasoning-effort", default=DEFAULT_REVIEW_REASONING)
    parser.add_argument("--fix-model", default=DEFAULT_FIX_MODEL)
    parser.add_argument("--fix-reasoning-effort", default=DEFAULT_FIX_REASONING)
    parser.add_argument(
        "--story-model-overrides",
        default="",
        help="JSON object or JSON file path mapping story ids to model profiles",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite target workspace files if needed")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    workspace = slugify(args.workspace)
    if not workspace:
        print("workspace must contain at least one alphanumeric character", file=sys.stderr)
        return 1

    template_dir = (repo_root / args.template).resolve()
    target_dir = repo_root / ".codex" / workspace
    audit_dir = target_dir / "audit"

    try:
        ensure_target_dir(target_dir, force=args.force)
    except FileExistsError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    read_only = args.read_only if args.read_only is not None else args.mode == "audit"

    try:
        story_model_overrides = parse_story_model_overrides(args.story_model_overrides)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    try:
        model_policy = build_model_policy(
            read_only=read_only,
            review_model=args.review_model,
            review_reasoning_effort=args.review_reasoning_effort,
            fix_model=args.fix_model,
            fix_reasoning_effort=args.fix_reasoning_effort,
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    audit_dir.mkdir(parents=True, exist_ok=True)

    try:
        prd_payload = build_prd(
            workspace=workspace,
            purpose=args.purpose,
            mode=args.mode,
            base_ref=args.base_ref,
            read_only=read_only,
            model_policy=model_policy,
            story_model_overrides=story_model_overrides,
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    progress_text = build_progress(prd_payload["userStories"], args.purpose)
    readme_text = build_readme(
        workspace=workspace,
        purpose=args.purpose,
        mode=args.mode,
        base_ref=args.base_ref,
        read_only=read_only,
        model_policy=model_policy,
    )
    codex_text = build_codex_md(
        workspace=workspace,
        purpose=args.purpose,
        base_ref=args.base_ref,
        mode=args.mode,
        read_only=read_only,
        model_policy=model_policy,
    )

    write_json(target_dir / "prd.json", prd_payload)
    (target_dir / "progress.txt").write_text(progress_text, encoding="utf-8")
    (target_dir / "README.md").write_text(readme_text, encoding="utf-8")
    (target_dir / "CODEX.md").write_text(codex_text, encoding="utf-8")
    copy_runner(template_dir=template_dir, target_dir=target_dir, max_iterations=args.max_iterations)

    for log_name in ("events.log", "run.log"):
        (target_dir / log_name).write_text("", encoding="utf-8")

    print(f"[OK] Created workspace: {target_dir}")
    print(f"[OK] Stories: {len(prd_payload['userStories'])} ({args.mode})")
    print(f"[OK] Base ref: {args.base_ref}")
    default_profile = model_policy["defaultProfile"]
    print(f"[OK] Read-only: {str(read_only).lower()}")
    print(f"[OK] Default model: {default_profile['model']} ({default_profile['reasoningEffort']})")
    if story_model_overrides:
        print(f"[OK] Story model overrides: {len(story_model_overrides)}")
    print(f"[NEXT] cd {target_dir} && ./ralph.sh {args.max_iterations}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
