# codex-skills mirror

This repository mirrors local Codex skills from `~/.codex/skills` into `./skills` and pushes updates to GitHub.

## One-time setup + sync

```bash
./scripts/sync_and_push.sh --repo tinker495/codex-skills --private
```

- Creates/uses `origin` GitHub repository.
- Syncs `~/.codex/skills` -> `./skills`.
- Commits and pushes when changes exist.

## Custom source path

```bash
./scripts/sync_and_push.sh --source /path/to/codex-skill --repo tinker495/codex-skills
```

## Continuous sync loop (optional)

```bash
INTERVAL_MINUTES=30 ./scripts/auto_sync_loop.sh --repo tinker495/codex-skills
```

Stop with `Ctrl+C`.

## Persistent background sync on macOS (recommended)

Install a `launchd` agent (runs on login and every N minutes):

```bash
INTERVAL_MINUTES=30 ./scripts/install_launch_agent.sh
```

Check status:

```bash
./scripts/launch_agent_status.sh
```

Remove agent:

```bash
./scripts/uninstall_launch_agent.sh
```
