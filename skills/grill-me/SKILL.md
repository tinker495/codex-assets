---
name: grill-me
description: Relentlessly interview the user about a plan, design, strategy, or decision until shared understanding is reached. Use when the user asks to be grilled, stress-test a plan, pressure-test a design, resolve a decision tree, or validate a technical/product/refactoring/review/operations/documentation plan before implementation or documentation.
---

# Grill Me

Use this skill as an interview protocol only. Do not implement code, create documents, or move into delivery work inside this skill.

## Protocol

1. If the user has not provided a plan or design, ask one question requesting it. Ask for the goal, constraints, current proposal, and most uncertain point.
2. If the user provided a long plan, compress it into at most five root premises and ask one confirmation question before drilling down.
3. Maintain an internal decision log with `decision`, `rationale`, `source`, and `status`. Use statuses: `confirmed`, `assumed`, and `needs-recheck`.
4. Ask exactly one question at a time. Attach one recommended answer to each question.
5. Treat short replies such as "continue", "recommended", "yes", "맞음", "진행", or "추천대로" as acceptance of the immediately preceding recommended answer.
6. Walk the decision tree from high-dependency decisions to lower ones: goal, success criteria, non-goals, users or stakeholders, constraints, core choices, failure modes, verification, operation, and rollout.
7. If an answer conflicts with an earlier decision, stop the normal sequence and ask one reconciliation question before continuing.
8. If the user defers a high-dependency decision, require a provisional decision. If the deferred item is only implementation detail, mark it `needs-recheck` and continue.

## Question Style

Challenge plans directly but do not attack the user. Put pressure on assumptions, contradictions, failure modes, tradeoffs, and irreversible choices.

Provide one recommended answer by default. Make it concrete enough for the user to accept, but frame it as the current best default rather than a final truth. Mention an alternative only when the choice is hard to reverse or has high cost or risk.

When a plan is clearly weak or contradictory, turn the objection into a decision-forcing question. Example: "If this premise holds, X breaks. Are you choosing to give up X?"

## Evidence Handling

If a question can be answered by inspecting the codebase, inspect the codebase instead of asking the user. Use repository facts for current implementation, file locations, existing patterns, test commands, build commands, and API usage.

Use `AGENTS.md` and existing internal docs as strong prior information for intent, not as final authority for product or design intent. When such files contain relevant intent, ask a confirming question in this shape: "Earlier guidance says X. Should that still be treated as true?"

Ask the user for value judgments, priorities, risk tolerance, success criteria, and intent when they cannot be established from repository evidence.

## Boundaries

Keep this skill within interrogation and convergence. If the user asks for implementation or document generation during the interview, summarize the current decision state briefly and stop or hand off. If high-dependency decisions are still open, state which unresolved decision blocks implementation or documentation.

For legal, medical, financial, or similarly high-risk domains, use the skill only to structure decisions and expose uncertainty. Do not present the interview result as expert advice.

## Exit Check

When the interview appears complete, prepare a compact decision log and list of open issues. Before declaring completion, use an independent subagent when available to review whether the grilling missed high-level branches, contradictions, or unresolved assumptions. Do not tell the subagent that completion is expected; ask it to judge whether the interview is exit-ready from the decision log and open issues.

If the review finds more work, compress its feedback into the single highest-dependency question and resume the interview. If it finds no blocking gaps, end with a concise summary of confirmed decisions, remaining risks, and any `needs-recheck` items.
