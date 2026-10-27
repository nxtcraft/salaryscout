# Remote Tech Jobs API – Real-Time Salary & Skills Data

[![Auto Refresh](https://img.shields.io/badge/data-auto--refreshed%20every%2012h-brightgreen)](https://github.com/nxtcraft/remote-jobs-engine/actions)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.162-009688)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> A production-ready REST API for **remote tech job listings with salary data** — auto-refreshed every 12 hours. Filter by skill tag, minimum salary, and get ranked tech skill demand metrics. Perfect for job boards, salary comparison tools, career analytics, and HR dashboards.

## What This API Does

- **Real-time remote job listings** sourced from RemoteOK (99+ jobs updated every 12 hours via GitHub Actions)
- **Normalized salary data** — parses `$120k–$160k`, `80000`, `$95,000` into structured min/max USD integers
- **Skill tag filtering** — search by `python`, `react`, `aws`, `kubernetes`, `golang`, and 100+ tech skills
- **Top skill demand ranking** — find which skills are most in demand and their average minimum salaries
- **REST API** — JSON responses, OpenAPI docs, zero rate-limit for self-hosted deployments

## Live API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Landing page with API overview |
| `GET` | `/health` | Service health + cached job count |
| `GET` | `/docs` | Interactive Swagger UI |
| `GET` | `/v1/jobs` | List remote jobs (filterable) |
| `GET` | `/v1/metrics/tags` | Top 10 in-demand skills + avg salary |

### Filter Parameters (`/v1/jobs`)

| Parameter | Type | Example | Description |
|-----------|------|---------|-------------|
| `tag` | string | `python` | Skill/tech tag filter (case-insensitive) |
| `min_salary` | integer | `100000` | Minimum annual salary in USD |
| `limit` | integer | `25` | Results per page (1–100) |

**Example requests:**
```
GET /v1/jobs?tag=python&min_salary=120000&limit=10
GET /v1/jobs?tag=react
GET /v1/metrics/tags
```

## Quick Start (Local)

```bash
# Clone the repository
git clone https://github.com/nxtcraft/remote-jobs-engine.git
cd remote-jobs-engine

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Fetch latest job data
python pipeline.py

# Start the API server
uvicorn main:app --reload --port 8000
```

Open **http://localhost:8000/docs** for interactive API docs.

## Run Tests

```bash
pytest -v
```

All 12 tests cover salary string parsing and API endpoint behavior.

## Deploy in 1 Click

### Render (Recommended — Free Tier)

1. Fork this repo on GitHub
2. Go to [render.com](https://render.com) → **New Web Service** → connect your fork
3. Render auto-detects `render.yaml` — click **Deploy**

### Docker

```bash
docker build -t remote-jobs-engine .
docker run -p 8000:8000 remote-jobs-engine
```

### Heroku / Railway

Both platforms read `Procfile` automatically:
```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

## Publish as a Monetized API

### RapidAPI
1. Deploy to Render/Railway/Heroku to get a public URL
2. Visit [rapidapi.com/provider](https://rapidapi.com/provider) → Add New API
3. Paste your public base URL → import spec from `/openapi.json`
4. Set pricing tiers (freemium / per-call)

### Zuplo
1. Create a new Zuplo project at [zuplo.com](https://zuplo.com)
2. Import from OpenAPI → paste your `/openapi.json` URL
3. Add rate-limiting and API key policies in the Zuplo dashboard

## Architecture

```
RemoteOK API
    │
    ▼
pipeline.py ──► data/latest_jobs.json
    │                   │
    ▼                   ▼
GitHub Actions      main.py (FastAPI)
(every 12h)             │
                        ▼
                 /v1/jobs  /v1/metrics/tags
```

## Data Auto-Refresh

`.github/workflows/ingest.yml` runs `python pipeline.py` on a cron schedule (`0 */12 * * *`) and commits the refreshed `data/latest_jobs.json` with message `chore: auto-refresh remote data [skip ci]`.

## Tech Stack

- **[FastAPI](https://fastapi.tiangolo.com/)** — modern Python web framework with auto-generated OpenAPI docs
- **[httpx](https://www.python-httpx.org/)** — async HTTP client with retry logic
- **[Pydantic](https://docs.pydantic.dev/)** — data validation and serialization
- **[GitHub Actions](https://docs.github.com/en/actions)** — scheduled CI/CD for data pipeline
- **Python 3.11+**

## Use Cases

- Remote job boards and aggregators
- Salary comparison and benchmarking tools
- Tech skills demand analytics
- Career coaching platforms
- HR market research dashboards
- Developer tools and browser extensions

## License

MIT — free to use, fork, and monetize.
