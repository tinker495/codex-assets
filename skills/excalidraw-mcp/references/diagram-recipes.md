# Excalidraw MCP Diagram Recipes

## First-Draft Planning Template

Before calling `create_view`, write a four-line plan:

1. Diagram type: architecture, flowchart, sequence, timeline, comparison, or explainer
2. Primary structure: zones, lanes, columns, or stages
3. Reveal order: what appears first, second, third
4. Camera path: close-up intro, sectional pans, final zoom-out

If the plan is not clear, do not start emitting JSON yet.

## Architecture Diagram

Use when showing systems, services, boundaries, or data flow.

- Start with one camera for the whole diagram.
- Add soft background zones for layers such as client, API, worker, and storage.
- Use rounded rectangles with labels for services.
- Add arrows only after both endpoints exist.
- End with one wider camera if the diagram spans multiple zones.

Good pattern:
- title
- layer zones
- services per layer
- connectors
- final overview

## Flowchart or Process Diagram

Use when showing ordered steps, branching, approval, or state movement.

- Reveal one step at a time.
- Keep the main path aligned on one axis.
- Use diamonds only for decisions; avoid decorative shape variety.
- Label arrows only when the branch condition matters.
- Prefer fewer steps per camera rather than one dense canvas.

Good pattern:
- title
- step 1 and step 2
- decision branch
- success and failure terminals
- final zoom-out

## Sequence Diagram

Use when explaining request/response flow across actors.

- Create one actor column at a time.
- Use dashed vertical lifelines.
- Pan across actors before drawing many cross-column arrows.
- Add message arrows from top to bottom.
- Finish with one overview camera for the full exchange.

Good pattern:
- title
- actor headers
- lifelines
- first interaction
- later interactions
- overview

## Animated or Transforming Diagram

Use when the user wants motion, evolution, or before/after transitions.

- Draw the initial state.
- Nudge the camera slightly.
- Delete the old element ids.
- Add replacement elements with new ids at the updated position.
- Repeat in short steps.

Use this for:
- path traversal
- queue movement
- algorithm walkthroughs
- state transitions

## Revision Recipe

Patch the current scene when the user asks for local edits.

1. Recover the latest `checkpointId`.
2. Decide whether the edit is additive, subtractive, or transformational.
3. Restore the checkpoint.
4. Delete only the affected ids.
5. Append new elements with fresh ids.
6. Add a small camera adjustment only if the new content needs reframing.

Prefer rebuild instead when:
- most lanes or groups move
- the diagram type changes
- the old framing prevents readability

## Compact JSON Discipline

- Keep the JSON compact and machine-oriented.
- Skip default fields unless they matter visually.
- Prefer labels inside shapes over separate text nodes.
- Reuse the same small palette instead of styling each node differently.

The server works best when the diagram is built in small, legible chunks rather than one monolithic payload.
