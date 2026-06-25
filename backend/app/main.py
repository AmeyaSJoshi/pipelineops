import asyncio
import io
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db, init_db
from app.models import Anomaly, Application, Candidate, Company, JobRole, ReportSnapshot, SourceAccount
from app.schemas import (
    AnomalyOut, AnomalyUpdate, ChatRequest, ChatResponse, ExportRequest, ExportResponse,
    GMISettingsResponse, HealthResponse, JobResponse, JobStartRequest,
    MetricsResponse, ReportSummaryResponse, ResetResponse, SeedResponse, SourceAccountOut,
)
from app.jobs import create_job, get_job, update_job
from app.seed import seed_demo_data, reset_demo_data
from app.services.normalization import normalize_candidate, normalize_application
from app.services.anomalies import detect_all_anomalies, save_anomalies
from app.services.reporting import calculate_metrics, calculate_role_metrics, generate_narrative_summary, get_recommended_actions
from app.services.reconciliation import find_duplicate_candidates, merge_candidates
from app.services.llm import generate_report, answer_chat_question
from app.services.exports import generate_csv_export, generate_sheet_preview
from app.services.sheets import export_to_google_sheets
from app.services.audit import log_action

settings = get_settings()

app = FastAPI(
    title="PipelineOps Agent API",
    description="AI recruiting operations agent — AgentBox compatible",
    version=settings.VERSION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


# ──────────────────────────────────────────────────────────────────────────────
# Health
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse, tags=["General"])
def health(db: Session = Depends(get_db)):
    try:
        db.execute(__import__("sqlalchemy").text("SELECT 1"))
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {str(e)}"

    gmi_configured = settings.gmi_configured()
    return HealthResponse(
        status="ok",
        service=settings.SERVICE_NAME,
        agentbox_ready=True,
        gmi_maas_configured=gmi_configured,
        message="GMI MaaS configured." if gmi_configured else "GMI MaaS env vars missing. Running in local demo fallback mode.",
        database=db_status,
        version=settings.VERSION,
    )


# ──────────────────────────────────────────────────────────────────────────────
# AgentBox Async Job Lifecycle
# ──────────────────────────────────────────────────────────────────────────────

SUPPORTED_TASKS = [
    "sync_all_demo_sources", "normalize_import", "reconcile_candidates",
    "detect_anomalies", "generate_manager_report", "update_sheet",
    "full_pipeline_refresh",
]


@app.post("/run", status_code=202, response_model=JobResponse, tags=["AgentBox"])
async def run_task(request: JobStartRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    if request.task not in SUPPORTED_TASKS:
        raise HTTPException(400, f"Unknown task '{request.task}'. Supported: {SUPPORTED_TASKS}")
    job = create_job(request.task, request.params)
    background_tasks.add_task(_execute_job, job["job_id"], request.task, request.params)
    return JobResponse(**job)


@app.get("/jobs/{job_id}", response_model=JobResponse, tags=["AgentBox"])
def get_job_status(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return JobResponse(**job)


async def _execute_job(job_id: str, task: str, params: Dict[str, Any]):
    from app.db import SessionLocal
    db = SessionLocal()
    try:
        update_job(job_id, status="running", progress=0.05)
        if task == "full_pipeline_refresh":
            result = await _full_pipeline_refresh(job_id, db)
        elif task == "detect_anomalies":
            anomalies = detect_all_anomalies(db)
            save_anomalies(db, anomalies)
            result = {"anomalies_found": len(anomalies)}
        elif task == "generate_manager_report":
            metrics = calculate_metrics(db)
            anomalies = db.query(Anomaly).filter(Anomaly.status == "open").all()
            summary = generate_report(metrics, [a.__dict__ for a in anomalies])
            result = {"summary": summary, "metrics": metrics}
        elif task == "reconcile_candidates":
            dupes = find_duplicate_candidates(db)
            result = {"duplicate_suggestions": len(dupes)}
        elif task == "sync_all_demo_sources":
            result = await _sync_all_demo(job_id, db)
        else:
            result = {"message": f"Task '{task}' completed (stub)."}
        update_job(job_id, status="completed", progress=1.0, result=result)
    except Exception as e:
        update_job(job_id, status="failed", error=str(e))
    finally:
        db.close()


async def _full_pipeline_refresh(job_id: str, db: Session) -> Dict[str, Any]:
    steps = [
        (10, "Ingesting records from demo sources"),
        (25, "Normalizing jobs and candidates"),
        (40, "Mapping pipeline stages"),
        (55, "Reconciling duplicate candidates"),
        (65, "Calculating metrics"),
        (75, "Detecting anomalies"),
        (85, "Generating manager narrative"),
        (95, "Preparing export preview"),
    ]

    # Step 1: sync all demo sources
    update_job(job_id, progress=0.10, result={"step": "Ingesting records"})
    await _sync_all_demo(job_id, db)

    update_job(job_id, progress=0.35, result={"step": "Normalizing jobs & pay rates"})
    await asyncio.sleep(0.05)

    update_job(job_id, progress=0.45, result={"step": "Mapping pipeline stages"})
    await asyncio.sleep(0.05)

    # Step 2: reconcile
    update_job(job_id, progress=0.55, result={"step": "Reconciling candidates"})
    dupes = find_duplicate_candidates(db)
    await asyncio.sleep(0.05)

    # Step 3: metrics
    update_job(job_id, progress=0.65, result={"step": "Calculating metrics"})
    metrics = calculate_metrics(db)
    await asyncio.sleep(0.05)

    # Step 4: anomalies
    update_job(job_id, progress=0.75, result={"step": "Detecting anomalies"})
    anomaly_dicts = detect_all_anomalies(db)
    save_anomalies(db, anomaly_dicts)
    metrics["anomaly_count"] = len(anomaly_dicts)
    await asyncio.sleep(0.05)

    # Step 5: report
    update_job(job_id, progress=0.85, result={"step": "Generating manager report"})
    anomalies_db = db.query(Anomaly).filter(Anomaly.status == "open").all()
    summary = generate_report(metrics, anomaly_dicts)
    narrative = generate_narrative_summary(metrics, anomalies_db)
    await asyncio.sleep(0.05)

    # Step 6: export preview
    update_job(job_id, progress=0.95, result={"step": "Preparing export"})
    sheet_preview = generate_sheet_preview(db)
    actions = get_recommended_actions(metrics, anomalies_db)

    # Save report snapshot
    snapshot = ReportSnapshot(
        metrics_json=metrics,
        narrative_summary=summary,
        generated_at=datetime.utcnow(),
    )
    db.add(snapshot)
    db.commit()

    log_action(db, "system", "full_pipeline_refresh", after_json={"metrics": metrics, "anomalies": len(anomaly_dicts)})

    return {
        "summary": summary,
        "narrative": narrative,
        "metrics": metrics,
        "anomalies": anomaly_dicts[:10],
        "duplicate_suggestions": len(dupes),
        "sheet_preview": sheet_preview,
        "recommended_actions": actions,
    }


async def _sync_all_demo(job_id: str, db: Session) -> Dict[str, Any]:
    from app.connectors import DEMO_CONNECTORS
    from app.services.normalization import normalize_job, normalize_candidate, normalize_application, content_hash

    total_records = 0
    for source_name, ConnectorClass in DEMO_CONNECTORS.items():
        connector = ConnectorClass()
        source = db.query(SourceAccount).filter(SourceAccount.source_type == source_name).first()
        if not source:
            continue

        # Fetch and store jobs
        raw_jobs = connector.fetch_jobs()
        for rj in raw_jobs:
            norm = normalize_job(rj, source_name)
            company_name = norm.get("company") or "Unknown"
            company = db.query(Company).filter(Company.normalized_name == norm.get("normalized_company")).first()
            if not company:
                company = db.query(Company).filter(Company.name == company_name).first()
            if not company:
                continue  # Skip — only create new roles for existing companies

            existing = db.query(JobRole).filter(
                JobRole.source_account_id == source.id,
                JobRole.external_id == norm.get("external_id")
            ).first()
            if not existing and norm.get("external_id"):
                role = JobRole(
                    external_id=norm["external_id"],
                    source_account_id=source.id,
                    company_id=company.id,
                    title=norm["title"],
                    normalized_title=norm.get("normalized_title"),
                    location_city=norm.get("location_city"),
                    location_state=norm.get("location_state"),
                    remote_type=norm.get("remote_type", "unknown"),
                    pay_min=norm.get("pay_min"),
                    pay_max=norm.get("pay_max"),
                    pay_unit=norm.get("pay_unit", "unknown"),
                    openings_count=int(norm.get("openings_count") or 1),
                    status=norm.get("status", "open"),
                    recruiter_owner=norm.get("recruiter_owner"),
                )
                db.add(role)

        # Fetch and store applications/candidates
        raw_apps = connector.fetch_applications()
        for ra in raw_apps:
            norm_cand = normalize_candidate(ra, source_name)
            norm_app = normalize_application(ra, source_name)

            # Upsert candidate by email hash
            candidate = None
            if norm_cand.get("email_hash"):
                candidate = db.query(Candidate).filter(
                    Candidate.email_hash == norm_cand["email_hash"]
                ).first()
            if not candidate:
                candidate = Candidate(
                    external_id=norm_cand.get("external_id"),
                    source_account_id=source.id,
                    full_name=norm_cand["full_name"],
                    email_hash=norm_cand.get("email_hash"),
                    email_display_masked=norm_cand.get("email_display_masked"),
                    phone_hash=norm_cand.get("phone_hash"),
                    phone_display_masked=norm_cand.get("phone_display_masked"),
                    location=norm_cand.get("location"),
                    current_title=norm_cand.get("current_title"),
                )
                db.add(candidate)
                db.flush()
            total_records += 1

        source.last_sync_at = datetime.utcnow()
        source.records_total = total_records
        db.commit()

    return {"records_synced": total_records}


# ──────────────────────────────────────────────────────────────────────────────
# Demo / Admin
# ──────────────────────────────────────────────────────────────────────────────

@app.post("/demo/seed", response_model=SeedResponse, tags=["Demo"])
def demo_seed(db: Session = Depends(get_db)):
    # Don't re-seed if already seeded
    if db.query(SourceAccount).first():
        return SeedResponse(message="Already seeded. Use /demo/reset first.", sources_created=0, companies_created=0, roles_created=0, candidates_created=0, applications_created=0)
    result = seed_demo_data(db)
    log_action(db, "user", "demo_seed", after_json=result)
    return SeedResponse(message="Demo data seeded successfully.", **result)


@app.post("/demo/reset", response_model=ResetResponse, tags=["Demo"])
def demo_reset(db: Session = Depends(get_db)):
    tables = reset_demo_data(db)
    return ResetResponse(message="Demo data reset. Run /demo/seed to re-populate.", tables_cleared=tables)


# ──────────────────────────────────────────────────────────────────────────────
# Sync
# ──────────────────────────────────────────────────────────────────────────────

@app.post("/sync/csv", tags=["Sync"])
async def sync_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    csv_text = content.decode("utf-8-sig")
    from app.connectors.csv_connector import CSVConnector
    connector = CSVConnector(csv_text, file.filename)
    status = connector.test_connection()
    if not status["success"]:
        raise HTTPException(400, status["message"])
    jobs = connector.fetch_jobs()
    candidates = connector.fetch_candidates()
    apps = connector.fetch_applications()
    return {
        "filename": file.filename,
        "jobs_found": len(jobs),
        "candidates_found": len(candidates),
        "applications_found": len(apps),
        "message": "CSV parsed. Review and confirm to import.",
        "preview": {"jobs": jobs[:5], "candidates": candidates[:5]},
    }


@app.post("/sync/demo/{source_name}", tags=["Sync"])
def sync_demo_source(source_name: str, db: Session = Depends(get_db)):
    from app.connectors import DEMO_CONNECTORS
    if source_name not in DEMO_CONNECTORS:
        raise HTTPException(404, f"Demo source '{source_name}' not found.")
    connector = DEMO_CONNECTORS[source_name]()
    return {
        "source": source_name,
        "jobs": connector.fetch_jobs(),
        "candidates": connector.fetch_candidates(),
        "applications": connector.fetch_applications(),
        "status": "demo",
    }


# ──────────────────────────────────────────────────────────────────────────────
# Reports
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/reports/summary", tags=["Reports"])
def report_summary(db: Session = Depends(get_db)):
    metrics = calculate_metrics(db)
    anomalies = db.query(Anomaly).filter(Anomaly.status == "open").all()
    roles = calculate_role_metrics(db)
    snapshot = db.query(ReportSnapshot).order_by(ReportSnapshot.generated_at.desc()).first()
    narrative = snapshot.narrative_summary if snapshot else generate_narrative_summary(metrics, anomalies)
    actions = get_recommended_actions(metrics, anomalies)
    return {
        "generated_at": datetime.utcnow().isoformat(),
        "metrics": metrics,
        "narrative_summary": narrative,
        "anomaly_count": len(anomalies),
        "top_anomalies": [
            {
                "id": a.id, "severity": a.severity, "category": a.category,
                "title": a.title, "explanation": a.explanation,
                "recommended_fix": a.recommended_fix, "status": a.status,
                "created_at": a.created_at.isoformat(),
            }
            for a in sorted(anomalies, key=lambda x: {"high": 0, "medium": 1, "low": 2}.get(x.severity, 3))[:5]
        ],
        "pipeline_data": roles[:20],
        "recommended_actions": actions,
    }


@app.get("/reports/pipeline", tags=["Reports"])
def report_pipeline(db: Session = Depends(get_db)):
    return {"roles": calculate_role_metrics(db)}


@app.get("/reports/anomalies", tags=["Reports"])
def report_anomalies(db: Session = Depends(get_db)):
    anomalies = db.query(Anomaly).order_by(Anomaly.created_at.desc()).all()
    return {
        "anomalies": [
            {
                "id": a.id, "severity": a.severity, "category": a.category,
                "title": a.title, "explanation": a.explanation,
                "recommended_fix": a.recommended_fix,
                "related_entity_type": a.related_entity_type,
                "related_entity_id": a.related_entity_id,
                "status": a.status,
                "created_at": a.created_at.isoformat(),
            }
            for a in anomalies
        ]
    }


@app.patch("/reports/anomalies/{anomaly_id}", tags=["Reports"])
def update_anomaly(anomaly_id: int, update: AnomalyUpdate, db: Session = Depends(get_db)):
    anomaly = db.query(Anomaly).filter(Anomaly.id == anomaly_id).first()
    if not anomaly:
        raise HTTPException(404, "Anomaly not found")
    old_status = anomaly.status
    anomaly.status = update.status
    if update.status == "resolved":
        anomaly.resolved_at = datetime.utcnow()
    db.commit()
    log_action(db, "user", "update_anomaly", "anomaly", anomaly_id,
               before_json={"status": old_status}, after_json={"status": update.status})
    return {"id": anomaly_id, "status": anomaly.status}


@app.post("/sheets/export", tags=["Reports"])
def sheets_export(request: ExportRequest = None, db: Session = Depends(get_db)):
    if request and request.format == "google_sheets":
        result = export_to_google_sheets(db)
    else:
        result = {
            "success": True,
            "format": "csv",
            "message": "CSV export ready.",
            "preview": generate_sheet_preview(db),
        }
    log_action(db, "user", "export", after_json={"format": request.format if request else "csv"})
    return result


@app.get("/exports/download", tags=["Reports"])
def download_csv(db: Session = Depends(get_db)):
    csv_data = generate_csv_export(db)
    combined = ""
    for tab_name, content in csv_data.items():
        combined += f"# {tab_name.replace('_', ' ').title()}\n{content}\n\n"
    return StreamingResponse(
        io.BytesIO(combined.encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=pipelineops_export.csv"},
    )


# ──────────────────────────────────────────────────────────────────────────────
# Agent Chat
# ──────────────────────────────────────────────────────────────────────────────

@app.post("/agent/chat", response_model=ChatResponse, tags=["Agent"])
def agent_chat(request: ChatRequest, db: Session = Depends(get_db)):
    metrics = calculate_metrics(db)
    anomalies = db.query(Anomaly).filter(Anomaly.status == "open").all()
    roles = calculate_role_metrics(db)
    context = {
        "metrics": metrics,
        "anomalies": [{"severity": a.severity, "title": a.title, "category": a.category} for a in anomalies],
        "roles": roles[:10],
    }
    response_text = answer_chat_question(request.message, context)
    mode = "gmi_maas" if settings.gmi_configured() else "demo_fallback"
    return ChatResponse(
        response=response_text,
        sources=["pipeline_metrics", "anomaly_report", "role_data"],
        mode=mode,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Sources & Metrics
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/sources", tags=["General"])
def list_sources(db: Session = Depends(get_db)):
    sources = db.query(SourceAccount).all()
    return {
        "sources": [
            {
                "id": s.id, "source_type": s.source_type, "display_name": s.display_name,
                "status": s.status, "last_sync_at": s.last_sync_at.isoformat() if s.last_sync_at else None,
                "records_total": s.records_total,
            }
            for s in sources
        ]
    }


@app.get("/metrics", tags=["General"])
def get_metrics(db: Session = Depends(get_db)):
    return calculate_metrics(db)


@app.get("/candidates", tags=["Candidates"])
def list_candidates(db: Session = Depends(get_db)):
    candidates = db.query(Candidate).filter(Candidate.is_merged_into == None).limit(100).all()
    result = []
    for c in candidates:
        active_apps = [a for a in c.applications if a.status == "active"]
        latest_stage = active_apps[-1].canonical_stage if active_apps else None
        result.append({
            "id": c.id, "full_name": c.full_name,
            "email_masked": c.email_display_masked,
            "phone_masked": c.phone_display_masked,
            "location": c.location, "current_title": c.current_title,
            "application_count": len(c.applications),
            "current_stage": latest_stage,
        })
    return {"candidates": result}


@app.get("/candidates/duplicates", tags=["Candidates"])
def get_duplicate_candidates(db: Session = Depends(get_db)):
    suggestions = find_duplicate_candidates(db)
    return {"suggestions": suggestions, "count": len(suggestions)}


@app.post("/candidates/merge", tags=["Candidates"])
def merge_candidate_records(primary_id: int, secondary_id: int, db: Session = Depends(get_db)):
    result = merge_candidates(db, primary_id, secondary_id, actor="user")
    if not result.get("success"):
        raise HTTPException(400, result.get("error", "Merge failed"))
    return result


# ──────────────────────────────────────────────────────────────────────────────
# Settings / GMI
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/settings/gmi", response_model=GMISettingsResponse, tags=["Settings"])
def gmi_settings():
    return GMISettingsResponse(
        gmi_maas_configured=settings.gmi_configured(),
        gmi_base_url=settings.GMI_MAAS_BASE_URL or None,
        gmi_model=settings.get_llm_model() if settings.llm_available() else None,
        agentbox_ready=True,
        deployment_mode=settings.GMI_AGENTBOX_DEPLOYMENT_MODE or "local_demo",
        listing_status=settings.GMI_AGENTBOX_LISTING_STATUS,
        google_sheets_configured=settings.google_sheets_configured(),
        allow_writes=settings.ALLOW_WRITES,
    )
