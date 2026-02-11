---
name: skill-topology-adjuster
description: Continuously reconcile Codex skill topology so all installed skills are structured and delegation to specialized skills stays consistent. Use when a skill is created/updated/removed, when topology drift is suspected, or when role classification (`specialist`, `orchestrator`, `specialist-orchestrator`, `meta`, `meta-orchestrator`, `utility`, `meta-tool`) and delegation edges must be corrected in real time.
---

# Skill Topology Adjuster

## Objective

Keep the skill graph coherent.
Assign a single owner per responsibility and enforce shallow delegation (`orchestrator -> specialist`) unless the topology explicitly allows one composed handoff.
Detect topology drift across all installed skills and apply minimal corrective edits immediately.

## Inputs

- Installed skills root path (default: `$CODEX_HOME/skills`)
- Target skill name and path
- Target skill responsibilities (from request + SKILL.md)
- Current topology document (default: `skill-topology-adjuster/references/skill_topology.md`)
- Existing delegation edges touching the target skill
- Specialist-identity erosion signals (whether one skill weakens another skill's specialist ownership)
- Change context (new/updated/removed skills, or explicit drift-check request)

## Workflow

1. Enumerate all installed skills under `$CODEX_HOME/skills`, including hidden namespaces (for example `.system`).
   - If using `rg`, prefer `rg --files -uu "$CODEX_HOME/skills" -g 'SKILL.md'` so hidden directories are not skipped.
2. Read every discovered `SKILL.md` once to build a full inventory.
3. Normalize inventory into a topology view:
   - skill name
   - role candidate
   - owned responsibilities
   - declared delegation targets
   - delegation evidence in context (explicit skill references and delegation/handoff wording)
   - responsibility-evidence snippets from each SKILL body (`Objective`/`Purpose`/`Workflow`/trigger sections)
4. Read `skill-topology-adjuster/references/skill_topology.md`.
5. Run consistency checks across all skills:
   - every installed skill appears in role map
   - role map/layers/graph/tree stay synchronized
   - every runtime edge declared in Delegation Graph also appears in Delegation Tree
   - delegation targets exist and reflect specialization boundaries
   - `codex-exec-sub-agent` is explicitly represented as reusable by any skill role
   - for every graph-declared `source -> target` edge between installed skills, the source skill `SKILL.md` must contain an explicit reference to the target skill
   - for every graph-declared `skill -> codex-exec-sub-agent` preferred edge, that source skill `SKILL.md` must also contain scenario-bound `codex-exec-sub-agent` delegation guidance
   - sub-agent preferred activators are explicitly documented in hierarchy/scenario form for high-cost scans (for example grep/search-heavy, O(N^2) parity checks, large log forensics)
   - orchestrators delegate specialist internals instead of duplicating them
   - detect specialist-identity erosion: if skill A's guidance makes skill B lose specialist ownership (A absorbs B's specialist internals instead of delegating), mark drift
   - for each erosion candidate pair (A, B), confirm whether A claims direct ownership/execution of B-owned specialist workflow; if yes and no explicit delegation boundary exists, mark `needs-fix`
   - delegation depth stays one hop unless explicitly allowed
   - detect responsibility-overlap candidates across skills by directly reading SKILL text, then check explicit delegation/reference exists between the pair
   - every skill has a per-skill audit status (`pass`/`needs-fix`) with reason
   - apply strict role checks:
     - `orchestrator`, `specialist-orchestrator`, or `meta-orchestrator`: require explicit cross-skill references and delegation/handoff wording
     - `meta`: require explicit delegation signal or explicit standalone note (`standalone`, `delegation optional`)
     - `specialist`/`utility`/`meta-tool`: no mandatory delegation, but must not claim foreign ownership
6. For the target skill, classify role as exactly one: `specialist`, `orchestrator`, `specialist-orchestrator`, `meta`, `meta-orchestrator`, `utility`, `meta-tool`.
7. Define ownership boundaries:
   - Owned here (what this skill owns)
   - Delegated out (which existing skill must own the rest)
8. Define delegation edges and keep them one-hop deep by default.
9. Reject design if it duplicates an existing specialist workflow instead of delegating.
10. Apply real-time corrective edits when drift exists:
   - update topology artifacts in one change:
   - Role map table
   - Orchestration layers
   - Sub-agent activation scenario catalog (when changed)
   - Delegation graph (Mermaid)
   - Delegation tree (Mermaid)
   - update affected skill instructions only for ownership/delegation wording when needed
11. Return a compact handoff note for the caller skill with:
   - scanned skill count and scanned skill names
   - final role
   - detected drift items and applied fixes
   - per-skill audit summary (each skill: pass/needs-fix + reason)
   - specialist-identity erosion findings (none or pairwise A -> B with reason)
   - ownership/delegation bullets
   - exact files changed

## Direct Read Requirement (LLM)

- Do not decide overlap/delegation only from role labels or script summary.
- For every overlap candidate, open both SKILL files and compare their responsibility text directly.
- Use evidence from actual SKILL body wording (Objective/Purpose/Workflow/trigger language) before marking `needs-fix`.
- If overlap is real and there is no explicit delegation/reference edge, mark both sides `needs-fix` and propose the minimum boundary/delegation edit.
- For specialist-identity erosion, read both SKILL files and verify whether non-owning skill text claims specialist internals that should remain owned by the specialist skill.
- If erosion is real, mark the eroding skill `needs-fix` (and mark the eroded specialist `needs-fix` if its boundary text became ambiguous), then propose the smallest ownership/delegation wording fix.

## Specialist Identity Erosion Check

Treat the following as explicit topology drift candidates:

- A non-specialist skill claims it can directly run or redefine specialist internals that belong to another installed specialist skill.
- A specialist-orchestrator or orchestrator keeps a copied specialist checklist instead of delegating to the specialist owner.
- A utility/meta skill expands into cross-domain implementation ownership that causes specialist skills to lose clear ownership boundaries.

Default correction policy:

1. Restore specialist ownership wording in the specialist skill.
2. Remove copied internals from non-owning skills.
3. Replace copied internals with explicit delegation to the specialist owner.

## Real-Time Adjustment Loop

Run this skill on every skill create/update/remove event and on explicit topology check requests.
If no drift is found, return a no-op handoff with evidence.

## Dual Verification Standard

When requests require high-assurance topology validation (for example O(N^2) edge parity checks), run two independent passes:

1. Sub-agent pass (`codex-exec-sub-agent`) in fresh context.
2. Local pass (current agent) with the same parity/meta-tool checks.
3. Compare outcomes and stop on any disagreement until reconciled.

Standardize this evidence set in both passes:

- graph/tree edge parity over installed skill pairs
- graph-only and tree-only edge sets
- explicit `codex-exec-sub-agent` universal-access proof (`ANY -> CESA` semantics)
- strict auditor result (`scripts/audit_topology.py --json`)

If the sub-agent cannot write a requested report file (read-only or permission errors), require inline report fallback and keep the JSONL run path as evidence.

## Sub-Agent Preferred Activation Policy

When keeping topology current, maintain an explicit "preferred activator" lane for `codex-exec-sub-agent` in the topology hierarchy.

Minimum scenario coverage:

- grep/search-heavy discovery where retries are likely (`grepai-deep-analysis` and related orchestrators)
- strict parity/overlap validation that benefits from independent fresh-context confirmation (`skill-topology-adjuster`)
- long-running forensic collection (`gh-fix-ci`, large logs) or broad retrospective evidence scans (`session-wrap-up`)

Policy constraints:

- keep these edges optional and scenario-bound; they do not replace primary ownership/delegation
- if a preferred activator is added in graph, mirror it in tree in the same change
- keep rationale documented in the topology scenario catalog

## Scripts

Use `scripts/audit_topology.py` as the default strict auditor.
Treat the script as candidate generation plus baseline checks; final overlap judgment must be validated by direct SKILL text reading.
If `--json` is rejected, rerun without the flag and parse the text output.

```bash
python3 scripts/audit_topology.py
python3 scripts/audit_topology.py --json
```

Exit code contract:
- `0`: no `needs-fix`
- `1`: one or more `needs-fix` items found
- `2`: audit execution error (for example, no `SKILL.md` found)

## Delegation Contract

When called by `skill-creator`, treat this skill as the owner of topology adjustment.
Do not ask the caller to re-derive role/edge logic after handoff; return final topology decisions ready to apply.

## Guardrails

- Keep scope to topology and orchestration boundaries only.
- Do not rewrite specialist internals.
- Do not skip full installed-skill scan; topology decisions are invalid without it.
- Do not rely on default file globs that skip hidden directories; include hidden skill namespaces in full scans.
- Keep delegation chains short and explicit.
- Prefer minimal diffs to existing topology docs.
- Apply smallest safe correction set; avoid speculative refactors.
- Never silently whitelist exceptions; encode exceptions in the skill text and report them.

## Validation

Run:

```bash
python3 scripts/audit_topology.py
python3 scripts/audit_topology.py --json
uv run --with pyyaml /Users/mrx-ksjung/.codex/skills/.system/skill-creator/scripts/quick_validate.py <path/to/skill-folder>
```

Quick validation guardrail:
- Run `quick_validate.py` once.
- If yaml import fails, rerun validation only via `uv run --with pyyaml` (do not switch to plain `python`).
- If it fails, rerun once with the same `uv run --with pyyaml` command.
- If it fails twice, stop and report without further edits.
- Before writing topology artifacts, verify destination parent directory is writable with `test -w`; if not writable, fallback to repo root or `$CODEX_HOME`, otherwise stop and report.

If topology changed, verify role map + graph + tree are synchronized in `skill-topology-adjuster/references/skill_topology.md`.
