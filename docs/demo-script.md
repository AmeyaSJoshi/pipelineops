# PipelineOps Agent — Demo Script

**Duration**: ~8 minutes  
**Audience**: Hackathon judges, recruiting ops teams, AgentBox marketplace reviewers  
**Goal**: Show the full agent loop — data in, anomalies detected, report generated, chat answered

---

## Setup (before demo, ~30 seconds)

1. Start the stack: `docker compose up` (or ensure backend on :8080 + frontend on :3000 are running)
2. Navigate to http://localhost:3000
3. If data is already seeded, click "Reset" in Settings → "Seed" in the top bar

---

## Act 1: The Problem (30 seconds)

> "Recruiting ops teams manage data across 6–10 different tools — job boards, ATS platforms, staffing software. Every week, someone's manually copying rows into a spreadsheet. Anomalies go unnoticed. Duplicate candidates slip through. Reports take hours."

Point to the empty dashboard.

> "PipelineOps Agent fixes this. It connects to your sources, normalizes everything into a single pipeline, and surfaces problems automatically."

---

## Act 2: Data Sources (1 minute)

Navigate to **Sources** page.

> "We have 8 pre-built connectors — Indeed, CareerBuilder, Monster, Dice for job boards; Greenhouse, Lever, Bullhorn for ATS; plus CSV upload for anything else."

Point to the "GMI Cloud Ready" banner.

> "When you add GMI MaaS credentials, LLM-powered features activate — stage classification, narrative reports, chat. Everything also works in deterministic fallback mode without credits."

Click **Run Demo Sync** on the Indeed connector.

> "Each connector pulls data in whatever shape that source returns it — different field names, different stage labels, different pay formats — and normalizes it into a canonical 13-stage pipeline."

---

## Act 3: Full Pipeline Refresh (1.5 minutes)

Click the blue **Run Full Pipeline Refresh** button in the top bar.

> "This fires an async job — AgentBox pattern, POST to /run returns 202 with a job ID. The backend syncs all sources in parallel, reconciles duplicate candidates, detects anomalies, and generates an executive report."

Watch the progress indicator.

> "Under the hood: 9 sources synced, 31 candidates normalized, 31 applications mapped into the canonical funnel, 13 anomalies detected."

When complete, the dashboard auto-updates.

---

## Act 4: Dashboard Tour (1 minute)

Point to the KPI cards.

> "7 open roles, 29 active candidates, 16 submitted to clients, 13 anomalies flagged."

Point to the pipeline table.

> "Each client row shows the funnel — applicants, submitted, interviewed, offered. You can see Meridian Robotics has 0 submissions out of 5 applicants. That's a bottleneck we'll fix in a moment."

Point to the anomaly panel.

> "Recent anomalies surfaced automatically — stale roles, missing pay rates, an offer with no compensation amount."

---

## Act 5: Anomalies & Reconciliation (2 minutes)

Navigate to **Anomalies** page.

> "13 anomalies auto-detected across 9 categories."

Point to a high-severity anomaly.

> "This Forklift Operator role has been open 4 weeks with no pay rate — you can't post it externally without one. High severity."

Click **Approve** on a medium-severity anomaly.

> "Ops team reviews and approves or ignores. Status tracked in audit log."

Click the **Candidate Reconciliation** tab.

> "James Rivera appears in both Indeed and Greenhouse with different email capitalizations — james.rivera@email.com vs James.Rivera@Email.com. Confidence score: 97%, email hash match."

Click **Approve Merge**.

> "One click merges the records, reassigns all applications to the primary, and marks the secondary as merged. No more duplicate submissions."

---

## Act 6: Reports (1 minute)

Navigate to **Reports** page.

> "AI-generated executive summary — this one's deterministic fallback since we're in demo mode, but with GMI MaaS it's an LLM-narrated summary."

Point to the conversion rates chart.

> "Submission rate: 52%. Offer rate: 25%. Placement rate: 7%. Meridian Robotics bottleneck visible here — they have 5 applicants and 0 submitted."

Point to Recommended Actions.

> "Three actions auto-prioritized: add pay rate to Forklift Operator, investigate Meridian Robotics bottleneck, follow up on 2 pending offers."

Click **Export to CSV**.

> "Download as CSV or push directly to Google Sheets if configured."

---

## Act 7: AI Chat (1 minute)

Navigate to **Chat** page.

> "Last piece — natural language Q&A against live pipeline data."

Type: "Which roles are stale?"

> "Returns the two roles with no activity in 14+ days. Context is pulled from the live DB, not a static knowledge base."

Type: "What's our offer-to-placement rate?"

> "7%. The agent explains why — 2 offers extended, only 1 placed so far this cycle."

---

## Act 8: AgentBox Integration (30 seconds)

Navigate to the **Settings** page.

> "Health check endpoint confirms AgentBox readiness. When you deploy to AgentBox, the async job pattern is already wired — POST /run, GET /jobs/{id}. The deployment checklist walks you through adding GMI credentials."

---

## Closing (15 seconds)

> "PipelineOps Agent: 8 source connectors, 13-stage canonical pipeline, automatic anomaly detection, candidate deduplication, AI reports and chat — fully deployed to GMI AgentBox. No manual data entry required."

---

## Key Numbers to Quote

- 8 demo connectors (4 job boards, 3 ATS platforms, CSV)
- 13 canonical pipeline stages
- 9 anomaly categories auto-detected
- 25+ API endpoints, AgentBox async job pattern
- 65 tests (unit + integration)
- 100% deterministic fallback — works without LLM credits

## Common Judge Questions

**Q: What happens when GMI MaaS isn't configured?**  
A: Deterministic fallback mode — stage mapping uses rule-based lookup tables, reports use template-based narratives, chat pattern-matches keywords. Every feature works.

**Q: How do you handle real ATS credentials?**  
A: Set `GREENHOUSE_API_KEY`, `LEVER_API_KEY`, or `BULLHORN_*` env vars. The connector factory picks up the credentials and switches from demo to live mode automatically.

**Q: Is PII safe?**  
A: Email and phone are SHA-256 hashed before storage and masked in all API responses (j***e@e***.com). LLM prompts never contain raw PII.

**Q: Can it handle large datasets?**  
A: SQLite for demo, Postgres for production (set `DATABASE_URL`). The sync uses upsert-by-email-hash so re-running is idempotent.
