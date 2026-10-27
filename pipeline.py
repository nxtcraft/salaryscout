"""Remote job ingestion pipeline - fetches from RemoteOK and normalizes data."""

import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

DATA_DIR = Path("data")
OUTPUT_FILE = DATA_DIR / "latest_jobs.json"
SOURCE_URL = "https://remoteok.com/api"
USER_AGENT = "RemoteJobsEngine/1.0 (+https://github.com/remote-jobs-engine)"
MAX_RETRIES = 3
RETRY_DELAY = 2.0


def parse_salary_str(salary_str: str | None) -> dict:
    """Parse salary string variants into normalized min/max USD integers."""
    empty = {"min": None, "max": None, "currency": None}
    if not salary_str or not salary_str.strip():
        return empty

    s = salary_str.replace(",", "").replace(" ", "")
    # Match patterns like $120k, 120k, $95000, 95000, with optional range
    pattern = r"(\$?)(\d+(?:\.\d+)?)(k?)\s*(?:[-–to]+\s*(\$?)(\d+(?:\.\d+)?)(k?))?"
    match = re.search(pattern, s, re.IGNORECASE)
    if not match:
        return empty

    currency = "USD" if match.group(1) or "$" in salary_str else "USD"

    def to_int(num_str: str, has_k: str) -> int:
        val = float(num_str)
        if has_k.lower() == "k":
            val *= 1000
        return int(val)

    sal_min = to_int(match.group(2), match.group(3))
    sal_max = None
    if match.group(5):
        sal_max = to_int(match.group(5), match.group(6))

    return {"min": sal_min, "max": sal_max, "currency": currency}


def fetch_jobs(retries: int = MAX_RETRIES) -> list[dict]:
    """Fetch job listings from RemoteOK API with retry logic."""
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    for attempt in range(1, retries + 1):
        try:
            with httpx.Client(timeout=20.0, follow_redirects=True) as client:
                resp = client.get(SOURCE_URL, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                # index 0 is always a disclaimer/metadata object, skip it
                return [item for item in data if isinstance(item, dict) and item.get("id")]
        except (httpx.TimeoutException, httpx.NetworkError) as exc:
            print(f"[attempt {attempt}/{retries}] Network error: {exc}")
            if attempt < retries:
                time.sleep(RETRY_DELAY * attempt)
        except httpx.HTTPStatusError as exc:
            print(f"HTTP error {exc.response.status_code}: {exc}")
            break
        except Exception as exc:
            print(f"Unexpected error: {exc}")
            break
    return []


def sanitize_tags(raw_tags) -> list[str]:
    if not raw_tags:
        return []
    if isinstance(raw_tags, str):
        raw_tags = [raw_tags]
    return [str(t).lower().strip() for t in raw_tags if t]


def normalize_job(raw: dict) -> dict | None:
    """Extract and normalize a single job record."""
    job_id = raw.get("id") or raw.get("slug")
    if not job_id:
        return None

    salary_raw = raw.get("salary") or ""
    # RemoteOK sometimes provides salary_min/salary_max as separate fields
    sal_min_raw = raw.get("salary_min")
    sal_max_raw = raw.get("salary_max")

    if sal_min_raw or sal_max_raw:
        salary = {
            "min": int(sal_min_raw) if sal_min_raw else None,
            "max": int(sal_max_raw) if sal_max_raw else None,
            "currency": "USD",
        }
    else:
        salary = parse_salary_str(salary_raw)

    date_str = raw.get("date") or raw.get("epoch")
    if date_str and str(date_str).isdigit():
        try:
            source_date = datetime.fromtimestamp(int(date_str), tz=timezone.utc).isoformat()
        except (ValueError, OSError):
            source_date = date_str
    else:
        source_date = date_str

    return {
        "id": str(job_id),
        "role": (raw.get("position") or raw.get("role") or "").strip(),
        "company": (raw.get("company") or "").strip(),
        "location": (raw.get("location") or "Worldwide").strip(),
        "tags": sanitize_tags(raw.get("tags")),
        "salary": salary,
        "apply_url": raw.get("url") or raw.get("apply_url") or "",
        "source_date": source_date,
        "ingested_at": datetime.now(tz=timezone.utc).isoformat(),
    }


def run():
    print(f"[{datetime.now().isoformat()}] Fetching jobs from {SOURCE_URL}...")
    raw_jobs = fetch_jobs()
    print(f"  Fetched {len(raw_jobs)} raw records.")

    jobs = []
    for raw in raw_jobs:
        normalized = normalize_job(raw)
        if normalized:
            jobs.append(normalized)

    print(f"  Normalized {len(jobs)} valid job records.")

    DATA_DIR.mkdir(exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)

    print(f"  Saved to {OUTPUT_FILE}")
    return jobs


if __name__ == "__main__":
    run()
