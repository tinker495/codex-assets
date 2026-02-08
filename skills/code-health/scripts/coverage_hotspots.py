import argparse
import json
import re
from pathlib import Path

TEST_RE = re.compile(r"(^|/)(tests?|__tests__)/|\.(test|spec)\.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Coverage hotspot summary")
    parser.add_argument("--coverage-json", type=Path, default=Path("coverage.json"))
    args = parser.parse_args()

    p = args.coverage_json
    if not p.exists():
        print(f"{p} not found.")
        return

    obj = json.loads(p.read_text())
    files = obj["files"]
    rows = []

    for fp, info in files.items():
        if not fp.startswith("src/"):
            continue
        if TEST_RE.search(fp):
            continue

        summ = info["summary"]
        stmts = summ.get("num_statements", 0)
        miss = summ.get("missing_lines", 0)
        # covered = summ.get('covered_lines', 0) # unused
        pct = summ.get("percent_covered", 0.0)
        rows.append((pct, miss, stmts, fp))

    rows.sort(key=lambda t: (t[0], -t[1], -t[2], t[3]))

    print("Lowest 15 non-test src files by % covered:")
    for pct, miss, stmts, fp in rows[:15]:
        print(f"{pct:6.2f}%  miss={miss:4d}  stmts={stmts:4d}  {fp}")

    # Missing hotspots by absolute missing lines
    rows2 = sorted(rows, key=lambda t: (-t[1], t[0], -t[2], t[3]))
    print("\nTop 20 missing-line hotspots (non-test src):")
    for pct, miss, stmts, fp in rows2[:20]:
        print(f"miss={miss:4d}  {pct:6.2f}%  stmts={stmts:4d}  {fp}")

    # Top 30 missing lines for a few files
    print("\nTop 5 hotspot missing lines (first 30 each):")
    for pct, miss, stmts, fp in rows2[:5]:
        missing = files[fp].get("missing_lines", [])
        print(f"\n{fp} ({pct:.2f}%, missing {miss})")
        print(", ".join(map(str, missing[:30])) + (" ..." if len(missing) > 30 else ""))


if __name__ == "__main__":
    main()
