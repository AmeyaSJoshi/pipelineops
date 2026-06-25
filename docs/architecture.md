# PipelineOps Agent — Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────┐
│                     Browser / AgentBox UI               │
│                  Next.js (port 3000)                    │
└──────────────────────────┬──────────────────────────────┘
                           │ HTTP / JSON
┌──────────────────────────▼──────────────────────────────┐
│                   FastAPI Backend (port 8080)            │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐  │
│  │  /run    │  │ /reports │  │  /agent  │  │/sources│  │
│  │  /jobs   │  │ /metrics │  │   /chat  │  │  /sync │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └───┬────┘  │
│       │              │              │             │       │
│  ┌────▼──────────────▼──────────────▼─────────────▼────┐ │
│  │                   Services Layer                     │ │
│  │  normalization  reconciliation  anomalies  reporting │ │
│  │  llm  audit  exports  sheets                        │ │
│  └────────────────────────┬────────────────────────────┘ │
│                           │                              │
│  ┌────────────────────────▼────────────────────────────┐ │
│  │               SQLAlchemy ORM                        │ │
│  └────────────────────────┬────────────────────────────┘ │
└───────────────────────────┼──────────────────────────────┘
                            │
         ┌──────────────────┼──────────────────┐
         ▼                  ▼                  ▼
   SQLite (dev)       PostgreSQL (prod)   In-memory (test)
```

## Component Responsibilities

### FastAPI Backend (`app/main.py`)

Entry point and route definitions. Responsibilities:
- CORS middleware
- Database initialization on startup (`init_db()`)
- Background task dispatch for async jobs (`/run`)
- Route registration for all 25+ endpoints

### Async Job System (`app/jobs.py`)

In-memory job store (dict). Each job has: `job_id`, `status` (pending/running/completed/failed), `task`, `created_at`, `result`, `error`.

Production note: replace with Redis for multi-worker deployments.

### Data Layer

**`app/db.py`** — SQLAlchemy engine, session factory, `get_db()` dependency, `init_db()`.

**`app/models.py`** — 11 ORM models:
- `SourceAccount` — connected data source (ATS, job board)
- `SyncRun` — individual sync execution log
- `ExternalRecord` — raw incoming record before normalization
- `Company` — client company (normalized)
- `JobRole` — open requisition with canonical pay/location
- `Candidate` — job seeker (hashed PII, supports merge chain via `is_merged_into`)
- `Application` — candidate × role with `canonical_stage`
- `PipelineEvent` — stage transition history
- `Anomaly` — detected issue with status tracking
- `ReportSnapshot` — saved report JSON
- `AuditLog` — immutable action log

### Services Layer

**`normalization.py`** — Pure functions for transforming raw source data:
- `parse_pay_range` — extracts (min, max, unit) from free-text pay strings
- `parse_location` — extracts city/state/remote_type
- `canonicalize_stage` — maps source-specific stage labels to the 13-stage canonical funnel
- `hash_email` / `mask_email` / `mask_phone` — PII safety
- `normalize_job` / `normalize_candidate` / `normalize_application` — full record normalization

**`reconciliation.py`** — Candidate deduplication:
- Confidence scoring: email hash (0.97) > phone hash (0.92) > name+location (0.88) > name+title (0.82)
- `find_duplicate_candidates` returns merge suggestions above 0.75 confidence
- `merge_candidates` reassigns applications, sets `is_merged_into` FK

**`anomalies.py`** — 9 checkers run on each pipeline refresh:
1. Missing pay rate on open roles
2. Stale roles (14+ days no activity; high severity at 21+ days)
3. Offer extended with no compensation amount
4. Interview scheduled with no date
5. High applicant count (≥5) with zero submitted to client
6. Submitted to client with no response in 7+ days
7. Duplicate submissions (same candidate × client in active roles)
8. Offer extended with no start date
9. Open role with no activity in 30+ days

**`reporting.py`** — Metrics calculation and narrative generation:
- `calculate_metrics` — funnel counts/rates, stale count, roles by client
- `generate_narrative_summary` — text description of pipeline health
- `get_recommended_actions` — prioritized action list

**`llm.py`** — GMI MaaS integration (OpenAI-compatible client):
- `classify_stage` — LLM stage disambiguation for ambiguous raw labels
- `generate_report` — LLM narrative from metrics dict
- `explain_anomaly` — LLM explanation for a specific anomaly
- `answer_chat_question` — LLM Q&A with pipeline context
- All functions have `_deterministic_*` fallbacks when `GMI_MAAS_API_KEY` is unset

**`audit.py`** — `log_action(db, actor, action, entity_type, entity_id, before, after)` → immutable `AuditLog` row.

**`exports.py`** — CSV generation (pipeline_summary, role_detail, candidate_stage_detail, anomalies).

**`sheets.py`** — Google Sheets export via service account credentials; falls back to `generate_sheet_preview` if not configured.

### Connectors (`app/connectors/`)

Abstract `BaseConnector` with `fetch_jobs`, `fetch_candidates`, `fetch_applications`, `fetch_events`, `normalize`.

8 demo connectors return differently-shaped synthetic data to prove normalization:

| Connector | Key field differences |
|---|---|
| Indeed | `jobPostingId`, `salary` as free text |
| CareerBuilder | `JobDID`, `Pay.FormattedMin/Max` |
| Monster | `JobID`, `Location.City/StateCode` |
| Dice | `id`, `employmentType`, `postedDate` |
| Greenhouse | `id` (int), `offices[].name`, nested departments |
| Lever | `posting` (string ID), `stage.text` |
| Bullhorn | `entity`, `clientCorporation.name`, `payRate` (float) |
| CSV | Configurable column mapping via LLM header normalization |

### Frontend (`frontend/`)

Next.js App Router with 7 pages:
- `/` Dashboard — KPIs, pipeline table, anomaly panel
- `/sources` — Source connection cards
- `/candidates` — Candidate table with masked PII
- `/anomalies` — Anomaly triage + candidate merge review
- `/reports` — Executive report + export
- `/chat` — Natural language Q&A
- `/settings` — GMI configuration + deployment checklist

## Data Flow: Full Pipeline Refresh

```
POST /run { task: "full_pipeline_refresh" }
  → creates job (pending)
  → fires background task

Background task:
  1. _sync_all_demo()
     for each connector:
       fetch_jobs() → normalize_job() → upsert JobRole
       fetch_candidates() → normalize_candidate() → upsert Candidate (by email_hash)
       fetch_applications() → normalize_application() → upsert Application
  
  2. reconcile_candidates(db)
     → find_duplicate_candidates() → save suggestions

  3. calculate_metrics(db)
     → funnel counts, rates, stale count

  4. detect_all_anomalies(db)
     → 9 checkers → save_anomalies()

  5. generate_report / generate_narrative_summary
     → LLM or deterministic fallback

  6. save ReportSnapshot

  7. job status → "completed", result attached
```

## Canonical Pipeline Stages

```
new_lead → applied → recruiter_screen → qualified →
submitted_to_client → client_review →
interview_scheduled → interview_completed →
offer → placed
          ↘ rejected
          ↘ withdrawn
          ↘ unknown
```

## Security Model

- **PII handling**: `email_hash` = SHA-256(lower(email)), never stored raw. API responses return `masked_email` (j***e@e***.com) and `masked_phone` (***-***-0101).
- **LLM prompts**: context passed to LLM contains only stage counts, role titles, company names — no email, phone, or candidate names.
- **Write protection**: `ALLOW_WRITES=false` by default. Mutation endpoints check this flag.
- **Secrets**: all credentials in environment variables. No hardcoded keys.
- **Audit trail**: every mutation logged to `AuditLog` with before/after JSON.
