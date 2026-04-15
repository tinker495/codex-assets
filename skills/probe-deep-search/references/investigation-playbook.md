# Investigation Playbook

Use this sequence when the user asks for a deep search, architecture read, or bug investigation.

## 1. Convert the request into search intents

Write down:

- domain terms
- likely symbol names
- known errors or log strings
- path constraints such as `src`, `server`, `tests`, or language extensions

## 2. Run one broad discovery pass

Use `probe search` with the strongest two or three terms first.

Examples:

```bash
probe search "checkout AND retry" ./src --max-results 8
probe search "session OR token" ./server --max-tokens 6000
```

## 3. Narrow structurally

For the best files:

- run `probe symbols <file>`
- extract the exact implementation with `probe extract`
- run `probe query` if sibling patterns matter

This is the minimum path for a "deep" read. Do not stop at ranked snippets alone.

## 4. Trace adjacent behavior

If the question is about behavior, follow one layer outward:

- caller
- callee
- validator
- serializer
- error handler

Repeat the same `search -> symbols/query -> extract` loop.

## 5. Decide whether fallback is justified

Fallback is justified when:

- `probe` cannot walk the target tree
- the files are non-code or unsupported
- the index is stale or unavailable
- you need a literal text search that structural tooling is missing

When falling back, say so explicitly and preserve the same investigation goal.
