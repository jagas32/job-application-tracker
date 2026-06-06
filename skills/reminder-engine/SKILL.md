---
name: reminder-engine
description: Find overdue and upcoming follow-ups across all tracked applications and suggest actions. Use when the user asks what to follow up on, what's overdue, or for reminders.
---

# Reminder Engine

## Purpose
Scan `tracking/` for follow-ups due and turn them into an actionable list.

## Workflow
1. Load all `tracking/*.json` records with a non-null `follow_up_date`.
2. Bucket them:
   - **Overdue**: `follow_up_date` < today
   - **Due today**
   - **Upcoming**: within the next 7 days
3. Flag stale records: status `applied`/`screening` with no history entry in 14+ days → suggest marking `ghosted` or sending a nudge.
4. For each item, suggest a concrete action based on status:
   - `applied`: polite check-in email to the recruiter/contact
   - `screening`/`interviewing`: thank-you or status inquiry
   - `offer`: respond before the deadline
5. Output a prioritized list (overdue first). Offer to draft any follow-up email.
6. If the user accepts new follow-up dates, update records via the `status-updater` conventions (read → append history note → write).

## Rules
- Never change a record without telling the user what changed.
- Rejected/withdrawn records are never surfaced.
- Optionally offer a scheduled task ("check follow-ups every morning") — don't create one unasked.
