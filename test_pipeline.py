"""Tests for pipeline salary parser and FastAPI endpoints."""

import json
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from pipeline import parse_salary_str
from main import app

client = TestClient(app)

SAMPLE_JOBS = [
    {
        "id": "1",
        "role": "Senior Engineer",
        "company": "Acme",
        "location": "Worldwide",
        "tags": ["python", "aws"],
        "salary": {"min": 120000, "max": 160000, "currency": "USD"},
        "apply_url": "https://example.com/job/1",
        "source_date": "2026-10-01T00:00:00+00:00",
        "ingested_at": "2026-10-27T00:00:00+00:00",
    }
]


@pytest.fixture(autouse=True)
def seed_data_file(tmp_path, monkeypatch):
    """Seed a temporary data file for API tests."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    data_file = data_dir / "latest_jobs.json"
    data_file.write_text(json.dumps(SAMPLE_JOBS), encoding="utf-8")
    monkeypatch.setattr("main.DATA_FILE", data_file)


# --- Salary parser tests ---

def test_parse_range_k():
    result = parse_salary_str("$120k - $160k")
    assert result["min"] == 120000
    assert result["max"] == 160000
    assert result["currency"] == "USD"


def test_parse_single_k():
    result = parse_salary_str("$90k")
    assert result["min"] == 90000
    assert result["max"] is None
    assert result["currency"] == "USD"


def test_parse_empty_string():
    result = parse_salary_str("")
    assert result == {"min": None, "max": None, "currency": None}


def test_parse_none():
    result = parse_salary_str(None)
    assert result == {"min": None, "max": None, "currency": None}


def test_parse_dollar_integer():
    result = parse_salary_str("$95,000")
    assert result["min"] == 95000


# --- API endpoint tests ---

def test_health_returns_200():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["job_count"] == 1


def test_jobs_returns_200():
    resp = client.get("/v1/jobs")
    assert resp.status_code == 200
    data = resp.json()
    assert "results" in data
    assert len(data["results"]) == 1


def test_jobs_tag_filter():
    resp = client.get("/v1/jobs?tag=python")
    assert resp.status_code == 200
    assert resp.json()["total"] == 1


def test_jobs_tag_filter_no_match():
    resp = client.get("/v1/jobs?tag=golang")
    assert resp.status_code == 200
    assert resp.json()["total"] == 0


def test_jobs_min_salary_filter():
    resp = client.get("/v1/jobs?min_salary=100000")
    assert resp.status_code == 200
    assert resp.json()["total"] == 1


def test_jobs_min_salary_filter_no_match():
    resp = client.get("/v1/jobs?min_salary=200000")
    assert resp.status_code == 200
    assert resp.json()["total"] == 0


def test_tag_metrics_returns_200():
    resp = client.get("/v1/metrics/tags")
    assert resp.status_code == 200
    assert "top_tags" in resp.json()
