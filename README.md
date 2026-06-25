# PipelineOps Agent

AI-powered recruiting operations agent for automated pipeline data entry, anomaly detection, and reporting. Built for the GMI AgentBox marketplace.

## What It Does

PipelineOps Agent connects to staffing/ATS data sources (Indeed, CareerBuilder, Monster, Dice, Greenhouse, Lever, Bullhorn, CSV), normalizes records into a canonical recruiting funnel, detects anomalies (stale roles, missing pay rates, bottlenecks), and generates executive reports — all via natural language chat or automated sync.

**Demo mode** runs entirely on synthetic data with no credentials required.

## Quick Start

### Local Dev (Docker)

```bash
cp .env.example .env
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8080
- API docs: http://localhost:8080/docs

### Local Dev (Manual)

**Backend:**
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

Then seed demo data:
```bash
curl -X POST http://localhost:8080/demo/seed
```

## Configuration

Copy `.env.example` to `.env` and fill in the relevant fields.

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | No | SQLite (default) or Postgres connection string |
| `ALLOW_WRITES` | No | Set to `true` to enable write endpoints in production |
| `GMI_MAAS_BASE_URL` | Optional | GMI MaaS endpoint (enables LLM features) |
| `GMI_MAAS_API_KEY` | Optional | GMI MaaS API key |
| `GMI_SELECTED_MODEL` | Optional | Model ID for LLM calls |
| `LOCAL_LLM_BASE_URL` | Optional | Local LLM base URL (OpenAI-compatible, fallback) |
| `GOOGLE_SHEETS_CREDENTIALS_JSON` | Optional | Service account JSON for Sheets export |
| `GOOGLE_SHEETS_SPREADSHEET_ID` | Optional | Target spreadsheet ID |

Without GMI credentials the agent runs in **deterministic fallback mode** — all features work, LLM-powered responses are rule-based.

## GMI AgentBox Integration

The agent follows the AgentBox async job pattern:

```
POST /run  →  202 { job_id, status: "pending" }
GET  /jobs/{job_id}  →  { status: "running" | "completed" | "failed", result }
```

Supported task types for `/run`:
- `full_pipeline_refresh` — sync all sources, reconcile candidates, detect anomalies, generate report
- `detect_anomalies` — anomaly detection only
- `reconcile_candidates` — candidate deduplication only

See [docs/gmi-agentbox-deployment.md](docs/gmi-agentbox-deployment.md) for deployment steps.

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health check + AgentBox readiness |
| POST | `/run` | Submit async job (202) |
| GET | `/jobs/{id}` | Poll job status |
| POST | `/demo/seed` | Seed synthetic demo data |
| POST | `/demo/reset` | Clear all data |
| GET | `/sources` | List connected data sources |
| GET | `/metrics` | Current pipeline metrics |
| GET | `/candidates` | Candidate list (masked PII) |
| GET | `/candidates/duplicates` | Merge suggestions |
| POST | `/candidates/merge` | Merge duplicate records |
| GET | `/reports/summary` | Executive report with narrative |
| GET | `/reports/pipeline` | Funnel metrics |
| GET | `/reports/anomalies` | Open anomalies |
| PATCH | `/reports/anomalies/{id}` | Update anomaly status |
| POST | `/agent/chat` | Natural language Q&A |
| POST | `/sheets/export` | Export to Google Sheets |
| GET | `/exports/download` | Download CSV export |
| GET | `/settings/gmi` | GMI connection status |

## Running Tests

```bash
cd backend
source venv/bin/activate
pytest tests/ -v
```

65 tests covering normalization, metrics calculation, anomaly detection, and API integration.

## Security Notes

- PII (email, phone) is SHA-256 hashed for deduplication; masked in all API responses
- Secrets are read from environment variables; never hardcoded
- `ALLOW_WRITES=false` by default — safe to expose read endpoints publicly
- All demo data is synthetic; no real candidate data is stored
- LLM prompts never contain raw PII

## Architecture

```
frontend (Next.js)  →  backend (FastAPI)  →  SQLite / Postgres
                              ↓
                    connectors (demo/real ATS)
                    normalization → canonical schema
                    anomaly detection
                    GMI MaaS LLM (optional)
```

See [docs/architecture.md](docs/architecture.md) for a full diagram.
