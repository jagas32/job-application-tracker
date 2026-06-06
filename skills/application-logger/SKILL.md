---
name: application-logger
description: Log a new job application as a structured JSON record in tracking/. Use when the user says they applied to a job, pastes a job posting, or asks to add/log an application.
---

# Application Logger

## Purpose
Create one JSON record per application in `tracking/` and register it in `tracking/index.json`.

## Workflow
1. Extract from the user's input (or job posting): company, role, source (LinkedIn, referral, company site, etc.), date applied (default: today), contacts, notes.
2. Generate `id` as `<company-slug>-<role-slug>-<YYYYMMDD>`.
3. Write `tracking/<company-slug>-<role-slug>.json`:

```json
{
  "id": "acme-data-analyst-20260606",
  "company": "Acme Corp",
  "role": "Data Analyst",
  "date_applied": "2026-06-06",
  "status": "applied",
  "source": "LinkedIn",
  "contacts": [{"name": "", "email": "", "role": ""}],
  "follow_up_date": "2026-06-13",
  "history": [{"date": "2026-06-06", "status": "applied", "note": "Initial application"}],
  "notes": ""
}
```

4. Default `follow_up_date` = date_applied + 7 days.
5. Append `{id, company, role, status, date_applied}` to `tracking/index.json` (create as `[]` if missing).

## Rules
- If a record with the same id exists, ask before overwriting — never clobber silently.
- Ask for company and role if missing; everything else may default to empty.
- Privacy: do not store salary expectations or personal identifiers beyond contact name/email.
- Confirm to the user what was logged in one line.
