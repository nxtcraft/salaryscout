"""FastAPI microservice exposing remote job data."""

import json
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query

DATA_FILE = Path("data/latest_jobs.json")

app = FastAPI(
    title="Remote Jobs API",
    description="Aggregated remote tech job listings with salary data.",
    version="1.0.0",
)


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
