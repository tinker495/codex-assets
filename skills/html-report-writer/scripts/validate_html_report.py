#!/usr/bin/env python3
"""Validate a self-contained HTML report artifact."""

from __future__ import annotations

import re
import sys
from html.parser import HTMLParser
from pathlib import Path


REQUIRED_TAGS = {"html", "head", "title", "body", "main", "style", "svg"}
REMOTE_ASSET_TAGS = {"audio", "embed", "iframe", "img", "script", "source", "track", "video"}


class ReportHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tags: set[str] = set()
        self.external_assets: list[str] = []
        self.html_lang = ""
        self.title_text = ""
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        normalized_tag = tag.lower()
        self.tags.add(normalized_tag)
        if normalized_tag == "title":
            self._in_title = True
        attr_map = {name.lower(): value or "" for name, value in attrs}
        if normalized_tag == "html":
            self.html_lang = attr_map.get("lang", "")
        asset_url = ""
        if normalized_tag == "link":
            asset_url = attr_map.get("href", "")
        elif normalized_tag in REMOTE_ASSET_TAGS:
            asset_url = attr_map.get("src", "")
        if asset_url.startswith(("http://", "https://", "//")):
            self.external_assets.append(asset_url)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title_text += data.strip()


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    parser = ReportHTMLParser()
    parser.feed(text)

    if path.suffix.lower() != ".html":
        errors.append("file extension must be .html")
    if not text.lstrip().lower().startswith("<!doctype html>"):
        errors.append("document must start with <!doctype html>")
    missing_tags = sorted(REQUIRED_TAGS - parser.tags)
    if missing_tags:
        errors.append(f"missing required tags: {', '.join(missing_tags)}")
    if not parser.html_lang:
        errors.append("html tag must include a lang attribute")
    if not parser.title_text:
        errors.append("title must not be empty")
    if "```" in text:
        errors.append("document contains Markdown code fences")
    if re.search(r"(?m)^#{1,6}\s+\S", text):
        errors.append("document appears to contain raw Markdown headings")
    if re.search(r"(?m)^\|.+\|$", text):
        errors.append("document appears to contain raw Markdown table rows")
    if parser.external_assets:
        errors.append("document references external assets: " + ", ".join(parser.external_assets))
    return errors


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: validate_html_report.py path/to/report.html", file=sys.stderr)
        return 2

    path = Path(argv[1])
    if not path.is_file():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2

    errors = validate(path)
    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        return 1

    print(f"ok: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
