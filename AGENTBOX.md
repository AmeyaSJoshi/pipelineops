# PipelineOps Agent — AgentBox Deployment Guide

## Overview

PipelineOps Agent is an AI-powered recruiting operations tool that ingests data from ATS platforms, normalizes pipeline stages, detects anomalies, and generates manager reports. It runs as a FastAPI backend + Next.js frontend, deployable on GMI AgentBox.

## Architecture

```
[ATS Sources] ──► [Connector Layer] ──► [FastAPI Backend] ──► [Next.js Frontend]
 Greenhouse             normalize()         /reports               Dashboard
 Lever                  canonicalize()      /candidates            Anomalies
 Bullhorn               reconcile()         /agent/chat            Chat
 CSV / Excel            detect_anomalies()  /run (async jobs)      Reports
```

## AgentBox Async Job Pattern

All long-running operations use the AgentBox job pattern:

```
POST /run  { "task": "full_pipeline_refresh" }
  → { "job_id": "abc123", "status": "pending" }

GET /jobs/abc123
  → { "status": "running", "progress": 0.65, "result": { "step": "Detecting anomalies" } }

GET /jobs/abc123
  → { "status": "completed", "progress": 1.0, "result": { "metrics": {...}, "anomalies": [...] } }
```

Supported tasks:
- `full_pipeline_refresh` — full end-to-end sync + analysis
- `sync_all_sources` — sync all configured live connectors
- `detect_anomalies` — run anomaly detection only
- `reconcile_candidates` — find duplicate candidates only
- `generate_manager_report` — generate LLM narrative report

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | Yes | SQLite (dev) or Postgres URL |
| `ENCRYPTION_KEY` | Yes | 32-byte hex key for encrypting credentials at rest |
| `GMI_MAAS_BASE_URL` | For AI | GMI MaaS endpoint |
| `GMI_MAAS_API_KEY` | For AI | GMI MaaS API key |
| `GREENHOUSE_API_KEY` | For Greenhouse | Harvest API key |
| `LEVER_API_KEY` | For Lever | Data API key |
| `BULLHORN_CLIENT_ID` | For Bullhorn | OAuth client ID |
| `BULLHORN_CLIENT_SECRET` | For Bullhorn | OAuth client secret |
| `BULLHORN_USERNAME` | For Bullhorn | Service account username |
| `BULLHORN_PASSWORD` | For Bullhorn | Used once for token, never persisted |
| `GOOGLE_SHEETS_CREDENTIALS_JSON` | For Sheets | Service account JSON (single-line) |
| `GOOGLE_SHEETS_SPREADSHEET_ID` | For Sheets | Target spreadsheet ID |

## Connector Status at a Glance

| Source | Status | Notes |
|---|---|---|
| Greenhouse | ✅ Live | Requires `GREENHOUSE_API_KEY` |
| Lever | ✅ Live | Requires `LEVER_API_KEY` |
| Bullhorn | ✅ Live | Requires OAuth credentials |
| Google Sheets | ✅ Live | Requires service account JSON |
| CSV / Excel | ✅ Ready | File upload, no credentials needed |
| Indeed | 🚫 Blocked | No official public API — see CONNECTOR_AUDIT.md |
| CareerBuilder | 🚫 Blocked | No official public API — see CONNECTOR_AUDIT.md |
| Monster | 🚫 Blocked | No official public API — see CONNECTOR_AUDIT.md |
| Dice | 🚫 Blocked | No official public API — see CONNECTOR_AUDIT.md |

## Quick Start

```bash
# Backend
cd backend
pip install -r requirements.txt
cp ../.env.example .env  # fill in your keys
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

# Frontend
cd frontend
npm install
npm run dev
```

## Docker

```bash
docker-compose up --build
```

The compose file starts:
- `backend` on port 8080
- `frontend` on port 3000

## Health Check

```
GET /health → { "status": "ok", "agentbox_ready": true, "gmi_maas_configured": true/false }
```

## First Run

1. Start the backend and frontend
2. Open `http://localhost:3000`
3. Navigate to `/sources` → "Seed Demo Data" to populate with sample data
4. Check `GET /onboarding/status` for step-by-step setup guidance
5. Run a full pipeline refresh from the dashboard

## Security Notes

- No credentials are logged or returned in API responses
- Connector API keys are used per-request; they are never written to the database without `ENCRYPTION_KEY` encryption
- `BULLHORN_PASSWORD` is used only for the initial OAuth token exchange and cleared from memory immediately
- Email and phone numbers are SHA-256 hashed before storage; only masked versions are displayed
- Set `ALLOW_WRITES=true` in production to enable data mutation endpoints

## GMI MaaS Integration

PipelineOps uses an OpenAI-compatible client pointed at the GMI MaaS base URL. Set:

```
GMI_MAAS_BASE_URL=https://inference.gmi.ai/v1
GMI_MAAS_API_KEY=your_key
GMI_SELECTED_MODEL=meta-llama/Llama-3.3-70B-Instruct
```

Without LLM credentials, the system falls back to deterministic template-based responses for all AI features.
