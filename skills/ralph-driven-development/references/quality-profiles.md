# Quality Profiles

Use this file when repository `AGENTS.md` does not fully specify quality checks.

## Selection Order

1. Use commands explicitly defined in repo-local `AGENTS.md`.
2. If incomplete, use stack defaults below.
3. If still unclear, run the smallest safe check set and report assumptions.

## Stack Defaults

### Python

```bash
pytest -q
pre-commit run --all-files
```

### Node/TypeScript

```bash
npm test
npm run lint
```

### Go

```bash
go test ./...
go vet ./...
```

### Rust

```bash
cargo test
cargo clippy --all-targets --all-features
```

### Java

```bash
./gradlew test
./gradlew check
```

### Unknown Stack

```bash
make test
```

## Helper Command

```bash
python ~/.codex/skills/ralph-driven-development/scripts/ralph_state.py quality-plan --repo-root . --json
```
