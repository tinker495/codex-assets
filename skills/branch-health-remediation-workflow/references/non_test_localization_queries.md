# Non-test Localization Query Playbook

Use these commands to localize non-test cleanup candidates without semantic-index tooling.

## 1) Start with intent discovery

```bash
probe search "normalization duplication" ./src --max-results 10
probe search "cache invalidation or redundant io" ./src --max-results 10
probe search "large function or helper fanout" ./src --max-results 10
```

## 2) Narrow to exact symbols and files

```bash
rg -n "cached_property|lru_cache|cache" src
rg -n "TODO|FIXME|HACK" src
rg -n "normalize|convert|transform|coerce" src
rg -n "load|read|parse|deserialize|save|write|dump|serialize" src
```

## 3) Extract concrete blocks before proposing edits

```bash
probe extract src/path/to/file.py:42
probe extract src/path/to/file.py#symbol_name
probe symbols src/path/to/file.py
```

## 4) Graph escalation

When candidate intent crosses multiple modules, escalate to `rpg-loop-reasoning` or build a manual call/dependency path with:

```bash
rg -n "symbol_name" src
rg -n "from .* import .*symbol_name|import .*module_name" src
```
