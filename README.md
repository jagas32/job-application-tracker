# Job Application Tracker

A file-based job application tracking system with an automated pipeline: structured JSON records, status history, follow-up reminders, and a self-contained HTML metrics dashboard. Built to run two ways — conversationally through Claude (Cowork) or directly from the command line.

## Overview

Job searches generate scattered state: who you applied to, who responded, what's overdue, what's next. This project centralizes all of it in plain JSON files (no database, no services) and automates the bookkeeping:

- Every application is one auditable record with an append-only status history
- A reminder engine surfaces what needs a nudge before it goes stale
- A dashboard turns the pipeline into metrics you can act on (response rate, time-to-response, stage distribution)

## Key Features

- **Structured records** — one JSON file per application in `tracking/`, plus a lightweight `index.json` for fast lookups
- **Pipeline stages** — `applied` → `screening` → `interviewing` → `offer` | `rejected` | `withdrawn` | `ghosted`
- **Append-only history** — every status change is timestamped and noted; records are never blindly overwritten
- **Follow-up engine** — overdue / due-today / upcoming buckets, plus stale-application detection (14+ days quiet)
- **HTML dashboard** — KPI cards, stage and weekly-volume charts (Chart.js), follow-up and application tables in a single portable file
- **Safe by design** — read-modify-write updates, `--dry-run` previews, duplicate-record protection, privacy rules (no salaries or personal identifiers)

## How to Run

### With Cowork (conversational)

Just describe what happened — Claude maps it to the right skill:

> "I applied to Acme as a Data Analyst today" → `application-logger`
> "Acme scheduled a phone screen for Friday" → `status-updater`
> "What do I need to follow up on?" → `reminder-engine`
> "Run the pipeline" → `pipeline-orchestrator` (backup → log → update → remind → report)

### With Python (CLI)

```bash
# Log a new application
python3 scripts/run_pipeline.py add --company "Acme" --role "Data Analyst" \
    --source LinkedIn --link "https://..." --notes "Referred by J. Smith"

# Update a status (history is appended automatically)
python3 scripts/run_pipeline.py update --company Acme --status interviewing \
    --note "Onsite scheduled 6/15"

# Check follow-ups / rebuild the dashboard / both
python3 scripts/run_pipeline.py remind
python3 scripts/run_pipeline.py report
python3 scripts/run_pipeline.py all

# Preview any write without touching files
python3 scripts/run_pipeline.py --dry-run update --company Acme --status offer
```

Supporting scripts: `import_csv.py` (bulk import), `check_followups.py`, `build_dashboard.py`.

## Example (Sample Data)

`inputs/sample_applications.csv` ships with 5 realistic applications. Running the pipeline on it produces:

| Metric | Value |
|---|---|
| Applications tracked | 5 (Stripe, Datadog, HubSpot, Shopify, Cloudflare) |
| Pipeline | 1 interviewing · 1 screening · 2 applied · 1 rejected |
| Response rate | 60% |
| Avg days to first response | 8.7 |
| Follow-ups | 1 overdue (Datadog), 3 upcoming |

…rendered as KPI cards, charts, and tables in `outputs/dashboard.html`.

## Project Structure

```
JobApplicationTracker/
├── CLAUDE.md            # Conventions & instructions for Claude
├── README.md            # This file
├── inputs/              # Job postings, resumes, CSV imports
├── outputs/             # Generated dashboard (dashboard.html)
├── tracking/            # Source of truth: JSON records + index.json
├── skills/              # 5 Claude skills (log, update, remind, report, orchestrate)
├── scripts/             # Python: run_pipeline.py + helpers
├── examples/            # Sample records and reports
└── docs/                # Documentation
```

## Tech Stack

- **Python 3** (standard library only — `json`, `csv`, `argparse`, `pathlib`; zero dependencies)
- **Chart.js** (CDN) for dashboard visualizations
- **Claude skills** (Markdown specs) defining each workflow's rules and guardrails
- **Plain JSON** as the storage layer — portable, diffable, version-controllable

## Portfolio Value

This project demonstrates practical AI-workflow engineering:

- **Skill-based agent design** — five composable skills with explicit contracts (inputs, rules, failure modes), coordinated by an orchestrator with backup and validation steps
- **Human-AI parity** — every workflow runs identically via natural language or CLI, so automation never locks out manual control
- **Data integrity discipline** — append-only history, safe read-modify-write updates, dry-run previews, index consistency checks
- **Zero-infrastructure analytics** — a full metrics dashboard from flat files, no server required

## Privacy

Records store no salaries, SSNs, or personal identifiers beyond contact name/email. Tracking data stays in this folder and is never committed elsewhere.
