# Probe CLI Recipes

Use these recipes when you need concrete `probe` commands quickly.

## Invocation policy

```bash
probe search "authentication flow" ./src
npx -y @probelabs/probe@latest search "authentication flow" ./src
```

Prefer the installed `probe` binary. Use the `npx` form only as an install-less fallback. Do not use `agent`, `probe-chat`, SDK, or MCP surfaces from this skill.

## Top-level command map

- `probe search`: semantic discovery and ranked code retrieval.
- `probe symbols`: symbol table-of-contents for one or more files.
- `probe extract`: exact body extraction by file, line, range, symbol, diff, or stdin.
- `probe query`: AST-pattern search.
- `probe lsp`: semantic navigation, daemon management, and workspace indexing.
- `probe config`: configuration inspection and validation.
- `probe benchmark`: Probe self-benchmarking only.

## Broad semantic search

```bash
probe search "authentication" ./src
probe search "error AND handling" ./
probe search "login OR auth" ./src
probe search "database NOT sqlite" ./
probe search "(error OR exception) AND retry" ./src
probe search "\"rate limit\"" ./src
probe search "+authenticate -legacy" ./src
probe search "auth*" ./src
```

## Add file and directory hints early

```bash
probe search "function AND ext:rs" ./
probe search "class AND file:src/**/*.py" ./
probe search "error AND dir:tests" ./
probe search "handler AND type:rust" ./
probe search "route AND lang:typescript" ./
probe search "API" ./ --max-tokens 10000
probe search "payment AND retry AND ext:ts" ./src --max-results 8
```

## Control result shape

```bash
probe search "config" ./ --files-only
probe search "config" ./ --dry-run
probe search "auth" ./src --max-results 5 --format json
probe search "auth" ./src --max-bytes 12000 --format xml
probe search "auth" ./src --no-merge --merge-threshold 1
probe search "exact_symbol_name" ./src --exact
probe search "\"UserService\" AND implementation" ./src --strict-elastic-syntax
probe search "auth OR login" ./src --session my-session-1
probe search "retry policy" ./src --reranker hybrid2
```

## Search option inventory

- Filesystem scope: `--ignore`, `--no-gitignore`, `--exclude-filenames`, `--language`
- Search semantics: `--frequency`, `--exact`, `--strict-elastic-syntax`
- Result caps: `--max-results`, `--max-bytes`, `--max-tokens`, `--timeout`
- Result shape: `--files-only`, `--dry-run`, `--no-merge`, `--merge-threshold`, `--format`
- Ranking extras: `--reranker`, `--question`
- Investigation state: `--session`, `--allow-tests`, `--lsp`

## Map a file before reading it

```bash
probe symbols src/main.rs
probe symbols src/main.rs --format json
probe symbols src/main.rs src/lib.rs
probe symbols src/main.rs --allow-tests
```

Use `probe symbols` before reading a long file when you only need the relevant functions, classes, or methods.

## Extract exact code bodies

```bash
probe extract src/main.rs:42
probe extract src/main.rs#authenticate
probe extract src/main.rs:10-50
probe extract src/main.rs#authenticate src/lib.rs#authorize
probe extract src/main.rs:42 --context 5
probe extract src/main.rs:42 --keep-input
git diff -- src/main.rs | probe extract --diff
rg -n "authenticate" src | probe extract --keep-input
go test | probe extract
```

Prefer extraction over opening whole files when you already know the symbol or line range.

## Extract option inventory

- Input sources: positional file refs, stdin, `--diff`, `--from-clipboard`, `--input-file`
- Scope controls: `--context`, `--ignore`, `--no-gitignore`, `--allow-tests`
- Output controls: `--format`, `--dry-run`, `--keep-input`, `--to-clipboard`
- Semantic enrichment: `--lsp`, `--include-stdlib`
- Intentionally unused in this skill: `--prompt`, `--instructions`

## AST pattern search

```bash
probe query "async fn $NAME($$$)" --language rust
probe query "function $NAME($$$) { return <$$$> }" --language javascript
probe query "class $CLASS: def __init__($$$)" --language python
probe query "async function $NAME($$$)" ./src --language typescript
probe query "type $NAME struct { $$$FIELDS }" ./pkg --language go --format json
```

Use `probe query` when the request is about structure rather than words.

## Query option inventory

- Parsing and scope: `--language`, `--ignore`, `--no-gitignore`, `--allow-tests`
- Payload control: `--max-results`, `--format`

## Escalate to LSP only when semantics matter

```bash
probe search "authenticate" ./src --lsp
probe extract src/auth.ts#authenticate --lsp
probe lsp call definition src/auth.ts#authenticate
probe lsp call references src/auth.ts#authenticate --include-declaration
probe lsp call call-hierarchy src/auth.ts#authenticate
```

See `lsp-and-indexing-recipes.md` for the full semantic-navigation surface.

## Other CLI surfaces

```bash
probe config show
probe config validate
probe benchmark --bench search --fast
```

Use `config` only when Probe behavior is surprising. Use `benchmark` only when diagnosing Probe itself.

## Recommended search progression

1. `probe search` to find likely files or symbols.
2. `probe symbols` on the most relevant file.
3. `probe extract` on the target symbol or range.
4. `probe query` if you need sibling patterns or structural variants.
5. `probe lsp ...` only if cross-file semantics still matter after extraction.

## When to retry or narrow

- Add `ext:`, `file:`, or `dir:` when the result set is noisy.
- Add `type:` or `lang:` when extension hints are too broad.
- Add `--max-results` when ranking is good but there is too much output.
- Add `--max-bytes` when you want a hard payload ceiling.
- Add `--max-tokens` when you want richer snippets from fewer results.
- Use `--files-only` or `--dry-run` when you need anchors before full extraction.
- Retry on a narrower subtree before falling back to `rg`.
