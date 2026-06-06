---
name: pipeline-orchestrator
description: Run the full job-tracker pipeline — log new applications, apply status updates, check reminders, and regenerate the dashboard. Use when the user asks to "run the pipeline", "sync everything", or gives a batch of updates at once.
---

# Pipeline Orchestrator

## Purpose
Coordinate the other skills in the correct order so one request handles logging, updates, and reporting end-to-end.

## Pipeline Order
1. **Log** — for each new application mentioned, apply `application-logger` conventions.
2. **Update** — for each status change mentioned, apply `status-updater` conventions.
3. **Remind** — run `reminder-engine` to surface overdue/upcoming follow-ups.
4. **Report** — run `dashboard-generator` to rebuild `outputs/dashboard.html`.

## Workflow
1. Parse the user's input into actions: new applications, status changes, or "just refresh".
2. Before any writes, back up `tracking/` to `tracking/.backup-<YYYYMMDD-HHMMSS>/`.
3. Execute steps 1–4 in order; skip steps with nothing to do (dashboard always regenerates if any data changed).
4. Validate after writes: every file in `tracking/` parses as JSON and appears in `index.json`; repair index if drift is found.
5. Summarize in one short block: N logged, N updated, N follow-ups due, dashboard link.

## Rules
- Each sub-step follows its own skill's rules — this skill adds ordering, backup, and validation only.
- Stop and ask on conflicts (duplicate ids, ambiguous company match); never guess on writes.
- If any step fails, report what completed and what didn't — don't roll back silently.
- Keep only the 5 most recent backups; delete older ones.
