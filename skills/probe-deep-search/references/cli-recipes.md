# Probe CLI Recipes

Use these recipes when you need concrete `probe` commands quickly.

## Broad semantic search

```bash
probe search "authentication" ./src
probe search "error AND handling" ./
probe search "login OR auth" ./src
probe search "database NOT sqlite" ./
```

## Add file and directory hints early

```bash
probe search "function AND ext:rs" ./
probe search "class AND file:src/**/*.py" ./
probe search "error AND dir:tests" ./
probe search "API" ./ --max-tokens 10000
probe search "payment AND retry AND ext:ts" ./src --max-results 8
```

## Map a file before reading it

```bash
probe symbols src/main.rs
probe symbols src/main.rs --format json
probe symbols src/main.rs src/lib.rs
```

Use `probe symbols` before reading a long file when you only need the relevant functions, classes, or methods.

## Extract exact code bodies

```bash
probe extract src/main.rs:42
probe extract src/main.rs#authenticate
probe extract src/main.rs:10-50
go test | probe extract
```

Prefer extraction over opening whole files when you already know the symbol or line range.

## AST pattern search

```bash
probe query "async fn $NAME($$$)" --language rust
probe query "function $NAME($$$) { return <$$$> }" --language javascript
probe query "class $CLASS: def __init__($$$)" --language python
probe query "async function $NAME($$$)" ./src --language typescript
```

Use `probe query` when the request is about structure rather than words.

## Recommended search progression

1. `probe search` to find likely files or symbols.
2. `probe symbols` on the most relevant file.
3. `probe extract` on the target symbol or range.
4. `probe query` if you need sibling patterns or structural variants.

## When to retry or narrow

- Add `ext:`, `file:`, or `dir:` when the result set is noisy.
- Add `--max-results` when ranking is good but there is too much output.
- Add `--max-tokens` when you want richer snippets from fewer results.
- Retry on a narrower subtree before falling back to `rg`.
