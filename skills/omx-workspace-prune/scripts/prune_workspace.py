#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import shutil
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path


@dataclass(frozen=True)
class Action:
    kind: str
    source: Path
    target: Path | None = None


def _pick_newest(paths: list[Path]) -> Path | None:
    if not paths:
        return None
    return max(paths, key=lambda p: p.stat().st_mtime)


def _extract_active_references(active_file: Path) -> set[str]:
    if not active_file.exists():
        return set()
    text = active_file.read_text(encoding='utf-8', errors='ignore')
    refs = set(re.findall(r'([A-Za-z0-9_.-]+\.md)', text))
    return refs


def _resolve_keep_session(state_dir: Path, explicit: str | None) -> str | None:
    if explicit:
        return explicit
    env_value = os.environ.get('OMX_SESSION_ID', '').strip()
    if env_value:
        return env_value

    candidates: list[Path] = []
    sessions_dir = state_dir / 'sessions'
    if sessions_dir.exists():
        candidates.extend([p for p in sessions_dir.iterdir() if p.is_dir() and p.name.startswith('omx-')])
    candidates.extend([p for p in state_dir.iterdir() if p.is_dir() and p.name.startswith('omx-')])
    newest = _pick_newest(candidates)
    return newest.name if newest else None


def _collect_session_actions(omx_dir: Path, keep_session: str | None) -> list[Action]:
    actions: list[Action] = []
    state_dir = omx_dir / 'state'
    if not state_dir.exists():
        return actions

    targets: list[Path] = []
    sessions_dir = state_dir / 'sessions'
    if sessions_dir.exists():
        targets.extend([p for p in sessions_dir.iterdir() if p.is_dir()])
    targets.extend([p for p in state_dir.iterdir() if p.is_dir() and p.name.startswith('omx-')])

    seen: set[Path] = set()
    for target in targets:
        if target in seen:
            continue
        seen.add(target)
        if keep_session and target.name == keep_session:
            actions.append(Action('KEEP', target))
        else:
            actions.append(Action('DELETE', target))
    return actions


def _collect_log_actions(omx_dir: Path, retention_days: int) -> list[Action]:
    logs_dir = omx_dir / 'logs'
    if not logs_dir.exists():
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    actions: list[Action] = []
    for log_file in sorted(logs_dir.glob('*.jsonl')):
        mtime = datetime.fromtimestamp(log_file.stat().st_mtime, tz=timezone.utc)
        if mtime < cutoff:
            actions.append(Action('DELETE', log_file))
        else:
            actions.append(Action('KEEP', log_file))
    return actions


def _collect_plan_actions(omx_dir: Path) -> list[Action]:
    plans_dir = omx_dir / 'plans'
    if not plans_dir.exists():
        return []

    archive_dir = plans_dir / 'archive'
    actions: list[Action] = []

    active_refs = _extract_active_references(plans_dir / 'ACTIVE.md')

    prd_latest = _pick_newest(list(plans_dir.glob('prd-*.md')))
    test_latest = _pick_newest(list(plans_dir.glob('test-spec-*.md')))

    keep_names = {'ACTIVE.md', 'README.md'}
    keep_names.update(active_refs)
    if prd_latest:
        keep_names.add(prd_latest.name)
    if test_latest:
        keep_names.add(test_latest.name)

    for file_path in sorted(plans_dir.glob('*.md')):
        if file_path.name in keep_names:
            actions.append(Action('KEEP', file_path))
            continue
        target = archive_dir / file_path.name
        actions.append(Action('ARCHIVE', file_path, target))

    return actions


def _apply_action(action: Action) -> None:
    if action.kind == 'DELETE':
        if action.source.is_dir():
            shutil.rmtree(action.source)
        elif action.source.exists():
            action.source.unlink()
    elif action.kind == 'ARCHIVE':
        assert action.target is not None
        action.target.parent.mkdir(parents=True, exist_ok=True)
        final_target = action.target
        if final_target.exists():
            stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
            final_target = final_target.with_name(f'{final_target.stem}-{stamp}{final_target.suffix}')
        shutil.move(str(action.source), str(final_target))


def main() -> int:
    parser = argparse.ArgumentParser(description='Prune .omx workspace safely')
    parser.add_argument('--workspace-root', default='.', help='Repository root containing .omx')
    parser.add_argument('--apply', action='store_true', help='Apply changes (default is dry-run)')
    parser.add_argument('--keep-session', help='Explicit session id to keep')
    parser.add_argument('--log-retention-days', type=int, default=7, help='Keep logs newer than N days')
    args = parser.parse_args()

    root = Path(args.workspace_root).resolve()
    omx_dir = root / '.omx'
    if not omx_dir.exists():
        raise SystemExit(f'ERROR: .omx directory not found under {root}')

    state_dir = omx_dir / 'state'
    keep_session = _resolve_keep_session(state_dir, args.keep_session) if state_dir.exists() else args.keep_session

    session_actions = _collect_session_actions(omx_dir, keep_session)
    log_actions = _collect_log_actions(omx_dir, args.log_retention_days)
    plan_actions = _collect_plan_actions(omx_dir)

    all_actions = session_actions + log_actions + plan_actions

    mode = 'apply' if args.apply else 'dry-run (no filesystem changes)'
    print(f'Mode: {mode}')
    print(f'Workspace: {root}')
    print(f'Keep session: {keep_session or "(none detected)"}')

    if not all_actions:
        print('SKIP no prune targets found')
        return 0

    for action in all_actions:
        if action.kind in {'KEEP', 'DELETE'}:
            print(f'{action.kind} {action.source}')
        else:
            print(f'ARCHIVE {action.source} -> {action.target}')

    if not args.apply:
        return 0

    for action in all_actions:
        if action.kind in {'DELETE', 'ARCHIVE'}:
            _apply_action(action)

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
