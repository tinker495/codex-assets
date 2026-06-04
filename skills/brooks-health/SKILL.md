---
name: brooks-health
description: "Read-only overall codebase health score across PR quality, architecture, tech debt, and tests."
---

# Brooks-Lint — Health Dashboard

## Setup

1. Read `../_shared/common.md` for the Iron Law, Project Config, Report Template, and Health Score rules
2. Read `../_shared/source-coverage.md` for book-level coverage, exceptions, and tradeoffs
3. Read `../_shared/decay-risks.md` for production risk symptom definitions
4. Read `../_shared/test-decay-risks.md` for test risk symptom definitions
5. Read `health-guide.md` in this directory for the dashboard orchestration process

## Process

**If the user has not specified a project or directory:** apply Auto Scope Detection
from `../_shared/common.md` to determine the review scope before proceeding.

1. Run abbreviated scans across all four dimensions (Step 1 of the guide)
2. Compute per-dimension and composite Health Scores with weighting (Step 2 of the guide)
3. Output the Health Dashboard using the dashboard report template (Step 3 of the guide)

**Mode line in report:** `Health Dashboard`
