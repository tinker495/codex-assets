---
name: excalidraw-mcp
description: "Use when the user wants a diagram drawn or revised inside Excalidraw through an MCP server named `excalidraw`: architecture diagrams, flowcharts, sequence diagrams, system maps, process visuals, animated explainers, or edits to an existing Excalidraw widget. This skill covers the full workflow: verify tool availability, call `read_me` once, plan camera flow and element order, render via `create_view`, and revise safely with checkpoints plus delete/restore patterns."
---

# Excalidraw MCP

Build diagrams through the `excalidraw` MCP server instead of describing them in prose. Favor readable scenes, deliberate camera moves, and checkpoint-based revisions over one giant JSON dump.

## Preflight

- Confirm the `excalidraw` MCP server is available.
- Expect model-callable tools `read_me` and `create_view`.
- If the server is missing, stop and tell the user the Excalidraw MCP is not configured.
- If this is the first render in the conversation, call `read_me` exactly once before `create_view`.
- If the user wants to modify the current diagram, reuse the latest `checkpointId` unless a full rebuild is clearly simpler.

## Workflow

1. Decide whether to create a new diagram or patch an existing one.
2. Write a short scene plan before emitting JSON:
   - diagram type
   - major nodes or lanes
   - reveal order
   - camera sequence
3. Convert the plan into a compact JSON array string and pass it to `create_view`.
4. Save the returned `checkpointId` for follow-up edits.
5. For follow-up edits, start with `restoreCheckpoint`, delete only what must change, and append new elements with fresh ids.

## Hard Rules

- Keep `elements` valid JSON. No comments, no trailing commas, no prose around the array.
- Start with `cameraUpdate` unless dark mode is requested; in dark mode, place the oversized dark background rectangle first, then the camera.
- Use only 4:3 camera sizes. Prefer `400x300`, `600x450`, `800x600`, `1200x900`, or `1600x1200`.
- Prefer labeled shapes over separate text elements whenever possible.
- Emit elements in reveal order: camera/background, shape, label, connector, next shape.
- Keep body text at `fontSize >= 16`, titles at `>= 20`, and secondary annotations at `>= 14`.
- Keep labeled boxes at least `120x60`.
- Never reuse an id after deletion.
- Do not call `read_me` repeatedly in the same conversation.
- Do not use emoji in diagram text.

## Edit Strategy

- Patch instead of rebuild when the user wants small additions, removals, recolors, relabels, or one local restructuring.
- Rebuild when the user changes the diagram type, framing, lane model, or most of the layout.
- Patch pattern:

```json
[
  { "type": "restoreCheckpoint", "id": "<checkpointId>" },
  { "type": "delete", "ids": "old1,old2" },
  { "type": "rectangle", "id": "new1", "x": 100, "y": 100, "width": 180, "height": 80 }
]
```

- If host or widget context exposes manual fullscreen edits, inspect that state before overwriting the scene.

## Composition Heuristics

- Give each camera one idea to reveal.
- Keep at least `20-30px` spacing between neighboring elements.
- Use background zones for layers or subsystems instead of overpacking nodes.
- For flows, reveal left-to-right or top-to-bottom.
- For sequence diagrams, pan across actor columns, then zoom out for the full interaction.
- For animation-like transforms, alternate slight camera nudges with delete-and-replace steps.

## Tool Boundaries

- Main model workflow: `read_me` then `create_view`.
- Treat `export_to_excalidraw`, `save_checkpoint`, and `read_checkpoint` as app-side helpers unless they are explicitly exposed to the model.

## References

- Read [element-rules.md](./references/element-rules.md) for JSON, camera, sizing, color, and checkpoint rules.
- Read [diagram-recipes.md](./references/diagram-recipes.md) for repeatable composition patterns and edit recipes.
