# Skill Topology

## Purpose

Define ownership and delegation boundaries across currently installed skills so specialist procedures live in one place and orchestrators stay thin.

## Ownership Rules

1. Keep specialist protocols in specialist skills.
2. Keep orchestration skills focused on sequence, gating, and output contracts.
3. Delegate by skill name; do not duplicate another skill's low-level checklist.
4. Keep delegation shallow by default: orchestrator -> specialist.
5. Allow one composed handoff only through designated `specialist-orchestrator` nodes when it replaces duplicated internals.

## Role Definitions

- `meta`: owns cross-skill creation or installation policy; either delegates explicitly or states that delegation is optional.
- `utility`: reusable helper skill with a narrow operational responsibility and no ownership over foreign specialist internals.
- `specialist`: single-domain owner for one workflow or tool surface.
- `specialist-orchestrator`: owns a domain workflow plus one composed handoff to specialists inside that domain.
- `orchestrator`: owns multi-skill delivery flow and delegates domain internals outward.
- `meta-tool`: cross-cutting execution surface that can be reused by any skill role without becoming an installed ownership node.

## Role Map

| Skill | Role | Primary Ownership |
| --- | --- | --- |
| `skill-creator` | meta | skill structure/content workflow and validation handoff rules |
| `skill-installer` | meta | curated or repo-backed skill installation flow |
| `skill-topology-adjuster` | utility | topology role classification, ownership boundaries, and delegation graph updates |
| `find-skills` | utility | discover installable skills and recommend install paths |
| `automation-creator` | utility | Codex automation directive authoring |
| `omx-workspace-prune` | utility | safe `.omx` workspace pruning and retention policy |
| `agents-md-builder` | specialist | AGENTS.md authoring and repo-specific instruction synthesis |
| `branch-onboarding-brief` | specialist | branch diff onboarding and briefing |
| `code-health` | specialist | code-health pipeline and risk summary |
| `desloppify` | specialist | desloppify scanner-driven debt reduction workflow |
| `doc` | specialist | DOCX editing and conversion workflow |
| `doc-separator` | specialist | mixed-document Tobe/As-Is separation |
| `docs-codebase-alignment-audit` | specialist | deterministic docs/codebase alignment audit and minimal-diff fixes |
| `gh-address-comments` | specialist | PR comment retrieval and response workflow |
| `gh-fix-ci` | specialist | GitHub Actions failure triage and fix gating |
| `interface-design` | specialist | intentional interface design workflow for app/product UI tasks |
| `jupyter-notebook` | specialist | notebook scaffold/edit workflow |
| `layer-boundary-test-scaffold` | specialist | scaffold and extend AST-based architecture boundary tests |
| `no-deep-flag-review` | specialist | review deep flag-passing violations and minimal fix direction |
| `pdf` | specialist | PDF rendering and visual QA |
| `reverse-doc` | specialist | code-to-As-Is documentation workflow |
| `screenshot` | specialist | OS-level screenshot capture |
| `slides` | specialist | artifact-tool presentation authoring workflow |
| `spec-diff` | specialist | Tobe/As-Is drift comparison workflow |
| `spreadsheet` | specialist | Python/openpyxl spreadsheet modeling and editing workflow |
| `spreadsheets` | specialist | artifact-tool workbook authoring workflow |
| `yeet` | specialist | explicit stage/commit/push/PR one-shot workflow |
| `grepai-deep-analysis` | specialist-orchestrator | deep code analysis protocol with bounded augmentation handoff |
| `refresh-branch-docs` | specialist-orchestrator | doc impact mapping and branch-grounded doc rewrite |
| `non-test-bloat-reduction` | specialist-orchestrator | per-commit non-test intent compression and bloat reduction |
| `branch-health-remediation-workflow` | orchestrator | branch onboarding + health + grepai remediation synthesis |
| `complexity-loc-balancer` | orchestrator | complexity reduction with non-test net growth guardrail |
| `main-merge` | orchestrator | merge sequence and conflict/doc handoff |
| `pr-workflow` | orchestrator | PR briefing/creation flow and release gating |
| `session-wrap-up` | orchestrator | session-end insight synthesis and skill/topology handoff |

## Orchestration Layers

```text
Layer 0: Meta / Utility
  skill-creator, skill-installer, skill-topology-adjuster, find-skills,
  automation-creator, omx-workspace-prune

Layer 1: Specialists (single-domain ownership)
  agents-md-builder, branch-onboarding-brief, code-health, desloppify, doc,
  doc-separator, docs-codebase-alignment-audit, gh-address-comments,
  gh-fix-ci, interface-design, jupyter-notebook, layer-boundary-test-scaffold,
  no-deep-flag-review, pdf, reverse-doc, screenshot, slides, spec-diff,
  spreadsheet, spreadsheets, yeet

Layer 2: Specialist-Orchestrators (domain workflow + bounded handoff)
  grepai-deep-analysis, refresh-branch-docs, non-test-bloat-reduction

Layer 3: Primary Orchestrators (task-level delivery ownership)
  branch-health-remediation-workflow, complexity-loc-balancer, main-merge,
  pr-workflow, session-wrap-up

Layer 4: Sub-Agent Preferred Activators (optional, scenario-bound)
  branch-health-remediation-workflow, gh-fix-ci, grepai-deep-analysis,
  non-test-bloat-reduction, skill-topology-adjuster, session-wrap-up
```

`codex-exec-sub-agent` remains a cross-cutting `meta-tool` runtime lane, but it is not currently an installed skill under `$CODEX_HOME/skills`; represent it only as optional runtime delegation (`Any Skill` -> `codex-exec-sub-agent`), not as an installed role-map node.

## Sub-Agent Activation Scenarios

| Skill | Prefer `codex-exec-sub-agent` When... | Expected Benefit |
| --- | --- | --- |
| grepai-deep-analysis | grep/search results are noisy across many modules and retries are needed | fresh context per cycle, less context contamination |
| branch-health-remediation-workflow | branch evidence collection spans onboarding + health + deep analysis | isolate heavy scans and keep the orchestrator thin |
| non-test-bloat-reduction | repeated candidate-cluster sweeps are needed over broad code areas | bounded long-running passes with traceable logs |
| skill-topology-adjuster | strict parity checks or O(N^2) overlap validation is requested | independent verification lane for drift adjudication |
| session-wrap-up | retrospective requires broad evidence mining before synthesis | offload heavy background scans while preserving summary context |
| gh-fix-ci | Actions logs are large, multi-run, or require repeated forensic extraction | isolate log-heavy analysis with reproducible artifacts |

## Delegation Graph

```mermaid
flowchart LR
  BHRW["branch-health-remediation-workflow"] --> BOB["branch-onboarding-brief"]
  BHRW --> CH["code-health"]
  BHRW --> GDA["grepai-deep-analysis"]

  NTBR["non-test-bloat-reduction"] --> CH
  NTBR --> GDA

  CLB["complexity-loc-balancer"] --> NTBR
  CLB --> CH

  MM["main-merge"] --> BOB
  MM --> RBD["refresh-branch-docs"]
  MM --> GDA
  MM --> CH

  RBD --> BOB
  RBD --> GDA

  PR["pr-workflow"] --> BOB
  PR --> CH
  PR --> GDA

  SWU["session-wrap-up"] --> SC["skill-creator"]
  SWU --> OWP["omx-workspace-prune"]
  SC --> STA["skill-topology-adjuster"]

  DOC["doc"] --> PDF["pdf"]
  SPD["spec-diff"] --> DSEP["doc-separator"]
  SPD --> RD["reverse-doc"]
  SS["spreadsheet"] --> PDF

  AMB["agents-md-builder"]
  AC["automation-creator"]
  DES["desloppify"]
  DCAA["docs-codebase-alignment-audit"]
  FS["find-skills"]
  GHF["gh-fix-ci"]
  GHC["gh-address-comments"]
  IFD["interface-design"]
  JNB["jupyter-notebook"]
  LBTS["layer-boundary-test-scaffold"]
  NDF["no-deep-flag-review"]
  SHOT["screenshot"]
  SLI["slides"]
  SPS["spreadsheets"]
  SI["skill-installer"]
  YEET["yeet"]

  ANY["Any Skill (Universal Access)"] --> CESA["codex-exec-sub-agent"]
  GDA --> CESA
  BHRW --> CESA
  NTBR --> CESA
  STA --> CESA
  SWU --> CESA
  GHF --> CESA
```

`codex-exec-sub-agent` is documented here as a reusable runtime meta-tool only. It is not part of the installed-skill role map for this snapshot.

## Delegation Tree (Operational View)

```mermaid
flowchart TD
  ROOT["Skill Topology"]

  ROOT --> ORCH["Primary Orchestrators"]
  ROOT --> HYB["Specialist-Orchestrators"]
  ROOT --> SPEC["Specialists"]
  ROOT --> META["Meta / Utility"]

  ORCH --> BHRW["branch-health-remediation-workflow"]
  ORCH --> CLB["complexity-loc-balancer"]
  ORCH --> MM["main-merge"]
  ORCH --> PR["pr-workflow"]
  ORCH --> SWU["session-wrap-up"]

  HYB --> GDA["grepai-deep-analysis"]
  HYB --> NTBR["non-test-bloat-reduction"]
  HYB --> RBD["refresh-branch-docs"]

  SPEC --> AMB["agents-md-builder"]
  SPEC --> BOB["branch-onboarding-brief"]
  SPEC --> CH["code-health"]
  SPEC --> DES["desloppify"]
  SPEC --> DOC["doc"]
  SPEC --> DSEP["doc-separator"]
  SPEC --> DCAA["docs-codebase-alignment-audit"]
  SPEC --> GHF["gh-fix-ci"]
  SPEC --> GHC["gh-address-comments"]
  SPEC --> IFD["interface-design"]
  SPEC --> JNB["jupyter-notebook"]
  SPEC --> LBTS["layer-boundary-test-scaffold"]
  SPEC --> NDF["no-deep-flag-review"]
  SPEC --> PDF["pdf"]
  SPEC --> RD["reverse-doc"]
  SPEC --> SHOT["screenshot"]
  SPEC --> SLI["slides"]
  SPEC --> SPD["spec-diff"]
  SPEC --> SS["spreadsheet"]
  SPEC --> SPS["spreadsheets"]
  SPEC --> YEET["yeet"]

  META --> SC["skill-creator"]
  META --> SI["skill-installer"]
  META --> STA["skill-topology-adjuster"]
  META --> FS["find-skills"]
  META --> AC["automation-creator"]
  META --> OWP["omx-workspace-prune"]

  BHRW --> BOB
  BHRW --> CH
  BHRW --> GDA

  NTBR --> CH
  NTBR --> GDA

  CLB --> NTBR
  CLB --> CH

  MM --> BOB
  MM --> RBD
  MM --> GDA
  MM --> CH

  RBD --> BOB
  RBD --> GDA

  PR --> BOB
  PR --> CH
  PR --> GDA

  SWU --> SC
  SWU --> OWP
  SC --> STA

  DOC --> PDF
  SPD --> DSEP
  SPD --> RD
  SS --> PDF

  ANY["Any Skill (Universal Access)"] --> CESA["codex-exec-sub-agent"]
  GDA --> CESA
  BHRW --> CESA
  NTBR --> CESA
  STA --> CESA
  SWU --> CESA
  GHF --> CESA
```

## Refactor Checklist

1. Identify duplicated procedures in non-owning skills.
2. Move details to the owning skill.
3. Replace duplicates with explicit delegation text.
4. Validate all edited skills with `quick_validate.py`.

## New Skill Onboarding Checklist

1. Classify the new skill role: `specialist`, `orchestrator`, `specialist-orchestrator`, `meta`, `utility`, or `meta-tool`.
2. Add the skill to the role map.
3. Add delegation edges to the graph only when they are real runtime handoffs.
4. Mirror every graph edge in the delegation tree in the same change.
5. Keep delegation depth to one hop by default.
6. Ensure specialist internals are not duplicated in orchestrators.
7. Validate edited skills with `quick_validate.py`.
