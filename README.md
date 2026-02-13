# codex-assets mirror

> 그냥 개인용이니 신경쓰지 말고 지나가세요

This repository mirrors local Codex assets from:

- `~/.codex/skills` -> `./skills`
- `~/.codex/automations` -> `./automations`

and pushes updates to GitHub.

## Sync mode (important)

Default mode is `merge`.

- `merge` (default): copy/update from local source into this repo, but do **not** delete files that are missing locally.
- `mirror`: strict mirror mode that deletes files in this repo when they are missing from local source.

Use strict mirror mode only when needed:

```bash
./scripts/sync_and_push.sh --mode mirror --repo tinker495/codex-assets
```

## Subagent model policy

Team default subagent model:

```bash
export CODEX_SUBAGENT_MODEL="gpt-5.3-codex-spark"
```

Recommended placement:
- shared zsh profile (for example, `~/.zshrc` or team-managed shell bootstrap)
- CI/automation shell env where `codex-exec-sub-agent` or `rlm-batch-runner` runs

Quick check:

```bash
echo "$CODEX_SUBAGENT_MODEL"
```

## One-time setup + sync

```bash
./scripts/sync_and_push.sh --repo tinker495/codex-assets --private
```

- Creates/uses `origin` GitHub repository.
- Syncs `~/.codex/skills` -> `./skills`.
- Syncs `~/.codex/automations` -> `./automations`.
- Keeps repo-only files in default `merge` mode.
- Commits and pushes when changes exist.

## Custom source paths

```bash
./scripts/sync_and_push.sh \
  --skills-source /path/to/codex-skill \
  --automations-source /path/to/codex-automations \
  --repo tinker495/codex-assets
```

`--source` is still supported as an alias of `--skills-source`.

## Continuous sync loop (optional)

```bash
INTERVAL_MINUTES=30 ./scripts/auto_sync_loop.sh --repo tinker495/codex-assets
```

Stop with `Ctrl+C`.

## Persistent background sync on macOS (recommended)

Install a `launchd` agent (runs on login and every N minutes):

```bash
INTERVAL_MINUTES=30 ./scripts/install_launch_agent.sh
```

The launch agent runs both skills and automations sync jobs.

Check status:

```bash
./scripts/launch_agent_status.sh
```

Remove agent:

```bash
./scripts/uninstall_launch_agent.sh
```
