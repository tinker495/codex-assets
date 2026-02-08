#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json


QUERY_PACKS: dict[str, list[str]] = {
    "understanding": [
        'grepai search "{seed} architecture module boundary interface contract" --json --compact',
        'grepai search "{seed} error handling fallback default warning" --json --compact',
        'grepai trace graph "{root_symbol}" --depth 5 --json',
        'rg -n "{seed}|{root_symbol}" src tests docs',
    ],
    "generation": [
        'grepai search "{seed} planner implementation data flow interface" --json --compact',
        'grepai search "{seed} dependency import call graph" --json --compact',
        'grepai trace graph "{root_symbol}" --depth 6 --json',
        'rg -n "{seed}|{root_symbol}" src docs',
    ],
    "hybrid": [
        'grepai search "{seed} architecture module boundary interface contract" --json --compact',
        'grepai search "{seed} planner implementation data flow interface" --json --compact',
        'grepai trace graph "{root_symbol}" --depth 5 --json',
        'rg -n "{seed}|{root_symbol}" src tests docs',
    ],
}


def format_queries(mode: str, seed: str, root_symbol: str) -> list[str]:
    templates = QUERY_PACKS[mode]
    return [q.format(seed=seed, root_symbol=root_symbol) for q in templates]


def main() -> None:
    parser = argparse.ArgumentParser(description="Emit RPG loop query packs.")
    parser.add_argument("--mode", choices=("understanding", "generation", "hybrid"), default="hybrid")
    parser.add_argument("--seed", default="anomaly", help="Domain seed term for search queries.")
    parser.add_argument("--root-symbol", default="prepare_anomaly_tiers_for_plans", help="Root symbol for tracing.")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args()

    queries = format_queries(args.mode, args.seed, args.root_symbol)
    payload = {
        "mode": args.mode,
        "seed": args.seed,
        "root_symbol": args.root_symbol,
        "queries": queries,
    }

    if args.format == "json":
        print(json.dumps(payload, indent=2))
        return

    print(f"# RPG Query Pack ({args.mode})")
    print(f"seed: {args.seed}")
    print(f"root_symbol: {args.root_symbol}")
    print("")
    for index, query in enumerate(queries, start=1):
        print(f"{index}. {query}")


if __name__ == "__main__":
    main()
