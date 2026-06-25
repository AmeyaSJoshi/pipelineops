# GMI AgentBox Marketplace Listing — PipelineOps Agent

## Listing Metadata

| Field | Value |
|---|---|
| **Name** | PipelineOps Agent |
| **Tagline** | AI recruiting operations agent — automated pipeline data entry, anomaly detection, and reporting |
| **Category** | Data & Analytics |
| **Version** | 1.0.0 |
| **License** | MIT |
| **Status** | Draft |

---

## Short Description (140 chars)

AI agent that syncs recruiting data from 8 sources, normalizes pipeline stages, flags anomalies, and generates executive reports via chat.

---

## Full Description

PipelineOps Agent is an AI-powered recruiting operations platform that eliminates manual pipeline data entry for staffing and recruiting teams.

### What It Does

**Automated Data Sync**
Connect job boards and ATS platforms (Indeed, CareerBuilder, Monster, Dice, Greenhouse, Lever, Bullhorn) or upload CSV exports. The agent normalizes all records into a canonical 13-stage recruiting funnel regardless of source format.

**Anomaly Detection**
Automatically flags pipeline problems before they cost placements:
- Stale open roles (no activity 14+ days)
- Missing pay rates on active requisitions
- Offers extended without compensation amounts
- Candidates stuck in early stages while newer applicants bypass them
- Duplicate candidate records across sources

**Candidate Reconciliation**
Identifies duplicate candidates submitted from multiple sources using email/phone hashing and name similarity. Presents merge suggestions with confidence scores for one-click approval.

**Executive Reporting**
AI-generated narrative summaries + structured metrics: funnel conversion rates by client, time-to-placement, offer acceptance rates, role performance. Export to Google Sheets or CSV.

**Natural Language Chat**
Ask questions in plain English: "Which roles are stale?", "What's our offer-to-placement rate?", "Which clients have the most bottlenecks?" The agent answers from live pipeline data using GMI MaaS LLM or a deterministic fallback.

### Key Features

- **8 pre-built connectors** with extensible connector interface
- **13-stage canonical funnel**: new_lead → applied → recruiter_screen → qualified → submitted_to_client → client_review → interview_scheduled → interview_completed → offer → placed / rejected / withdrawn
- **PII-safe**: email and phone hashed (SHA-256) for deduplication; masked in all API responses
- **Demo mode**: runs entirely on synthetic data — no credentials required to evaluate
- **Async job pattern**: fully compatible with AgentBox orchestration (`POST /run` → `GET /jobs/{id}`)
- **GMI MaaS integration**: stage classification, anomaly explanation, report narration, chat Q&A

### Tech Stack

- **Backend**: Python / FastAPI / SQLAlchemy / SQLite (dev) / PostgreSQL (prod)
- **Frontend**: Next.js / TypeScript / Tailwind CSS / shadcn/ui
- **LLM**: GMI MaaS (OpenAI-compatible) with deterministic fallback
- **Deployment**: Docker / AgentBox

---

## Screenshots

1. **Dashboard** — KPI cards (open roles, active candidates, interviews, placements), pipeline funnel by client, anomaly panel
2. **Data Sources** — 9 source connections with status badges, one-click demo sync
3. **Anomalies & Reconciliation** — Tabbed view: pipeline anomalies with severity badges + candidate merge suggestions with confidence scores
4. **Manager Reports** — AI narrative + conversion rates chart + recommended actions grid
5. **AI Chat** — Conversational Q&A with suggested queries and workspace context
6. **Settings** — GMI API configuration, health status, deployment checklist

---

## Demo Instructions

1. Click "Try in AgentBox"
2. The agent auto-seeds synthetic data (9 sources, 5 clients, 7 roles, 31 candidates)
3. Click "Run Full Pipeline Refresh" in the top bar
4. Explore the Dashboard, Anomalies, and Reports pages
5. Try the chat: ask "Which roles are stale?" or "What's our offer rate?"

No credentials required for demo evaluation.

---

## API Reference

```
GET  /health                    → AgentBox readiness check
POST /run                       → Submit async job (202 + job_id)
GET  /jobs/{id}                 → Poll job status
POST /demo/seed                 → Seed synthetic data
GET  /metrics                   → Pipeline KPIs
GET  /reports/summary           → Full executive report
GET  /reports/anomalies         → Open anomalies list
POST /agent/chat                → Natural language Q&A
GET  /exports/download          → CSV data export
```

---

## Pricing / Usage Notes

- Runs on any AgentBox compute tier
- LLM features require GMI MaaS credits (stage classification, report narration, chat)
- All core features (sync, normalization, anomaly detection, metrics) work without LLM credits in fallback mode
- Request GMI hackathon credits: http://discord.gg/mbYhCJSbF6

---

## Support

- GitHub Issues: [link to repo]
- Discord: http://discord.gg/mbYhCJSbF6 (GMI Cloud community)
