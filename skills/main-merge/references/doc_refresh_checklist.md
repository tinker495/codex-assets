# Doc Refresh Checklist

Use this checklist after merge conflicts are resolved and validation is complete.

## 1) Build doc impact set

Run:

```bash
python "$CODEX_HOME/skills/refresh-branch-docs/scripts/collect_doc_refresh_context.py" --base origin/main --format md
```

Prioritize:
- docs already changed on branch
- docs mapped from high-churn non-test modules
- API/spec docs that mention changed symbols

## 2) Ground every doc claim

For each updated behavior statement, require:
- one call-path anchor (`grepai trace graph` output)
- one symbol anchor (`rg -n`)
- one test/spec anchor when available

If one anchor is missing, mark as unresolved instead of asserting.

## 3) Rewrite and align terminology

- Replace stale names/signatures.
- Align data shape tables and constraint/objective wording.
- Remove outdated migration notes that no longer apply.

## 4) Consistency checks

```bash
rg -n "TODO|TBD|FIXME|\\bdeprecated\\b" docs
rg -n "<old_symbol>" docs
rg -n "<new_symbol>" docs
```

## 5) Delivery requirements

Report:
- updated docs list
- evidence anchors (file path + symbol)
- unresolved ambiguities
- follow-up items
