#!/usr/bin/env python3
"""Reminder engine: bucket follow-ups into overdue / due today / upcoming (7d),
and flag stale applied/screening records (no history activity in 14+ days)."""
import json
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TODAY = date.today()

def d(s): return datetime.strptime(s, "%Y-%m-%d").date()

overdue, due_today, upcoming, stale = [], [], [], []
for p in sorted((ROOT / "tracking").glob("*.json")):
    if p.name == "index.json":
        continue
    r = json.loads(p.read_text())
    if r["status"] in ("rejected", "withdrawn"):
        continue
    label = f'{r["company"]} — {r["role"]} [{r["status"]}]'
    fu = r.get("follow_up_date")
    if fu:
        fud = d(fu)
        if fud < TODAY: overdue.append((fud, label))
        elif fud == TODAY: due_today.append((fud, label))
        elif fud <= TODAY + timedelta(days=7): upcoming.append((fud, label))
    last = max(d(h["date"]) for h in r["history"])
    if r["status"] in ("applied", "screening") and (TODAY - last).days >= 14:
        stale.append((last, label))

for title, items in [("OVERDUE", overdue), ("DUE TODAY", due_today),
                     ("UPCOMING (7 days)", upcoming), ("STALE (14+ days quiet)", stale)]:
    print(f"{title}: {len(items)}")
    for dt, label in sorted(items):
        print(f"  {dt}  {label}")
