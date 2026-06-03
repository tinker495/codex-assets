# Evidence Register

| Fact Or Claim | Source Type | Source Link Or Path | Retrieved Or Observed | Confidence | Notes |
| --- | --- | --- | --- | --- | --- |
| Repo has 353 commits from 2026-04-15 to 2026-06-04 and 250 branches | Git metadata | Local `git rev-list`, `git log`, `git branch -a` | 2026-06-04 | High | Re-run after new commits or branch pruning |
| Repo is a small repo for codebase-recon calibration, so all-time top-10 lists apply | Git metadata plus codebase-recon rule | User-supplied `codebase-recon` skill and local git vitals | 2026-06-04 | High | Rule threshold is under 500 commits |
| Top hotspot is `tests/tui/test_app.py` with 51 file touches | Git metadata | Local `git log --format=format: --name-only HEAD` with blank lines filtered | 2026-06-04 | Medium | Counts are file-touch appearances, not semantic churn |
| Top bug magnet is `tests/tui/test_app.py` with 16 file touches in fix/bug/broken commits | Git metadata | Local `git log -i -E --grep='fix|bug|broken'` | 2026-06-04 | Medium | Commit-message heuristic |
| No firefighting commits matched `revert|hotfix|emergency|rollback` | Git metadata | Local `git log --oneline HEAD` grep | 2026-06-04 | Medium | Keyword heuristic |
| Active contributors are 3 of 3 total contributors in the last 3 months | Git metadata | `git shortlog -sn --no-merges HEAD` and `--since='3 months ago' HEAD` | 2026-06-04 | High | Explicit `HEAD` was required for non-empty output |
| Pure SPP produces abstract slot decisions without standard container binding | Local documentation | `/Users/mrx-ksjung/project/snk2501o-sinokor-placement-optimization/src/stowage/planner/spp/AGENTS.md` | 2026-06-04 | High | Packed-OOG is a documented exception with actual OOG members |
| Loading SPP pipeline composes heuristic, `run_spp`, and PostSPP materialization | Local documentation | `/Users/mrx-ksjung/project/snk2501o-sinokor-placement-optimization/src/stowage/planner/spp/AGENTS.md` and `src/stowage/planner/pipeline/AGENTS.md` | 2026-06-04 | High | Verify implementation before changing code |
| `uv run spp-bench` is the official SPP benchmark command | Local documentation | `/Users/mrx-ksjung/project/snk2501o-sinokor-placement-optimization/src/scripts/AGENTS.md` | 2026-06-04 | High | Benchmark was not run during setup |
| TUI file I/O should go through `src/tui/data_loader.py` and widgets should render domain results only | Local documentation | `/Users/mrx-ksjung/project/snk2501o-sinokor-placement-optimization/src/tui/AGENTS.md` | 2026-06-04 | High | Applies to TUI layer |
