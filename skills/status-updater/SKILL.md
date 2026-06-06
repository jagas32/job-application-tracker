---
name: status-updater
description: Update the status of an existing job application (e.g., heard back, interview scheduled, rejected, offer). Use when the user reports any change in an application's state.
---

# Status Updater

## Purpose
Safely change an application's status in `tracking/` and keep an auditable history.

## Valid Statuses
`applied` → `screening` → `interviewing` → `offer` | `rejected` | `withdrawn` | `ghosted`

Backward moves are allowed but should be confirmed with the user.

## Workflow
1. Identify the record: match company/role against `tracking/index.json`. If ambiguous, list matches and ask.
2. Read the existing JSON file — never write from memory.
3. Update `status`, append to `history[]`:

```json
{"date": "2026-06-06", "status": "interviewing", "note": "Phone screen scheduled for 6/10"}
```

4. Adjust `follow_up_date`:
   - `screening`/`interviewing`: day after the scheduled event, or +5 days if unknown
   - `offer`: +2 days
   - `rejected`/`withdrawn`/`ghosted`: clear it (null)
5. Write the file, then update the matching entry in `tracking/index.json`.

## Rules
- Safe updates only: read → modify → write; never truncate `history[]`.
- One status change per history entry, always timestamped.
- If a record isn't found, offer to log it via `application-logger` instead.
- Confirm the change in one line: old status → new status.
