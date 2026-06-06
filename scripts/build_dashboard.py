#!/usr/bin/env python3
"""Build a self-contained HTML dashboard from tracking/ into outputs/dashboard.html."""
import json
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TODAY = date.today()
TERMINAL = ("rejected", "withdrawn", "ghosted")
STAGES = ["applied", "screening", "interviewing", "offer", "rejected", "withdrawn", "ghosted"]
COLORS = {"applied": "#64748b", "screening": "#f59e0b", "interviewing": "#3b82f6",
          "offer": "#22c55e", "rejected": "#ef4444", "withdrawn": "#a855f7", "ghosted": "#94a3b8"}

def d(s): return datetime.strptime(s, "%Y-%m-%d").date()

records = []
for p in sorted((ROOT / "tracking").glob("*.json")):
    if p.name != "index.json":
        records.append(json.loads(p.read_text()))

# --- metrics ---
total = len(records)
active = sum(1 for r in records if r["status"] not in TERMINAL)
responded = [r for r in records if any(h["status"] != "applied" for h in r["history"])]
response_rate = round(100 * len(responded) / total) if total else 0
offers = sum(1 for r in records if r["status"] == "offer")
ttr = [(min(d(h["date"]) for h in r["history"] if h["status"] != "applied") - d(r["date_applied"])).days
       for r in responded]
avg_ttr = round(sum(ttr) / len(ttr), 1) if ttr else None

stage_counts = {s: sum(1 for r in records if r["status"] == s) for s in STAGES}
stage_counts = {s: c for s, c in stage_counts.items() if c}

# weekly application counts
weeks = {}
for r in records:
    monday = d(r["date_applied"]) - timedelta(days=d(r["date_applied"]).weekday())
    weeks[monday] = weeks.get(monday, 0) + 1
if weeks:
    w, end = min(weeks), max(weeks)
    labels, counts = [], []
    while w <= end:
        labels.append(w.strftime("%b %d")); counts.append(weeks.get(w, 0)); w += timedelta(days=7)
else:
    labels, counts = [], []

followups = sorted([r for r in records if r.get("follow_up_date") and r["status"] not in TERMINAL],
                   key=lambda r: r["follow_up_date"])

def days_in_stage(r):
    return (TODAY - max(d(h["date"]) for h in r["history"])).days

def badge(s):
    return f'<span class="badge" style="background:{COLORS[s]}1a;color:{COLORS[s]}">{s}</span>'

fu_rows = "".join(
    f'<tr><td>{r["follow_up_date"]}</td><td>{r["company"]}</td><td>{r["role"]}</td>'
    f'<td>{badge(r["status"])}</td>'
    f'<td>{"⚠️ overdue" if d(r["follow_up_date"]) < TODAY else ("today" if d(r["follow_up_date"]) == TODAY else "upcoming")}</td></tr>'
    for r in followups) or '<tr><td colspan="5">No follow-ups scheduled</td></tr>'

all_rows = "".join(
    f'<tr><td>{r["company"]}</td><td>{r["role"]}</td><td>{badge(r["status"])}</td>'
    f'<td>{r["date_applied"]}</td><td>{days_in_stage(r)}</td>'
    f'<td>{r.get("follow_up_date") or "—"}</td></tr>'
    for r in sorted(records, key=lambda r: r["date_applied"], reverse=True)) \
    or '<tr><td colspan="6">No applications tracked yet</td></tr>'

kpis = [("Total applications", total), ("Active", active),
        ("Response rate", f"{response_rate}%"), ("Offers", offers),
        ("Avg days to response", avg_ttr if avg_ttr is not None else "—")]
kpi_html = "".join(f'<div class="card"><div class="num">{v}</div><div class="lbl">{k}</div></div>'
                   for k, v in kpis)

html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Job Application Dashboard</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
 body{{font-family:-apple-system,'Segoe UI',sans-serif;margin:0;background:#f1f5f9;color:#0f172a;padding:24px}}
 h1{{margin:0 0 4px}} .sub{{color:#64748b;margin-bottom:24px}}
 .cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:16px;margin-bottom:24px}}
 .card{{background:#fff;border-radius:12px;padding:18px;box-shadow:0 1px 3px rgba(0,0,0,.08)}}
 .num{{font-size:30px;font-weight:700}} .lbl{{color:#64748b;font-size:13px;margin-top:4px}}
 .row{{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:24px}}
 .panel{{background:#fff;border-radius:12px;padding:18px;box-shadow:0 1px 3px rgba(0,0,0,.08)}}
 .panel h2{{font-size:15px;margin:0 0 12px;color:#334155}}
 table{{width:100%;border-collapse:collapse;font-size:14px}}
 th{{text-align:left;color:#64748b;font-weight:600;padding:8px;border-bottom:2px solid #e2e8f0}}
 td{{padding:8px;border-bottom:1px solid #f1f5f9}}
 .badge{{padding:2px 10px;border-radius:999px;font-size:12px;font-weight:600}}
 @media(max-width:800px){{.row{{grid-template-columns:1fr}}}}
</style></head><body>
<h1>Job Application Dashboard</h1>
<div class="sub">Generated {TODAY} · {total} applications tracked</div>
<div class="cards">{kpi_html}</div>
<div class="row">
 <div class="panel"><h2>Pipeline by stage</h2><canvas id="stages" height="220"></canvas></div>
 <div class="panel"><h2>Applications per week</h2><canvas id="weekly" height="220"></canvas></div>
</div>
<div class="panel" style="margin-bottom:24px"><h2>Follow-ups</h2>
<table><tr><th>Due</th><th>Company</th><th>Role</th><th>Status</th><th></th></tr>{fu_rows}</table></div>
<div class="panel"><h2>All applications</h2>
<table><tr><th>Company</th><th>Role</th><th>Status</th><th>Applied</th><th>Days in stage</th><th>Next follow-up</th></tr>{all_rows}</table></div>
<script>
new Chart(document.getElementById('stages'),{{type:'bar',
 data:{{labels:{json.dumps(list(stage_counts))},datasets:[{{data:{json.dumps(list(stage_counts.values()))},
 backgroundColor:{json.dumps([COLORS[s] for s in stage_counts])},borderRadius:6}}]}},
 options:{{plugins:{{legend:{{display:false}}}},scales:{{y:{{beginAtZero:true,ticks:{{stepSize:1}}}}}}}}}});
new Chart(document.getElementById('weekly'),{{type:'line',
 data:{{labels:{json.dumps(labels)},datasets:[{{data:{json.dumps(counts)},borderColor:'#3b82f6',
 backgroundColor:'rgba(59,130,246,.15)',fill:true,tension:.3}}]}},
 options:{{plugins:{{legend:{{display:false}}}},scales:{{y:{{beginAtZero:true,ticks:{{stepSize:1}}}}}}}}}});
</script></body></html>"""

out = ROOT / "outputs" / "dashboard.html"
out.parent.mkdir(exist_ok=True)
out.write_text(html)
print(f"Wrote {out} ({len(records)} records)")
