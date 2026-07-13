---
name: html-report-writer
description: Creates self-contained, diagram-first HTML reports and briefings with inline SVG explanations, then reviews rendered snapshots with vision input. Use when the user asks for a report, briefing, review summary, status update, audit, research synthesis, or handoff as .html or explicitly says not to use .md.
---

# HTML Report Writer

## Quick start

1. Determine the audience, purpose, source material, and destination path from context. If the request is clear, do not interview the user.
2. Write a complete, self-contained `.html` file instead of a Markdown report, with SVG diagrams as the primary explanation medium.
3. Validate the file with `python scripts/validate_html_report.py path/to/report.html` when this script is available.
4. Render the HTML, save a screenshot, and inspect that screenshot through Codex vision input when available.
5. Final response: give the absolute file path, what it covers, and validation plus visual-review evidence.

## Output contract

- Start with `<!doctype html>`, language-tagged `<html>`, `<head>`, UTF-8 charset, viewport metadata, meaningful `<title>`, and inline CSS.
- Use semantic structure: `<header>`, `<main>`, `<section>`, headings in order, and `<footer>` only when useful.
- Keep the document static and portable: no external CSS, fonts, scripts, or remote images unless explicitly requested.
- Require inline SVG diagrams for the core explanation. Do not rely on Mermaid, canvas, or remote images unless they are pre-rendered into inline SVG or static HTML.
- Do not wrap the artifact in Markdown fences and do not create `.md` output unless the user separately requests it.
- Use the user's language for visible prose. Preserve source terms, code identifiers, issue numbers, and file paths as literals.
- Separate facts, judgments, assumptions, risks, next actions, and evidence/source sections.

## Diagram-first rules

- Most of the artifact should be visual explanation: SVG flowcharts, timelines, system maps, dependency graphs, swimlanes, state diagrams, risk heatmaps, or evidence maps.
- Put a visual executive summary near the top before dense prose. Prose should explain diagrams, not replace them.
- Use `<figure>` with inline `<svg>`, `<title>`, `<desc>`, visible labels, and a short caption for each major diagram.
- For architecture/process briefings, show actors, boundaries, data/control flow, decisions, and failure paths visually.
- For audits/reviews, prefer severity maps, finding clusters, cause-effect chains, and remediation roadmaps over long bullet lists.
- Keep diagrams readable at laptop width and print scale: avoid tiny labels, crossing lines, unlabeled arrows, and color-only meaning.
- Use tables as supporting structure; do not let prose-only sections dominate the report.

## HTML writing rules

- Favor readable information design: clear title block, short summary, scannable sections, compact tables, and restrained status badges.
- Use a centered content width, generous line height, print-friendly colors, and `@media print` rules.
- Use tables for comparison, status matrices, decision logs, and risk registers.
- Ensure long paths, URLs, hashes, and code identifiers wrap safely with CSS such as `overflow-wrap: anywhere`.
- Avoid dark-only themes, decorative gradients, nested cards, and marketing-style hero layouts for operational reports.
- For audits/reviews, include severity, evidence, impact, and recommended action for each finding.

## Workflow

1. Synthesize the source material into a short outline before writing.
2. Choose a filename in kebab-case, such as `release-readiness-brief-2026-05-18.html`, unless the user gave a path.
3. Write the HTML file with inline CSS, inline SVG diagrams, and no generated boilerplate comments.
4. Inspect for Markdown leakage and missing diagrams: no leading `#` headings, fenced code blocks around the whole document, raw Markdown tables, or diagram-free core sections.
5. Run the validator script if available:

   ```bash
   python /Users/mrx-ksjung/.agents/skills/html-report-writer/scripts/validate_html_report.py /path/to/report.html
   ```

6. Render the HTML in a browser and check that diagrams, labels, and dense sections do not overlap or overflow.

## Visual snapshot review

- Use Browser, Playwright, or another real renderer; save a desktop `.png` near the HTML or under `artifacts/`.
- For long reports, also capture one lower-page viewport with diagrams, tables, or dense content.
- Feed screenshots into Codex vision input, such as a local image attachment or `view_image`; inspect hierarchy, spacing, wrapping, contrast, overflow, and overlap.
- If problems appear, patch HTML/CSS and repeat once. Report screenshot path and verdict; if rendering is unavailable, state that separately.

## Minimal structure

```html
<!doctype html>
<html lang="ko">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Report Title</title>
    <style>
      body { margin: 0; font: 16px/1.6 system-ui, sans-serif; color: #1f2933; background: #f7f8fa; }
      main { max-width: 1040px; margin: 0 auto; padding: 32px 20px 56px; }
      svg, table { width: 100%; } svg { height: auto; } text, code { overflow-wrap: anywhere; }
      @media print { body { background: white; } main { max-width: none; padding: 0; } }
    </style>
  </head>
  <body>
    <main>
      <header><p>Briefing</p><h1>Report Title</h1><p>One-paragraph executive summary.</p></header>
      <figure>
        <svg viewBox="0 0 800 260" role="img" aria-labelledby="diagram-title diagram-desc">
          <title id="diagram-title">Core Explanation</title>
          <desc id="diagram-desc">Visual summary of the report flow.</desc>
        </svg>
        <figcaption>Core flow summary.</figcaption>
      </figure>
    </main>
  </body>
</html>
```
