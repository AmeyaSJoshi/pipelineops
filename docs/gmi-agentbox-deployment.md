# GMI AgentBox Deployment Guide

## Prerequisites

1. GMI Cloud account with AgentBox access
2. Docker image pushed to a registry accessible by AgentBox
3. GMI MaaS API key (optional — agent works in fallback mode without it)

## Step 1: Build and Push Docker Image

```bash
# Build backend image
docker build -f docker/Dockerfile.backend -t pipelineops-agent:latest .

# Tag and push to your registry
docker tag pipelineops-agent:latest <your-registry>/pipelineops-agent:latest
docker push <your-registry>/pipelineops-agent:latest
```

## Step 2: Configure Environment

Set these environment variables in the AgentBox deployment config:

```env
# Required
DATABASE_URL=sqlite:///./pipelineops.db
ALLOW_WRITES=false

# GMI MaaS (enables LLM features — agent works without these)
GMI_MAAS_BASE_URL=https://inference.gmi.ai/v1
GMI_MAAS_API_KEY=<your-key>
GMI_SELECTED_MODEL=meta-llama/Llama-3.1-70B-Instruct

# AgentBox metadata
GMI_AGENTBOX_DEPLOYMENT_MODE=production
GMI_AGENTBOX_MARKETPLACE_CATEGORY=Data & Analytics
GMI_AGENTBOX_LISTING_STATUS=Published
```

## Step 3: AgentBox Agent Definition

Create `agentbox.json` in the project root (or configure via the AgentBox UI):

```json
{
  "name": "PipelineOps Agent",
  "version": "1.0.0",
  "description": "AI recruiting operations agent for pipeline data entry, anomaly detection, and reporting.",
  "category": "Data & Analytics",
  "entrypoint": {
    "type": "http",
    "port": 8080,
    "healthCheck": "/health",
    "runEndpoint": "/run",
    "jobStatusEndpoint": "/jobs/{job_id}"
  },
  "capabilities": [
    "async_jobs",
    "natural_language_chat",
    "csv_import",
    "data_export"
  ],
  "requiredEnvVars": ["DATABASE_URL"],
  "optionalEnvVars": ["GMI_MAAS_BASE_URL", "GMI_MAAS_API_KEY", "GMI_SELECTED_MODEL"],
  "demoMode": {
    "seedEndpoint": "/demo/seed",
    "resetEndpoint": "/demo/reset"
  }
}
```

## Step 4: Deploy

```bash
# Using GMI CLI (example — check GMI docs for current CLI syntax)
gmi agentbox deploy \
  --image <your-registry>/pipelineops-agent:latest \
  --env-file .env \
  --port 8080
```

Or deploy via the AgentBox web UI by providing the image URL and environment variables.

## Step 5: Verify Deployment

```bash
# Check health
curl https://<your-agentbox-url>/health

# Expected response
{
  "status": "ok",
  "agentbox_ready": true,
  "gmi_maas_configured": true,
  "database": "ok",
  "version": "1.0.0"
}

# Seed demo data and run a pipeline refresh
curl -X POST https://<your-agentbox-url>/demo/seed
curl -X POST https://<your-agentbox-url>/run \
  -H "Content-Type: application/json" \
  -d '{"task": "full_pipeline_refresh", "params": {}}'
```

## Async Job Pattern

AgentBox uses a non-blocking job pattern. All long-running operations follow this flow:

```
POST /run
  Body: { "task": "full_pipeline_refresh", "params": {} }
  Response 202: { "job_id": "abc123", "status": "pending" }

GET /jobs/abc123
  Response: { "job_id": "abc123", "status": "running", "progress": 0.4 }

GET /jobs/abc123  (poll until completed)
  Response: {
    "job_id": "abc123",
    "status": "completed",
    "result": { "metrics": {...}, "anomalies": [...], "narrative": "..." }
  }
```

Supported task types:
- `full_pipeline_refresh` — full sync + anomaly detection + report generation
- `detect_anomalies` — anomaly scan only
- `reconcile_candidates` — candidate deduplication only

## Connecting Real Data Sources

The agent ships with 8 demo connectors. To connect real sources, set credentials as environment variables and update the source account status via `POST /sources/{id}/configure`.

| Source | Required Env Vars |
|---|---|
| Greenhouse | `GREENHOUSE_API_KEY`, `GREENHOUSE_SUBDOMAIN` |
| Lever | `LEVER_API_KEY` |
| Bullhorn | `BULLHORN_CLIENT_ID`, `BULLHORN_CLIENT_SECRET`, `BULLHORN_USERNAME`, `BULLHORN_PASSWORD` |
| Indeed | Contact Indeed for Employer API access |
| Google Sheets (export) | `GOOGLE_SHEETS_CREDENTIALS_JSON`, `GOOGLE_SHEETS_SPREADSHEET_ID` |

CSV upload requires no credentials — use `POST /sync/csv` with a multipart file upload.

## Production Checklist

- [ ] `ALLOW_WRITES=false` unless you intend to enable write operations
- [ ] Database backed by Postgres (set `DATABASE_URL=postgresql://...`) for production persistence
- [ ] Secrets set as AgentBox environment variables, not in the image
- [ ] Health check endpoint responding at `/health`
- [ ] Demo data seeded for marketplace listing review
