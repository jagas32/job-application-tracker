# Job Application Tracker

## Overview & Goal
Track job applications end-to-end: log new applications, update statuses, schedule follow-ups, and surface metrics (response rate, time-to-response, pipeline by stage) in a dashboard.

## Folder Structure
- `inputs/` — raw materials: job postings, resumes, cover letters
- `outputs/` — generated reports and dashboards (HTML/MD)
- `tracking/` — source of truth: one JSON file per application + `index.json`
- `skills/` — workflow skills (logger, updater, dashboard, reminders, orchestrator)
- `examples/` — sample application records and reports
- `scripts/` — reusable Python/shell helpers used by skills
- `docs/` — project documentation

## Key Conventions
- **Structured JSON per application**: `tracking/<company>-<role-slug>.json` with fields: `id`, `company`, `role`, `date_applied`, `status`, `source`, `contacts`, `follow_up_date`, `history[]` (timestamped status changes), `notes`.
- **Statuses**: `applied` → `screening` → `interviewing` → `offer` | `rejected` | `withdrawn` | `ghosted`.
- **Safe updates**: never overwrite a record blindly — read, append to `history[]`, then write. Back up `tracking/` before bulk operations.
- **Privacy**: no salaries, SSNs, or personal identifiers beyond name/email in records; never commit tracking data outside this folder.

## Current Status (2026-06-06) — Setup Complete
- All 5 skills created: application-logger, status-updater, reminder-engine, dashboard-generator, pipeline-orchestrator.
- `scripts/run_pipeline.py` — CLI runner: `add`, `update`, `remind`, `report`, `all`, with global `--dry-run`. Tested end-to-end (dry-run writes nothing; real writes keep record/index/dashboard consistent).
- Helpers: `import_csv.py` (bulk import), `check_followups.py`, `build_dashboard.py`.
- Sample data: 5 applications in `tracking/` (from `inputs/sample_applications.csv`) + `index.json`.
- Pipeline: 4 active (1 interviewing, 1 screening, 2 applied), 1 rejected; 60% response rate; 0 offers.
- Follow-ups: Datadog overdue (6/2); HubSpot & Cloudflare due 6/9; Stripe onsite 6/9, follow up 6/10.
- Dashboard at `outputs/dashboard.html`; regenerate via `report` after any tracking change.
- README.md fully professional (overview, features, Cowork + CLI usage, sample metrics, tech stack, portfolio value).
- Remaining ideas: scheduled daily reminder check; examples/ and docs/ content; follow-up email drafts.

## Running the Pipeline
1. Log: use `skills/application-logger` to add a record to `tracking/`.
2. Update: use `skills/status-updater` to change statuses and append history.
3. Remind: use `skills/reminder-engine` to flag overdue follow-ups.
4. Report: use `skills/dashboard-generator` to build `outputs/dashboard.html`.
5. Or run all steps via `skills/pipeline-orchestrator`.
