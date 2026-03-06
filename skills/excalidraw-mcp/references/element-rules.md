# Excalidraw MCP Element Rules

## Tool Contract

- Use `read_me` once at the start of the conversation.
- Use `create_view` with a single string field named `elements`.
- `elements` must be a compact JSON array string.
- The server rejects invalid JSON and oversized payloads. Keep the scene incremental and checkpoint-driven when it grows.

## Camera Rules

- Use 4:3 cameras only.
- Preferred sizes:
  - `400x300`: close-up
  - `600x450`: section view
  - `800x600`: default whole-diagram view
  - `1200x900`: large overview
  - `1600x1200`: panorama only when necessary
- Start the array with `cameraUpdate` unless dark mode requires a full-canvas background rectangle first.
- Move the camera before revealing the elements it should frame.
- Use multiple camera updates for long diagrams instead of one overcrowded static scene.

## Layout Rules

- Prefer one labeled shape over separate shape plus text.
- Use standalone text mainly for titles, subtitles, and annotations.
- Minimum labeled shape size: `120x60`.
- Minimum spacing between neighboring items: `20-30px`.
- Minimum font sizes:
  - body labels: `16`
  - titles: `20`
  - secondary notes: `14`
- Keep arrows short and labels concise. If a label is long, widen the arrow or shorten the text.

## Ordering Rules

- Array order controls both streaming order and z-order.
- Reveal in this sequence:
  - camera or backdrop
  - background zones
  - main shapes
  - labels
  - arrows
  - decorative or finishing touches
- Avoid emitting all shapes first and all text later. That makes the animation harder to follow.

## Color and Contrast

- Use a small consistent palette within one scene.
- On white backgrounds, keep text dark enough to remain readable.
- Do not use emoji in labels or titles.
- For dark mode, start with an oversized background rectangle such as:

```json
{
  "type": "rectangle",
  "id": "darkbg",
  "x": -4000,
  "y": -3000,
  "width": 10000,
  "height": 7500,
  "backgroundColor": "#1e1e2e",
  "fillStyle": "solid",
  "strokeColor": "transparent",
  "strokeWidth": 0
}
```

Then switch text and fills to dark-background-safe colors.

## Checkpoints and Deletes

- Every successful `create_view` call returns a `checkpointId`.
- For edits, prepend:

```json
[{ "type": "restoreCheckpoint", "id": "<checkpointId>" }]
```

- Remove existing elements with:

```json
{ "type": "delete", "ids": "id1,id2,id3" }
```

- Never reuse deleted ids.
- If a checkpoint is missing or expired, rebuild from scratch instead of guessing.

## Practical Failure Modes

- Invalid JSON: remove comments, prose, trailing commas, and smart quotes.
- Overcrowded scene: split across cameras or use checkpoints.
- Tiny unreadable text: enlarge shapes and zoom in with the camera.
- Poor contrast: darken text or simplify the palette.
- Jumpy edits: patch from checkpoint instead of resending the whole scene for a small change.
