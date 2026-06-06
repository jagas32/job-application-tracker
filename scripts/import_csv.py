#!/usr/bin/env python3
"""Import applications from a CSV (Company,Role,Date_Applied,Status,Job_Link,Notes)
into tracking/ as one JSON record per application + index.json.

Safe-update convention: existing records are never overwritten; they are skipped
and reported so the user can resolve conflicts explicitly.
"""
import csv, json, re, sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRACKING = ROOT / "tracking"

def slug(s):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", s.lower())).strip("-")

# Optional richer history/follow-up details (keyed by record id), used when
# notes describe progression. Generic fallback below handles unknown ids.
EXTRA = {
    "stripe-data-analyst-20260511": {
        "history": [
            {"date": "2026-05-18", "status": "screening", "note": "Recruiter scheduled phone screen"},
            {"date": "2026-05-22", "status": "interviewing", "note": "Phone screen went well; onsite scheduled 2026-06-09"},
        ],
        "follow_up": "2026-06-10",  # day after onsite
        "source": "company site",
    },
    "datadog-business-intelligence-analyst-20260518": {
        "history": [
            {"date": "2026-05-28", "status": "screening", "note": "Recruiter reached out; sent availability"},
        ],
        "follow_up": "2026-06-02",  # +5 days after screening event
        "source": "company site",
    },
    "hubspot-marketing-operations-analyst-20260526": {
        "follow_up": "2026-06-09",  # per notes
        "source": "referral",
        "contacts": [{"name": "Megan T.", "email": "", "role": "referrer"}],
    },
    "shopify-data-analyst-merchant-insights-20260429": {
        "history": [
            {"date": "2026-05-08", "status": "screening", "note": "Completed take-home assignment"},
            {"date": "2026-05-20", "status": "rejected", "note": "Rejected after take-home; ask for feedback"},
        ],
        "follow_up": None,
        "source": "company site",
    },
    "cloudflare-analytics-engineer-20260602": {
        "source": "company site",
    },
}

def main(csv_path):
    TRACKING.mkdir(exist_ok=True)
    index_path = TRACKING / "index.json"
    index = json.loads(index_path.read_text()) if index_path.exists() else []
    created, skipped = [], []

    with open(csv_path, newline="") as f:
        for row in csv.DictReader(f):
            company, role = row["Company"].strip(), row["Role"].strip()
            applied = row["Date_Applied"].strip()
            status = row["Status"].strip().lower()
            rid = f"{slug(company)}-{slug(role)}-{applied.replace('-', '')}"
            path = TRACKING / f"{slug(company)}-{slug(role)}.json"
            if path.exists():
                skipped.append(path.name)
                continue
            extra = EXTRA.get(rid, {})
            history = [{"date": applied, "status": "applied", "note": "Initial application"}]
            history += extra.get("history", [])
            if history[-1]["status"] != status:  # ensure history ends at current status
                history.append({"date": applied, "status": status, "note": row.get("Notes", "")})
            if "follow_up" in extra:
                follow_up = extra["follow_up"]
            elif status in ("rejected", "withdrawn", "ghosted"):
                follow_up = None
            else:
                d = datetime.strptime(applied, "%Y-%m-%d") + timedelta(days=7)
                follow_up = d.strftime("%Y-%m-%d")
            record = {
                "id": rid,
                "company": company,
                "role": role,
                "date_applied": applied,
                "status": status,
                "source": extra.get("source", "unknown"),
                "job_link": row.get("Job_Link", "").strip(),
                "contacts": extra.get("contacts", []),
                "follow_up_date": follow_up,
                "history": history,
                "notes": row.get("Notes", "").strip(),
            }
            path.write_text(json.dumps(record, indent=2) + "\n")
            index = [e for e in index if e["id"] != rid]
            index.append({"id": rid, "company": company, "role": role,
                          "status": status, "date_applied": applied})
            created.append(path.name)

    index.sort(key=lambda e: e["date_applied"])
    index_path.write_text(json.dumps(index, indent=2) + "\n")
    print(f"Created: {len(created)}", *created, sep="\n  ")
    if skipped:
        print(f"Skipped (already exist): {len(skipped)}", *skipped, sep="\n  ")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ROOT / "inputs" / "sample_applications.csv")
