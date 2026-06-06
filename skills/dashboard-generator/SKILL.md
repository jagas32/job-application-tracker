---
name: dashboard-generator
description: Generate an HTML dashboard of job application metrics from tracking/ data. Use when the user asks for a dashboard, report, metrics, stats, or pipeline overview.
---

# Dashboard Generator

## Purpose
Read all records in `tracking/` and produce a self-contained `outputs/dashboard.html`.

## Metrics
- **KPI cards**: total applications, active (not rejected/withdrawn/ghosted), response rate (% past `applied`), offers, avg days to first response.
- **Pipeline by stage**: count per status (bar chart).
- **Applications over time**: weekly counts from `date_applied` (line chart).
- **Follow-ups due**: table of records with `follow_up_date` <= today, sorted oldest first.
- **Full table**: company, role, status, date applied, days in current stage, next follow-up.

## Workflow
1. Load every `tracking/*.json` (skip `index.json` for metrics; use it only for lookups).
2. Compute metrics with a script in `scripts/` (create `scripts/build_dashboard.py` if missing; reuse it on later runs).
3. Render a single-file HTML dashboard (inline CSS/JS; Chart.js from cdnjs is acceptable) to `outputs/dashboard.html`.
4. Overwrite the previous dashboard — outputs are regenerable, tracking data is not.
5. Present the file to the user.

## Rules
- Read-only with respect to `tracking/` — this skill never modifies records.
- Handle empty/missing tracking data gracefully: render an empty-state dashboard, don't error.
- Days-in-stage = today minus last `history[]` entry date.
- Privacy: dashboard shows company/role/status only; no contact emails.
