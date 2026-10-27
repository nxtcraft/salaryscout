"""FastAPI microservice exposing remote job data."""

import json
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query

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


@app.get("/", include_in_schema=False)
def root():
    jobs = load_jobs()
    return {
        "name": "SalaryScout – Remote Tech Jobs API",
        "description": "Real-time remote tech job listings with salary data. Auto-refreshed every 12 hours.",
        "version": "1.0.0",
        "job_count": len(jobs),
        "endpoints": {
            "jobs": "/v1/jobs",
            "tag_metrics": "/v1/metrics/tags",
            "health": "/health",
            "docs": "/docs",
            "openapi": "/openapi.json",
        },
        "example_queries": [
            "/v1/jobs?tag=python&min_salary=120000",
            "/v1/jobs?tag=react&limit=10",
            "/v1/metrics/tags",
        ],
    }


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
