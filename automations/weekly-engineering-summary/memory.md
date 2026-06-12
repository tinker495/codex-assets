2026-06-05 16:03:08 KST

- Weekly summary basis collected for 2026-05-29..2026-06-05.
- Merged PRs confirmed from git first-parent and GitHub metadata: #265, #267, #268, #259, #263, #276.
- No explicit incident issues found via GitHub issue search (`incident OR outage OR sev OR postmortem OR rollback OR hotfix`), and no rollout/release notes found in repo search; only `beforeSeparate` tag exists locally.
- Key watch items from merged PR bodies: `TODO(spp-pure-stack-weight)` in PR #276, separate flaky calculator test investigation noted in PR #268, missing `make test-full` target noted in PR #267.
- Review activity this week included human approvals on all merged PRs plus automated Codex/Gemini comment reviews; notable review topics were timing diagnostics/run-button guards (#267), `_settle_until`/timeout config (#268), and RF key prefilter simplification (#265).

2026-06-12 16:03:23 KST

- Weekly summary basis collected for 2026-06-05..2026-06-12 from `git log --first-parent` and GitHub PR metadata/reviews.
- Merged PRs confirmed on `main`: #307, #308, #309, #310, #311, #313, #322, #325, #328, #329, #330, #331, #332, #333, #334, #335, #336, #337, #338, #339.
- Main delivery lane this week was the `Planning Demand`/`Quantity Bound` stack (#307-#313, #322), with representative file paths `docs/adr/0008-planning-demand-quantity-bound.md`, `src/stowage/planner/demand.py`, `src/stowage/planner/quantity_bound.py`, and `src/tui/dataclass_widgets/quantity_bound.py`.
- Follow-up stabilization landed as hotfix PR #328 on `2026-06-11`, scoped to `tests/stowage/planner/spp/_regression_diagnostics_and_oog_helpers.py`, `tests/stowage/planner/spp/_solver_test_utils.py`, and `tests/stowage/planner/spp/test_regression_spp_diagnostics_evaluator.py`.
- Cleanup wave merged on `2026-06-12`: docs/meta-clean PRs #325, #329-#332 and ultraclean PRs #333-#339; representative paths include `docs/index.md`, `src/tui/renderers/spp_renderer.py`, `src/stowage/planner/spp/heuristic/solver/horizontal/middle.py`, and `src/stowage/domain/stowage_plan/stowage_plan.py`.
- No explicit incident issue was found via GitHub search `incident OR outage OR sev OR postmortem OR rollback OR hotfix updated:>=2026-06-05`, and no separate rollout/release note was found in repo search; only local tag `beforeSeparate` exists.
- Review signal: merged PRs in this window show `APPROVED`, primarily by `kh-mo` or `bwkim71`, with automated Codex/Gemini comment reviews attached; current queue still needing review is PR #314, #340, and #342.
