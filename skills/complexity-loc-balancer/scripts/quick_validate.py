#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate complexity/LOC balance gate for one cycle.")
    parser.add_argument("--baseline-offending", type=int, required=True)
    parser.add_argument("--current-offending", type=int, required=True)
    parser.add_argument("--baseline-min-cc", type=int, required=True)
    parser.add_argument("--current-min-cc", type=int, required=True)
    parser.add_argument("--working-non-test-net", type=int, required=True)
    parser.add_argument("--xenon-regressed", action="store_true")
    args = parser.parse_args()

    failures: list[str] = []
    if args.xenon_regressed:
        failures.append("xenon_regression")
    if args.current_offending > args.baseline_offending or args.current_min_cc > args.baseline_min_cc:
        failures.append("complexity_regression")
    if args.working_non_test_net > 0:
        failures.append("loc_guardrail_breach")

    if failures:
        print("rejected")
        print("reason_codes=" + ",".join(failures))
        return 1

    print("accepted")
    print("reason_codes=balance_ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
