---
name: paperbanana-cli
description: Run the local PaperBanana installation to generate methodology diagrams, generate statistical plots, and evaluate generated diagrams from any workspace. Use when the user asks for PaperBanana `generate`, `plot`, `evaluate`, NeurIPS-style academic figure generation from text/data, or comparative diagram quality scoring against a human reference.
---

# PaperBanana CLI

## Overview

Execute PaperBanana commands without requiring the current working directory to be `~/project/paperbanana`.
Use this skill as the default operational path for PaperBanana tasks in Codex.

## Workflow

```text
Request -> Preflight -> Route Task -> Run CLI -> Return Output Path + Next Action
```

1. Run preflight checks:
   - `bash scripts/run_paperbanana.sh --help`
   - Confirm `GOOGLE_API_KEY` is available in env or `.env`.
2. Route by intent:
   - Methodology diagram: run **Diagram Eligibility Gate** first, then use `generate` only if it passes.
   - Statistical plot: use `plot`.
   - Comparative scoring: use `evaluate`.
3. Execute through the wrapper script:
   - `bash scripts/run_paperbanana.sh <subcommand> ...`
   - For `generate`, prefer stable wrapper: `bash scripts/generate_with_stable_output.sh ...`
4. Report:
   - Exact command used.
   - Output file path (`--output` if provided, otherwise PaperBanana auto path).
   - Any validation caveats (missing caption/context/reference).

## No Dummy Runs Policy (MANDATORY)

Do not run dummy/smoke generation that creates throwaway artifacts.

1. Allowed preflight:
   - `bash scripts/run_paperbanana.sh --help`
   - Environment checks only (`GOOGLE_API_KEY`, paths).
2. Disallowed:
   - Any synthetic `generate` call only for tool health check.
   - Any placeholder diagram output not requested by user.
3. Execution rule:
   - Run `generate` only when real user target exists (real source text + intended output path).
   - If blocked, report blocker instead of producing a dummy output.

## Diagram Eligibility Gate (MANDATORY)

Apply this gate before any `generate` call.

1. Hard no-go (do **not** diagramize):
   - Table-of-contents order, reading order, onboarding order.
   - Simple numbered checklists without branching.
   - Single linear sequence that adds no spatial/causal insight.
   - Plain schema/type listings and code-like pseudo-structures.
2. Borderline threshold:
   - Generate only when at least **2** complexity signals are present:
     - Branching decisions (if/else paths).
     - Feedback loop or cyclic dependency.
     - Multi-actor handoff across 3+ components.
     - Spatial state mapping (grid/stack/before-after occupancy).
3. Default behavior for ambiguous cases:
   - Prefer keeping existing text/ASCII.
   - Report skipped conversion with one-line reason: `below diagram threshold`.

## Source Text Authoring Rules (MANDATORY)

PaperBanana renders source text into visual diagrams. Text-heavy source = text-heavy diagram. The source must describe **visual topology**, not technical specifications.

### Anti-Text-Wall Rules

1. **Box labels: 2~5 words max.**
   - Good: `P0 Masking`, `Binder 4-Stage`, `SPP Execution`
   - Bad: `P0 Action Masking: Overstow prevention (intra-block vertical order); Cross-zone HOLD/DECK restow prevention; PBS/Block Stowage DG zone masks`
2. **No code, variable names, or formulas inside boxes.**
   - Good: `Resistance Update`
   - Bad: `resistance[l] += alpha * resistance_delta[l]`
3. **No multi-line descriptions inside nodes.**
   - Each node = one short label. Supplementary text goes to edge labels or a small legend, not inside the box.
4. **Edge labels: max 3 words.**
   - Good: `feedback`, `per block`, `eval only`
   - Bad: `SPP rejection stats -> resistance_delta[block] updated -> affects next step P0/P1/P2`
5. **Focus on TOPOLOGY (nodes + edges + flow direction), not CONTENT.**
   - Source text defines: what boxes exist, how they connect, what the visual layout is.
   - Source text does NOT define: implementation details, data schemas, algorithms.

### Source Text Structure Template

```text
<Title of Diagram>

NODES (short labels only):
  Node1, Node2, Node3, ...

FLOW:
  Node1 -> Node2 -> Node3
  Node3 -> Node4 [label: "eval only"]
  Node4 --feedback--> Node1

LAYOUT HINTS:
  - Top-to-bottom / Left-to-right
  - Group {Node1, Node2} as "Phase A"
  - Highlight Node3 (decision point)

VISUAL REQUIREMENTS:
  - Use color grouping for phases
  - Dashed arrows for optional/eval-only paths
  - Bold arrows for main flow
```

### Context/Caption Anti-Text-Wall Directive

Always include this phrase in the `--caption` or `-c` argument:

> **"Schematic diagram with SHORT labels (2-5 words per box). No paragraphs or code inside boxes. Focus on flow topology."**

This overrides PaperBanana's tendency to reproduce all source text verbatim.

## Graph vs ASCII Policy (MANDATORY)

1. Keep graph diagrams as Mermaid:
   - If the source is a true graph (flowchart, dependency graph, decision graph), keep or author it in Mermaid first.
   - Do not replace Mermaid graph sources with PaperBanana-only artifacts by default.
2. Prioritize PaperBanana for non-graph or geometry-heavy ASCII:
   - Use PaperBanana primarily when the source diagram is not a graph, or when ASCII geometry is too complex to maintain/read.
   - Typical targets: layered spatial layouts, dense occupancy maps, and complex geometric schematics.
3. Conversion boundary:
   - If a Mermaid graph already communicates clearly, skip PaperBanana conversion unless the user explicitly requests publication-grade rendering.

## Task Commands

### Generate Diagram

```bash
bash scripts/generate_with_stable_output.sh \
  --input <method_txt> \
  --caption "<figure_caption>" \
  --output <target.png> \
  --iterations 3
```

### Generate Plot

```bash
bash scripts/run_paperbanana.sh plot \
  --data <data.csv|data.json> \
  --intent "<visual_intent>" \
  --iterations 3
```

### Evaluate Diagram

```bash
bash scripts/run_paperbanana.sh evaluate \
  --generated <generated.png> \
  --reference <human_reference.png> \
  --context <method_txt> \
  --caption "<figure_caption>"
```

## Log-Guided Refinement Loop (MANDATORY when iterating)

When generation requires retries, read run logs and promote critic feedback into explicit hard constraints.

1. Mine critic output across all iterations:
   - `find <output_dir>/run_* -path '*/iter_*/details.json' -print0 | xargs -0 jq -r '.critique.critic_suggestions[]? // empty'`
2. Cluster recurring failures:
   - Endpoint mismatch (`A -> B` wrong target).
   - Arrow style/color mismatch (solid/dashed, black/grey/red, thickness).
   - Loop timing mismatch (`validate` once vs every loop).
   - Matrix/table omissions (missing rows/groups, wrong legend, wrong `—` cells).
3. Rewrite source text with `MUST` constraints only (no vague language).
4. Regenerate to the same `--output` path and recheck logs.
5. Accept only if latest critic suggestions are empty and visual spot-check confirms key constraints.

## Prompt Hardening Checklist (for diagram generation)

Use this checklist whenever previous runs required more than one revision.

1. Edge contract:
   - Enumerate every critical edge explicitly as `SOURCE -> TARGET`.
   - Declare forbidden alternatives: `DO NOT connect to background/group container`.
2. Style contract:
   - Fix arrow style per edge class (main flow, branch, feedback, bypass).
   - Use exact style words (`solid`, `dashed`, `thin`, `bold`) and exact color names; avoid synonyms.
3. Loop contract:
   - Specify loop granularity in plain logic (e.g., `validate_plan(FULL) exactly once after all blocks/containers`).
   - State which arrows represent loop-back vs normal forward flow.
4. Table/matrix contract:
   - Provide full row-group and row list with exact ordering.
   - Provide complete cell-state map (`full`, `approx`, `indirect`, `—`) for every row/column.
   - Explicitly include legend policy (keep or remove) to avoid oscillation.

## Critic Conflict Arbitration (MANDATORY)

Critic feedback can conflict across iterations. Resolve with deterministic priority:

1. Source truth first:
   - If critic feedback contradicts the source method text, keep source truth and reject critic request.
2. Semantics over cosmetics:
   - Prioritize node identity, edge endpoints, loop timing, and table values over font/style micro-adjustments.
3. Freeze decisions:
   - When a property oscillates (for example rectangle vs rounded rectangle), pin one canonical value in source text with `MUST` and `MUST NOT`.
4. Stop condition:
   - If remaining critic issues are cosmetic-only and semantic checks pass, mark as acceptable with caveat.

## Endpoint Precision Protocol (for bypass/feedback-heavy graphs)

When repeated failures mention "connect to border/background":

1. Add explicit anchor constraints:
   - `Arrow MUST terminate on <node> border (not center, not group background).`
2. Add anti-target constraints:
   - `Arrow MUST NOT terminate on band/subgraph container.`
3. Reduce ambiguous crossings:
   - Require orthogonal routing around nodes so arrows do not appear to point to adjacent nodes.
4. Keep bypass labels near origin:
   - Place bypass labels close to source node to avoid critic drift on readability.

## Matrix Determinism Mode (for table diagrams)

For constraint matrices, enforce data-first rendering:

1. Encode each cell with both color and token (`F/A/I/—`) to prevent color-only drift.
2. Provide exact row count and exact row order.
3. Ban duplicate row labels explicitly (`must appear once only`).
4. Add row-group membership assertions per row (which group owns the row).
5. Reject output if any row/group mismatch is found, even when critic reports no issues.

## High-Risk Patterns from Real Runs (2026-02-09)

Observed repeated failure classes in iterative runs:

- Arrow endpoint drift (edge points to nearby region instead of target node).
- Arrow style drift (correct node mapping but wrong dashed/solid, color, or thickness).
- Feedback/loop semantic drift (wrong source node or wrong loop timing semantics).
- Constraint matrix drift (missing row groups, duplicated/omitted rows, mismatched `—` cells).

Mitigation: convert each failure into a literal `MUST` statement in the next prompt, then re-run.

## Post-Generation Verification (MANDATORY)

After every `generate` call, **read the output image** and verify against source text spec:
1. All specified edges exist and no forbidden edges appear.
2. Colors match spec (do not rely on PaperBanana critic alone).
3. Layout constraints are met (band positions, routing, anchoring).
4. If verification fails, identify best iteration from `run_<id>/diagram_iter_*.png` and copy that instead of `final_output.png`.

## Iteration Selection Policy

PaperBanana's critic may not select the best iteration. When the final output still has issues:
1. Read ALL iteration images (`diagram_iter_1.png`, `diagram_iter_2.png`, `diagram_iter_3.png`).
2. Select the iteration that best satisfies the source text spec.
3. Copy that specific iteration to the target path.

## Known Failure Patterns and Mitigations

### Cross-Band Routing (bypass / skip connections)

**Problem**: When dashed lines must cross from one horizontal band to another (e.g., Preprocess → SPP skipping MPP), PaperBanana's image generator routes them through the intermediate band interior, violating no-touch constraints on intermediate nodes (e.g., P0/P1/P2).

**Mitigation**: In source text AND caption, provide **explicit spatial routing geometry**:
- Specify FAR-LEFT MARGIN or FAR-RIGHT MARGIN routing.
- Name exactly which side each bypass line must use.
- State "completely OUTSIDE the [band name] band interior".
- Add "Leave generous whitespace margins on both sides for bypass routing" to LAYOUT section.

Example caption reinforcement:
> "Bypass A routes down the FAR-RIGHT margin, completely OUTSIDE the MPP band. Bypass C routes down the FAR-LEFT margin."

### Color Fidelity

**Problem**: PaperBanana often renders specified dashed line colors as gray instead of the requested color (blue, green, red).

**Mitigation**:
- Include hex color codes in source text: `A=bright blue (#2196F3)`.
- Repeat color requirements in QUALITY GATE section.
- In caption: explicitly state "Bypass A MUST be blue, NOT gray".

### Missing Edges

**Problem**: Edges connecting nodes across different bands (e.g., MaterializedPool → inventory_slice) are frequently dropped during generation.

**Mitigation**:
- In source text LAYOUT section, describe the cross-band edge explicitly: "MaterializedPool → inventory_slice is a VERTICAL arrow going straight down from Preprocess band to MPP band."
- Add the edge to QUALITY GATE checklist.

### Endpoint Precision

**Problem**: Dashed lines terminate on band backgrounds instead of specific box borders.

**Mitigation**:
- In source text, add explicit ENDPOINT ANCHOR RULES section.
- In caption: "All bypass arrows terminate ON the [target box] box border, not on background."

## Input Contract

- `generate`:
  - Required: method text file, caption.
  - Optional: `--output`, `--iterations`.
- `plot`:
  - Required: CSV/JSON data file, intent.
  - Optional: `--output`, `--iterations`.
- `evaluate`:
  - Required: generated image, reference image, method context file, caption.

## Troubleshooting

1. `paperbanana: command not found`
   - Wrapper automatically falls back to `uv run --project /Users/mrx-ksjung/project/paperbanana`.
2. Auth/provider failure
   - Verify `GOOGLE_API_KEY` and rerun `paperbanana setup` if needed.
3. Wrong output location
   - Pass `--output` explicitly.
4. Need detailed flags
   - Read `references/usage.md`.

## Resources

- `scripts/run_paperbanana.sh`: stable CLI entrypoint with fallback behavior.
- `scripts/generate_with_stable_output.sh`: generate wrapper that resolves actual output path and writes deterministically to target file.
- `references/usage.md`: verified command/flag reference aligned with the local install at `/Users/mrx-ksjung/project/paperbanana`.
