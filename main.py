"""FastAPI microservice exposing remote job data."""

import json
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse, HTMLResponse

DATA_FILE = Path("data/latest_jobs.json")

app = FastAPI(
    title="SalaryScout – Remote Tech Jobs API",
    description=(
        "Real-time remote tech job listings with normalized salary data. "
        "Filter by skill tag (python, react, aws, kubernetes), minimum salary in USD, "
        "and get ranked skill demand metrics. Auto-refreshed every 12 hours."
    ),
    version="1.0.0",
    contact={"name": "SalaryScout", "url": "https://github.com/nxtcraft/salaryscout"},
    license_info={"name": "MIT"},
)


@app.api_route("/", methods=["GET", "HEAD"], include_in_schema=False)
def root():
    jobs = load_jobs()
    job_count = len(jobs)
    salary_jobs = [j for j in jobs if j.get("salary", {}).get("min")]
    avg_salary = int(sum(j["salary"]["min"] for j in salary_jobs) / len(salary_jobs)) if salary_jobs else 0

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<meta name="description" content="SalaryScout — Real-time remote tech job listings with normalized salary data. Filter by skill, salary, and get market insights. Auto-refreshed every 12 hours."/>
<meta name="keywords" content="remote jobs API, tech jobs, salary data, python jobs, react jobs, remote work, developer jobs"/>
<title>SalaryScout – Remote Tech Jobs API</title>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet"/>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Inter',sans-serif;background:#0f1117;color:#e2e8f0;line-height:1.6}}
.hero{{background:linear-gradient(135deg,#1e2a3a 0%,#0f1117 60%);padding:80px 24px 60px;text-align:center;border-bottom:1px solid #1e293b}}
.badge{{display:inline-block;background:#10b981;color:#fff;font-size:12px;font-weight:600;padding:4px 12px;border-radius:20px;margin-bottom:20px;letter-spacing:.5px}}
h1{{font-size:clamp(2rem,5vw,3.5rem);font-weight:700;background:linear-gradient(135deg,#38bdf8,#818cf8);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:16px}}
.subtitle{{font-size:1.1rem;color:#94a3b8;max-width:560px;margin:0 auto 40px}}
.cta-group{{display:flex;gap:12px;justify-content:center;flex-wrap:wrap}}
.btn{{padding:12px 28px;border-radius:8px;font-size:15px;font-weight:600;text-decoration:none;transition:all .2s}}
.btn-primary{{background:linear-gradient(135deg,#38bdf8,#818cf8);color:#fff}}
.btn-primary:hover{{opacity:.9;transform:translateY(-1px)}}
.btn-secondary{{background:#1e293b;color:#e2e8f0;border:1px solid #334155}}
.btn-secondary:hover{{background:#263548}}
.stats{{display:flex;justify-content:center;gap:40px;padding:40px 24px;flex-wrap:wrap;border-bottom:1px solid #1e293b}}
.stat{{text-align:center}}
.stat-number{{font-size:2rem;font-weight:700;color:#38bdf8}}
.stat-label{{font-size:13px;color:#64748b;margin-top:4px}}
.section{{max-width:900px;margin:0 auto;padding:60px 24px}}
.section-title{{font-size:1.4rem;font-weight:600;margin-bottom:24px;color:#f1f5f9}}
.endpoints{{display:grid;gap:12px}}
.endpoint{{background:#1e293b;border:1px solid #334155;border-radius:10px;padding:18px 20px;display:flex;align-items:flex-start;gap:14px}}
.method{{background:#10b981;color:#fff;font-size:11px;font-weight:700;padding:3px 8px;border-radius:4px;flex-shrink:0;margin-top:2px}}
.ep-path{{font-family:monospace;font-size:14px;color:#38bdf8;font-weight:600}}
.ep-desc{{font-size:13px;color:#94a3b8;margin-top:3px}}
.code-block{{background:#1e293b;border:1px solid #334155;border-radius:10px;padding:20px;margin-bottom:16px}}
.code-block pre{{font-family:monospace;font-size:13px;color:#a5f3fc;overflow-x:auto;white-space:pre-wrap}}
.code-label{{font-size:11px;color:#64748b;margin-bottom:8px;text-transform:uppercase;letter-spacing:.5px}}
.plans{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:16px}}
.plan{{background:#1e293b;border:1px solid #334155;border-radius:10px;padding:20px;text-align:center}}
.plan.featured{{border-color:#38bdf8}}
.plan-name{{font-size:13px;font-weight:600;color:#64748b;margin-bottom:8px}}
.plan-price{{font-size:1.8rem;font-weight:700;color:#f1f5f9}}
.plan-price span{{font-size:14px;font-weight:400;color:#64748b}}
.plan-limit{{font-size:12px;color:#94a3b8;margin-top:8px}}
footer{{text-align:center;padding:40px 24px;border-top:1px solid #1e293b;color:#475569;font-size:13px}}
footer a{{color:#38bdf8;text-decoration:none}}
</style>
</head>
<body>
<div class="hero">
  <div class="badge">LIVE API</div>
  <h1>SalaryScout</h1>
  <p class="subtitle">Real-time remote tech job listings with normalized salary data. Filter by skill, salary range, and get market insights — auto-refreshed every 12 hours.</p>
  <div class="cta-group">
    <a href="https://rapidapi.com/PradeepKumarKesharwani/api/salaryscout" class="btn btn-primary" target="_blank">Get API Key — Free</a>
    <a href="/docs" class="btn btn-secondary">View Docs</a>
  </div>
</div>

<div class="stats">
  <div class="stat"><div class="stat-number">{job_count}</div><div class="stat-label">Live Jobs</div></div>
  <div class="stat"><div class="stat-number">${avg_salary:,}</div><div class="stat-label">Avg Min Salary</div></div>
  <div class="stat"><div class="stat-number">12h</div><div class="stat-label">Refresh Interval</div></div>
  <div class="stat"><div class="stat-number">3</div><div class="stat-label">Endpoints</div></div>
</div>

<div class="section">
  <h2 class="section-title">Endpoints</h2>
  <div class="endpoints">
    <div class="endpoint">
      <span class="method">GET</span>
      <div><div class="ep-path">/v1/jobs</div><div class="ep-desc">List remote tech jobs. Filter by tag (python, react, aws) and minimum salary in USD.</div></div>
    </div>
    <div class="endpoint">
      <span class="method">GET</span>
      <div><div class="ep-path">/v1/metrics/tags</div><div class="ep-desc">Top 10 in-demand skills with job count and average minimum salary.</div></div>
    </div>
    <div class="endpoint">
      <span class="method">GET</span>
      <div><div class="ep-path">/health</div><div class="ep-desc">Service health check with live job count.</div></div>
    </div>
  </div>
</div>

<div class="section" style="padding-top:0">
  <h2 class="section-title">Example Requests</h2>
  <div class="code-block">
    <div class="code-label">Python jobs with $120k+ salary</div>
    <pre>GET /v1/jobs?tag=python&min_salary=120000&limit=10</pre>
  </div>
  <div class="code-block">
    <div class="code-label">Top skills by demand & salary</div>
    <pre>GET /v1/metrics/tags</pre>
  </div>
  <div class="code-block">
    <div class="code-label">React jobs (latest 25)</div>
    <pre>GET /v1/jobs?tag=react</pre>
  </div>
</div>

<div class="section" style="padding-top:0">
  <h2 class="section-title">Pricing Plans</h2>
  <div class="plans">
    <div class="plan featured">
      <div class="plan-name">BASIC</div>
      <div class="plan-price">$0<span>/mo</span></div>
      <div class="plan-limit">500,000 req/month</div>
    </div>
    <div class="plan">
      <div class="plan-name">PRO</div>
      <div class="plan-price">$9.99<span>/mo</span></div>
      <div class="plan-limit">Unlimited</div>
    </div>
    <div class="plan">
      <div class="plan-name">ULTRA</div>
      <div class="plan-price">$29.99<span>/mo</span></div>
      <div class="plan-limit">Unlimited</div>
    </div>
    <div class="plan">
      <div class="plan-name">MEGA</div>
      <div class="plan-price">$99.99<span>/mo</span></div>
      <div class="plan-limit">Unlimited</div>
    </div>
  </div>
</div>

<footer>
  <p>Built by <a href="https://github.com/nxtcraft" target="_blank">nxtcraft</a> · Data from <a href="https://remoteok.com" target="_blank">RemoteOK</a> · <a href="/docs" target="_blank">API Docs</a> · <a href="https://github.com/nxtcraft/salaryscout" target="_blank">GitHub</a></p>
</footer>
</body>
</html>"""
    return HTMLResponse(content=html)


def load_jobs() -> list[dict]:
    if not DATA_FILE.exists():
        return []
    with open(DATA_FILE, encoding="utf-8") as f:
        return json.load(f)


@app.get("/health")
def health():
    jobs = load_jobs()
    return {"status": "ok", "job_count": len(jobs)}


@app.get("/v1/jobs")
def get_jobs(
    tag: Optional[str] = Query(None, description="Filter by tag (case-insensitive)"),
    min_salary: Optional[int] = Query(None, description="Minimum salary filter"),
    limit: int = Query(25, ge=1, le=100, description="Max results (1-100)"),
):
    jobs = load_jobs()
    if not jobs and not DATA_FILE.exists():
        raise HTTPException(status_code=503, detail="Data not yet ingested. Run pipeline.py first.")

    if tag:
        tag_lower = tag.lower()
        jobs = [j for j in jobs if tag_lower in j.get("tags", [])]

    if min_salary is not None:
        jobs = [
            j for j in jobs
            if j.get("salary", {}).get("min") is not None
            and j["salary"]["min"] >= min_salary
        ]

    return {"total": len(jobs), "results": jobs[:limit]}


@app.get("/v1/metrics/tags")
def tag_metrics():
    jobs = load_jobs()
    tag_data: dict[str, dict] = {}

    for job in jobs:
        sal_min = job.get("salary", {}).get("min")
        for tag in job.get("tags", []):
            if tag not in tag_data:
                tag_data[tag] = {"count": 0, "salary_sum": 0, "salary_count": 0}
            tag_data[tag]["count"] += 1
            if sal_min is not None:
                tag_data[tag]["salary_sum"] += sal_min
                tag_data[tag]["salary_count"] += 1

    ranked = sorted(tag_data.items(), key=lambda x: x[1]["count"], reverse=True)[:10]

    return {
        "top_tags": [
            {
                "tag": tag,
                "job_count": stats["count"],
                "avg_min_salary": (
                    int(stats["salary_sum"] / stats["salary_count"])
                    if stats["salary_count"]
                    else None
                ),
            }
            for tag, stats in ranked
        ]
    }
