# Complexity/LOC Decision Matrix

Use these reason codes for deterministic cycle verdicts.

| Code | Condition | Verdict | Required Action |
| --- | --- | --- | --- |
| `balance_ok` | offending blocks `<=` baseline, min-cc `<=` baseline, non-test net `<= 0`, xenon non-regressive | accepted | continue next cycle only if user requests |
| `loc_guardrail_breach` | non-test net `> 0` | rejected | run deletion-only follow-up before new extraction |
| `complexity_regression` | offending blocks `>` baseline or min-cc `>` baseline | rejected | revert or redesign branch structure |
| `xenon_regression` | xenon changed pass->fail | rejected | restore previous threshold status before proceeding |
| `balance_blocked` | two consecutive rejected cycles with same root cause | rejected | stop loop and report blocker clearly |

## Prioritization

When multiple failures are true, choose highest priority:

1. `xenon_regression`
2. `complexity_regression`
3. `loc_guardrail_breach`
4. `balance_blocked`
