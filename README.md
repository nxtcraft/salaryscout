# Remote Tech & Compensation Data Engine

A production-ready micro-service that ingests remote job listings from RemoteOK, normalizes salary data, and exposes a clean REST API.

## Quick Start

```bash
# 1. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Ingest latest job data
python pipeline.py

# 4. Start the API server
uvicorn main:app --reload --port 8000
```

Open API docs at: http://localhost:8000/docs

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Service health + cached job count |
| GET | `/v1/jobs` | List jobs with optional filters |
| GET | `/v1/metrics/tags` | Top 10 skills + avg salary |

### Query Parameters for `/v1/jobs`

| Param | Type | Description |
|-------|------|-------------|
| `tag` | string | Filter by skill tag (case-insensitive) |
| `min_salary` | int | Minimum salary in USD |
| `limit` | int | Results per page (1–100, default 25) |

## Running Tests

```bash
pytest -v
```

## Deployment

### Render (1-click)

1. Fork this repo on GitHub.
2. Go to [render.com](https://render.com) → New → Web Service → connect your fork.
3. Render auto-detects `render.yaml` — click **Deploy**.

### Docker

```bash
docker build -t remote-jobs-engine .
docker run -p 8000:8000 remote-jobs-engine
```

### Heroku / Railway

Uses `Procfile` automatically. Set `PORT` env var if needed.

## Publishing to RapidAPI or Zuplo

1. Deploy the service to Render, Railway, or any public URL.
2. **RapidAPI**: Go to [rapidapi.com/developer](https://rapidapi.com/provider) → Add New API → enter your public base URL → import OpenAPI spec from `/openapi.json`.
3. **Zuplo**: Create a new project → import from URL → paste your `/openapi.json` URL → configure rate-limiting and API keys in the Zuplo dashboard.

## Data Auto-Refresh

A GitHub Actions workflow (`.github/workflows/ingest.yml`) runs every 12 hours to re-fetch jobs and commit the updated `data/latest_jobs.json` automatically.
