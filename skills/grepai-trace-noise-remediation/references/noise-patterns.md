# Noise Patterns

Use this catalog to quickly map observed graph artifacts to a test-first fix.

## Pattern 1: Declaration Self-Edge Artifact
- Symptom: self-edge exists at declaration line, not runtime call site.
- Typical root cause: regex call extraction captures function signature token as call.
- Test shape: assert `caller==callee` appears once and line matches runtime call.

## Pattern 2: Intermediate Inbound Overreach
- Symptom: unrelated callers are pulled into graph through non-root intermediate nodes.
- Typical root cause: BFS collects inbound edges at all depths.
- Test shape: for root path `A->B->C`, verify unrelated `X->B` is excluded.

## Pattern 3: String/Comment Artifacts
- Symptom: edges include tokens from log strings or comments (`enabled`, `fakeCall`, etc.).
- Typical root cause: regex call match applied without lexical masking.
- Test shape: include log/comment text and assert only real function references remain.

## Pattern 4: Anonymous Function Declaration Artifact
- Symptom: `func` appears as callee in Go output.
- Typical root cause: anonymous function declaration token matched as call.
- Test shape: include `go func() { helper() }()` and assert `func` is absent.

## Pattern 5: Stale Index False Negative
- Symptom: code change landed but graph metrics remain unchanged.
- Typical root cause: long-lived background watcher built from old binary/index state.
- Recovery:
  1. stop watcher
  2. run bounded foreground refresh
  3. restart background watcher
  4. re-measure same roots

## Root Set for Stable Comparison
Use this baseline set for watch/trace-heavy repositories:

```bash
go run ./cmd/grepai trace graph runWatchForeground --depth 2 --mode precise --json | jq '{root:.graph.root,node_count:(.graph.nodes|length),edge_count:(.graph.edges|length)}'
go run ./cmd/grepai trace graph watchProject --depth 2 --mode precise --json | jq '{root:.graph.root,node_count:(.graph.nodes|length),edge_count:(.graph.edges|length)}'
go run ./cmd/grepai trace graph discoverWorktreesForWatch --depth 2 --mode precise --json | jq '{root:.graph.root,node_count:(.graph.nodes|length),edge_count:(.graph.edges|length)}'
```
