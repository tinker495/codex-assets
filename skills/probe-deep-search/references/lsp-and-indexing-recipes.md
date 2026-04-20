# Probe LSP and Indexing Recipes

Use these recipes when plain `search -> symbols/query -> extract` is not enough and you need cross-file semantic navigation. This is still CLI-only Probe usage.

## Daemon health and readiness

```bash
probe lsp status
probe lsp ping
probe lsp languages
probe lsp version
probe lsp start
probe lsp init
probe lsp doctor
```

Use these first when semantic commands fail or seem stale.

## Symbol navigation

```bash
probe lsp call definition src/auth.ts:42:10
probe lsp call definition src/auth.ts#authenticate
probe lsp call references src/auth.ts#authenticate
probe lsp call references src/auth.ts#authenticate --include-declaration
probe lsp call implementations src/auth.ts#AuthProvider
probe lsp call type-definition src/auth.ts#AuthProvider
probe lsp call hover src/auth.ts#authenticate
probe lsp call call-hierarchy src/auth.ts#authenticate
probe lsp call fqn src/auth.ts#authenticate
```

Use `file:line:column` when you know the exact cursor position. Use `file#symbol` when symbol resolution is stable enough.

## Document and workspace symbol lookup

```bash
probe lsp call document-symbols src/auth.ts
probe lsp call workspace-symbols authenticate --max-results 20
```

Use these when `probe symbols` is too local but full-text search is too noisy.

## Enriched extraction

```bash
probe extract src/auth.ts#authenticate --lsp
probe extract src/auth.ts#authenticate --lsp --include-stdlib
probe search "authenticate" ./src --lsp
```

Use LSP-enriched search or extraction only when you actually need reference and call-hierarchy context.

## Workspace indexing

```bash
probe lsp index --workspace . --wait
probe lsp index --workspace . --languages rust,typescript --progress
probe lsp index --workspace . --file src/auth.ts --file src/routes.ts
probe lsp index-status --detailed
probe lsp index-status --follow
probe lsp index-stop
```

Index only when semantic commands are incomplete, stale, or too shallow for a large workspace.

## LSP admin and recovery

```bash
probe lsp logs
probe lsp crash-logs
probe lsp connections
probe lsp restart
probe lsp shutdown
probe lsp wal-sync
probe lsp cache --help
probe lsp index-config --help
probe lsp index-export --help
probe lsp edge-audit --help
probe lsp enrich-symbol --help
```

These are recovery and inspection tools. Do not reach for them during normal repository reading unless the semantic path is actually broken.

## Full LSP surface at a glance

- Daemon lifecycle: `status`, `languages`, `ping`, `version`, `start`, `restart`, `shutdown`, `doctor`
- Semantic calls: `call definition`, `references`, `hover`, `document-symbols`, `workspace-symbols`, `call-hierarchy`, `implementations`, `type-definition`, `fqn`
- Indexing: `index`, `index-status`, `index-stop`, `index-config`, `index-export`, `init`
- Diagnostics and admin: `logs`, `crash-logs`, `connections`, `cache`, `wal-sync`, `edge-audit`, `enrich-symbol`

## Probe configuration

```bash
probe config show
probe config validate
probe config get some.key
probe config set some.key some-value
probe config reset
```

Use configuration commands only when Probe behavior itself is surprising.
