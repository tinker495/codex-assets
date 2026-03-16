# openai.yaml fields (generator scope + extended example)

`agents/openai.yaml` is an extended, product-specific config intended for the machine/harness to read, not the agent. It is separate from `SKILL.md` frontmatter and does not affect Anthropic-style skill triggering.

`scripts/generate_openai_yaml.py` currently scaffolds only the `interface:` block. If you need `dependencies:` or `policy:`, add them manually after generation.

## Extended example

```yaml
interface:
  display_name: "Optional user-facing name"
  short_description: "Optional user-facing description"
  icon_small: "./assets/small-400px.png"
  icon_large: "./assets/large-logo.svg"
  brand_color: "#3B82F6"
  default_prompt: "Optional surrounding prompt to use the skill with"

dependencies:
  tools:
    - type: "mcp"
      value: "github"
      description: "GitHub MCP server"
      transport: "streamable_http"
      url: "https://api.githubcopilot.com/mcp/"

policy:
  allow_implicit_invocation: true
```

## What the generator writes

When run without extra overrides, the generator writes:

```yaml
interface:
  display_name: "Generated from skill name"
  short_description: "Generated short UI description"
```

Supported `--interface key=value` fields:

- `display_name`
- `short_description`
- `icon_small`
- `icon_large`
- `brand_color`
- `default_prompt`

Canonical field order in generated output:

1. `display_name`
2. `short_description`
3. `icon_small`
4. `icon_large`
5. `brand_color`
6. `default_prompt`

## Constraints enforced by the generator

- Quote all string values.
- Keep keys unquoted.
- `short_description` must be 25-64 characters.
- `brand_color`, if present, must be a 6-digit hex color like `#3B82F6`.
- `icon_small` and `icon_large`, if present, must be relative paths starting with `./`.
- `default_prompt`, if present, must be non-empty.

## Writing guidance

- For `interface.display_name`: prefer a clean human-facing title.
- For `interface.short_description`: keep it scannable and concrete; avoid repeating the full skill description.
- For `interface.default_prompt`: prefer a short task-shaped prompt. If the goal is to demonstrate explicit skill invocation, mention the skill token such as `$skill-name`.
- Only include icon paths or brand color when the assets and brand choice are real, not placeholders.

## Field descriptions

- `interface.display_name`: Human-facing title shown in UI skill lists and chips.
- `interface.short_description`: Human-facing short UI blurb (25–64 chars) for quick scanning.
- `interface.icon_small`: Path to a small icon asset (relative to skill dir). Default to `./assets/` and place icons in the skill's `assets/` folder.
- `interface.icon_large`: Path to a larger logo asset (relative to skill dir). Default to `./assets/` and place icons in the skill's `assets/` folder.
- `interface.brand_color`: Hex color used for UI accents (e.g., badges).
- `interface.default_prompt`: Default prompt snippet inserted when invoking the skill.
- `dependencies`: Optional manual section for tool/runtime dependencies not scaffolded by the generator.
- `dependencies.tools[].type`: Dependency category. Only `mcp` is supported for now.
- `dependencies.tools[].value`: Identifier of the tool or dependency.
- `dependencies.tools[].description`: Human-readable explanation of the dependency.
- `dependencies.tools[].transport`: Connection type when `type` is `mcp`.
- `dependencies.tools[].url`: MCP server URL when `type` is `mcp`.
- `policy`: Optional manual section for harness behavior not scaffolded by the generator.
- `policy.allow_implicit_invocation`: When false, the skill is not injected into
  the model context by default, but can still be invoked explicitly via `$skill`.
  Defaults to true.
