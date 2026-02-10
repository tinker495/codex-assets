#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

LINK_PATTERN = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")


def main() -> int:
    docs_root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("docs")
    docs_root = docs_root.resolve()

    if not docs_root.exists() or not docs_root.is_dir():
        print(f"[ERROR] docs root not found: {docs_root}")
        return 2

    missing: list[str] = []
    for md in docs_root.rglob("*.md"):
        lines = md.read_text(encoding="utf-8").splitlines()
        for idx, line in enumerate(lines, start=1):
            for match in LINK_PATTERN.finditer(line):
                link = match.group(1).strip().strip('"\'')
                if not link or link.startswith(("#", "http://", "https://", "mailto:")):
                    continue
                link_no_anchor = link.split("#", 1)[0]
                if not link_no_anchor:
                    continue
                target = (md.parent / link_no_anchor).resolve()
                if not target.exists():
                    missing.append(f"{md}:{idx}:{link}")

    if missing:
        print("\n".join(missing))
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
