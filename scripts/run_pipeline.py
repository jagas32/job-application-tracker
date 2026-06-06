#!/usr/bin/env python3
"""Job Application Tracker — pipeline CLI.

Usage:
  python3 scripts/run_pipeline.py add --company "Acme" --role "Data Analyst" [options]
  python3 scripts/run_pipeline.py update --company "Acme" --status interviewing [options]
  python3 scripts/run_pipeline.py remind
  python3 scripts/run_pipeline.py report
  python3 scripts/run_pipeline.py all          # remind + report

Global flag:
  --dry-run   show what would change without writing anything

Conventions (see CLAUDE.md): one JSON per application in tracking/, append-only
history, safe read-modify-write updates, index.json kept in sync.
"""
import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRACKING = ROOT / "tracking"
INDEX = TRACKING / "index.json"
STATUSES = ["applied", "screening", "interviewing", "offer", "rejected", "withdrawn", "ghosted"]
TERMINAL = ("rejected", "withdrawn", "ghosted")
TODAY = datetime.now().strftime("%Y-%m-%d")


def slug(s: str) -> str:
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", s.lower())).strip("-")


def load_index() -> list:
    return json.loads(INDEX.read_text()) if INDEX.exists() else []


def save_index(index: list, dry: bool) -> None:
    if dry:
        return
    index.sort(key=lambda e: e["date_applied"])
    INDEX.write_text(json.dumps(index, indent=2) + "\n")


def find_record(company: str, role: str | None) -> Path:
    """Resolve a record file by company (and optional role); exit on 0 or 2+ matches."""
    matches = [e for e in load_index() if slug(company) in slug(e["company"])]
    if role:
        matches = [e for e in matches if slug(role) in slug(e["role"])]
    if not matches:
        sys.exit(f"No record found for company '{company}'"
                 + (f" role '{role}'" if role else "") + ". Use 'add' to log it first.")
    if len(matches) > 1:
        opts = "\n  ".join(f'{e["company"]} — {e["role"]} [{e["status"]}]' for e in matches)
        sys.exit(f"Ambiguous match — narrow with --role:\n  {opts}")
    e = matches[0]
    return TRACKING / f'{slug(e["company"])}-{slug(e["role"])}.json'


def default_follow_up(status: str, base: str) -> str | None:
    if status in TERMINAL:
        return None
    days = {"applied": 7, "screening": 5, "interviewing": 5, "offer": 2}[status]
    return (datetime.strptime(base, "%Y-%m-%d") + timedelta(days=days)).strftime("%Y-%m-%d")


# ---------------------------------------------------------------- commands ---

def cmd_add(args) -> bool:
    path = TRACKING / f"{slug(args.company)}-{slug(args.role)}.json"
    if path.exists():
        sys.exit(f"Record already exists: tracking/{path.name} — use 'update' instead.")
    date = args.date or TODAY
    record = {
        "id": f"{slug(args.company)}-{slug(args.role)}-{date.replace('-', '')}",
        "company": args.company,
        "role": args.role,
        "date_applied": date,
        "status": "applied",
        "source": args.source,
        "job_link": args.link,
        "contacts": [],
        "follow_up_date": args.follow_up or default_follow_up("applied", date),
        "history": [{"date": date, "status": "applied", "note": args.notes or "Initial application"}],
        "notes": args.notes,
    }
    print(f"{'[dry-run] Would create' if args.dry_run else 'Created'} tracking/{path.name}")
    print(json.dumps(record, indent=2))
    if not args.dry_run:
        TRACKING.mkdir(exist_ok=True)
        path.write_text(json.dumps(record, indent=2) + "\n")
        index = load_index()
        index.append({"id": record["id"], "company": args.company, "role": args.role,
                      "status": "applied", "date_applied": date})
        save_index(index, args.dry_run)
    return not args.dry_run


def cmd_update(args) -> bool:
    path = find_record(args.company, args.role)
    record = json.loads(path.read_text())  # read-modify-write, never from memory
    old = record["status"]
    if old == args.status:
        sys.exit(f"{record['company']} — {record['role']} is already '{old}'.")
    if STATUSES.index(args.status) < STATUSES.index(old) and args.status not in TERMINAL:
        print(f"Note: backward move {old} → {args.status}")
    entry = {"date": TODAY, "status": args.status,
             "note": args.note or f"Status changed: {old} → {args.status}"}
    record["status"] = args.status
    record["history"].append(entry)
    record["follow_up_date"] = args.follow_up or default_follow_up(args.status, TODAY)
    if args.note:
        record["notes"] = args.note

    print(f"{'[dry-run] Would update' if args.dry_run else 'Updated'} "
          f"{record['company']} — {record['role']}: {old} → {args.status}")
    print(f"  history += {json.dumps(entry)}")
    print(f"  follow_up_date = {record['follow_up_date']}")
    if not args.dry_run:
        path.write_text(json.dumps(record, indent=2) + "\n")
        index = load_index()
        for e in index:
            if e["id"] == record["id"]:
                e["status"] = args.status
        save_index(index, args.dry_run)
    return not args.dry_run


def cmd_remind(args) -> bool:
    subprocess.run([sys.executable, str(ROOT / "scripts" / "check_followups.py")], check=True)
    return False  # read-only


def cmd_report(args) -> bool:
    if args.dry_run:
        n = len(list(TRACKING.glob("*.json"))) - (1 if INDEX.exists() else 0)
        print(f"[dry-run] Would regenerate outputs/dashboard.html from {n} records")
        return False
    subprocess.run([sys.executable, str(ROOT / "scripts" / "build_dashboard.py")], check=True)
    return False


def cmd_all(args) -> bool:
    print("== Reminders ==")
    cmd_remind(args)
    print("\n== Dashboard ==")
    cmd_report(args)
    return False


def main() -> None:
    p = argparse.ArgumentParser(description="Job Application Tracker pipeline")
    p.add_argument("--dry-run", action="store_true", help="preview changes without writing")
    sub = p.add_subparsers(dest="command", required=True)

    a = sub.add_parser("add", help="log a new application")
    a.add_argument("--company", required=True)
    a.add_argument("--role", required=True)
    a.add_argument("--date", help="YYYY-MM-DD (default: today)")
    a.add_argument("--source", default="unknown")
    a.add_argument("--link", default="", help="job posting URL")
    a.add_argument("--notes", default="")
    a.add_argument("--follow-up", help="YYYY-MM-DD (default: +7 days)")
    a.set_defaults(func=cmd_add)

    u = sub.add_parser("update", help="change an application's status")
    u.add_argument("--company", required=True)
    u.add_argument("--role", help="disambiguate if multiple roles at one company")
    u.add_argument("--status", required=True, choices=STATUSES)
    u.add_argument("--note", help="history note")
    u.add_argument("--follow-up", help="YYYY-MM-DD (default: per-status rule)")
    u.set_defaults(func=cmd_update)

    sub.add_parser("remind", help="show overdue/upcoming follow-ups").set_defaults(func=cmd_remind)
    sub.add_parser("report", help="rebuild outputs/dashboard.html").set_defaults(func=cmd_report)
    sub.add_parser("all", help="remind + report").set_defaults(func=cmd_all)

    args = p.parse_args()
    wrote = args.func(args)
    if wrote and args.command in ("add", "update"):
        print("\nTracking changed — run 'report' to refresh the dashboard.")


if __name__ == "__main__":
    main()
