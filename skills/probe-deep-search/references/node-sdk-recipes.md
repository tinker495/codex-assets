# Probe Node SDK Recipes

Use these examples when the task should call `@probelabs/probe` from code instead of shelling out.

## Import surface

```ts
import { search, extract, query, symbols } from "@probelabs/probe";
```

## Semantic search

```ts
const results = await search({
  query: "authentication",
  path: "./src",
  maxTokens: 10000,
});
```

## Exact extraction

```ts
const code = await extract({
  files: ["src/auth.ts:42"],
  format: "markdown",
});
```

## File symbol map

```ts
const fileSymbols = await symbols({
  files: ["src/auth.ts"],
});
```

## AST pattern query

```ts
const matches = await query({
  pattern: "async function $NAME($$$)",
  path: "./src",
  language: "typescript",
});
```

## Usage guidance

- Use the SDK when the repository already has Node.js tooling and the search must be embedded in code.
- Keep search paths narrow to reduce latency and noise.
- Mirror the CLI workflow: search first, then symbols or query, then extract exact code.
- Prefer returning small, reviewable result sets to upstream callers.
