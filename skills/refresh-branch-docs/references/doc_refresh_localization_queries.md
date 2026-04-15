# Doc Refresh Localization Query Pack

Use these commands to ground documentation refresh work with repo-local evidence.

## Discovery

```bash
probe search "changed workflow constraints rendering state" ./src --max-results 10
probe search "docs integrity checks make target links" . --max-results 10
probe search "plan quality reliability tracker" ./docs --max-results 10
```

## Exact anchors

```bash
rg -n "<symbol_or_term>" src docs
rg -n "TODO|TBD|FIXME|\\bdeprecated\\b" docs
rg -n "<old_symbol>|<new_symbol>" docs
```

## Block extraction

```bash
probe extract src/path/to/file.py#symbol_name
probe extract src/path/to/file.py:42
probe symbols src/path/to/file.py
```

## Dependency or call-path support

Use `rpg-loop-reasoning` when a claim needs cross-module flow proof.
Otherwise pair `probe extract` with nearby call-site searches:

```bash
rg -n "symbol_name\\(" src
rg -n "from .* import .*symbol_name|import .*module_name" src
```
