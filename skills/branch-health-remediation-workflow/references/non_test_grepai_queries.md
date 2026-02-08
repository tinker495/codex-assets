# Non-test Grepai Query Playbook

Use this playbook to start non-test inefficiency and fragmentation analysis. Filter out test-only hits in synthesis.

```mermaid
flowchart LR
  A["Select entry points"] --> B["Search"]
  B --> C["Trace"]
  C --> D["Filter tests"]
  D --> E["Summarize"]
```

## Non-test scope filters
- Exclude `tests/`.
- Exclude `**/test_*.py`.
- Exclude `**/*_test.py`.
- Exclude `**/conftest.py`.

## Entry-point discovery
- Prefer `rg --files -g '!tests/**' -g '!**/test_*.py' -g '!**/*_test.py' -g '!**/conftest.py' src` to list candidates.
- Use `grepai search "def main|__main__|App\\(|cli" --json --compact` to find primary entry points.
- Use code-health top churn/complexity files as entry points, but keep them non-test only.

## Query set (start)
Run each with `--json --compact`.
- `grepai search "cached_property|lru_cache|cache" --json --compact`
- `grepai search "TODO|FIXME|HACK" --json --compact`
- `grepai search "normalize|convert|transform|coerce" --json --compact`
- `grepai search "load|read|parse|deserialize" --json --compact`
- `grepai search "save|write|dump|serialize" --json --compact`

## Query set (duplication and fragmentation)
Run each with `--json --compact`.
- `grepai search "duplicate|clone|copy\\(|deepcopy\\(" --json --compact`
- `grepai search "adapter|wrapper|facade|bridge" --json --compact`
- `grepai search "manager|service|helper" --json --compact`

## Query set (hot paths and heavy work)
Run each with `--json --compact`.
- `grepai search "calc|compute|score|cost|weight|optimi[sz]e|evaluate" --json --compact`
- `grepai search "sort\\(|sorted\\(" --json --compact`
- `grepai search "re\\.compile|re\\.search|re\\.match|re\\.findall" --json --compact`

## Query set (I/O and serialization)
Run each with `--json --compact`.
- `grepai search "open\\(|Path\\(|read_text|write_text|read_bytes|write_bytes" --json --compact`
- `grepai search "json\\.load|json\\.dump|yaml\\.|toml\\.|csv\\." --json --compact`

## Query set (state mutation and batching)
Run each with `--json --compact`.
- `grepai search "append\\(|extend\\(|setdefault\\(|update\\(|pop\\(" --json --compact`
- `grepai search "global |nonlocal |singleton|registry" --json --compact`

## Query set (warnings and fallbacks)
Run each with `--json --compact`.
- `grepai search "logger\\.|logging\\.getLogger|warnings\\.warn|warn\\(" --json --compact`
- `grepai search "try:|except |fallback|default" --json --compact`

## Trace targets
Use `grepai trace graph` depth 5 to 7 from main entry points and heavy functions discovered above.

## Synthesis checklist
- Confirmed inefficiency findings with evidence anchors.
- Fragmentation areas with module-level call graph notes.
- At least one deletion or consolidation option if safe.
