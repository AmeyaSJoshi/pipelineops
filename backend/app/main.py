import asyncio
import io
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, BackgroundTasks, Query
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
from app.services.normalization import normalize_candidate, normalize_application, normalize_job, content_hash
from app.services.anomalies import detect_all_anomalies, save_anomalies
from app.services.reporting import calculate_metrics, calculate_role_metrics, generate_narrative_summary, get_recommended_actions
from app.services.reconciliation import find_duplicate_candidates, merge_candidates
from app.services.llm import generate_report, answer_chat_question
from app.services.exports import generate_csv_export, generate_sheet_preview
from app.services.sheets import export_to_google_sheets
from app.services.audit import log_action
from app.auth import router as auth_router

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


app.include_router(auth_router)


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
# Connectors — status and live sync
# ──────────────────────────────────────────────────────────────────────────────

BLOCKED_SOURCES = {"indeed", "careerbuilder", "monster", "dice"}
LIVE_SOURCES = {"greenhouse", "lever", "bullhorn"}

CONNECTOR_WORKAROUNDS = {
    "indeed": "Export candidates as CSV from Indeed Employer dashboard, then upload via /sync/file.",
    "careerbuilder": "Export candidates as CSV from CareerBuilder portal, then upload via /sync/file.",
    "monster": "Export candidates from Monster Employer Center as CSV, then upload via /sync/file.",
    "dice": "Export candidate profiles from Dice employer account as CSV, then upload via /sync/file.",
}


def _build_connector(source_type: str):
    """Instantiate the correct connector class with credentials from settings."""
    from app.connectors import GreenhouseConnector, LeverConnector, BullhornConnector
    from app.connectors import IndeedConnector, CareerBuilderConnector, MonsterConnector, DiceConnector

    mapping = {
        "greenhouse": lambda: GreenhouseConnector(api_key=settings.GREENHOUSE_API_KEY),
        "lever": lambda: LeverConnector(api_key=settings.LEVER_API_KEY),
        "bullhorn": lambda: BullhornConnector(
            client_id=settings.BULLHORN_CLIENT_ID,
            client_secret=settings.BULLHORN_CLIENT_SECRET,
            username=settings.BULLHORN_USERNAME,
            password=settings.BULLHORN_PASSWORD,
        ),
        "indeed": lambda: IndeedConnector(),
        "careerbuilder": lambda: CareerBuilderConnector(),
        "monster": lambda: MonsterConnector(),
        "dice": lambda: DiceConnector(),
    }
    factory = mapping.get(source_type)
    if not factory:
        raise HTTPException(404, f"Unknown source type '{source_type}'.")
    return factory()


@app.get("/connectors", tags=["Connectors"])
def list_connectors():
    """Return status of all connector types — what's live, what's blocked, what needs creds."""
    return {
        "live": {
            "greenhouse": {
                "configured": settings.greenhouse_configured(),
                "status": "ready" if settings.greenhouse_configured() else "needs_credentials",
                "env_var": "GREENHOUSE_API_KEY",
                "docs": "https://developers.greenhouse.io/harvest",
            },
            "lever": {
                "configured": settings.lever_configured(),
                "status": "ready" if settings.lever_configured() else "needs_credentials",
                "env_var": "LEVER_API_KEY",
                "docs": "https://hire.lever.co/developer/documentation",
            },
            "bullhorn": {
                "configured": settings.bullhorn_configured(),
                "status": "ready" if settings.bullhorn_configured() else "needs_credentials",
                "env_vars": ["BULLHORN_CLIENT_ID", "BULLHORN_CLIENT_SECRET", "BULLHORN_USERNAME", "BULLHORN_PASSWORD"],
                "docs": "https://bullhorn.github.io/rest-api-docs",
            },
        },
        "file": {
            "csv": {"status": "ready", "formats": ["csv"], "endpoint": "/sync/file"},
            "excel": {"status": "ready", "formats": ["xlsx"], "endpoint": "/sync/file"},
        },
        "blocked": {
            src: {
                "status": "blocked",
                "reason": "No official public API available. See CONNECTOR_AUDIT.md.",
                "workaround": CONNECTOR_WORKAROUNDS.get(src, ""),
            }
            for src in sorted(BLOCKED_SOURCES)
        },
    }


@app.get("/connectors/{source_type}/status", tags=["Connectors"])
def connector_status(source_type: str):
    """Test a specific connector's connection and return detailed status."""
    connector = _build_connector(source_type)
    result = connector.test_connection()
    return {"source": source_type, **result}


@app.post("/connectors/{source_type}/sync", tags=["Connectors"])
async def sync_live_connector(
    source_type: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Trigger a live sync from Greenhouse, Lever, or Bullhorn."""
    if source_type in BLOCKED_SOURCES:
        connector = _build_connector(source_type)
        return connector.test_connection()

    if source_type not in LIVE_SOURCES:
        raise HTTPException(400, f"'{source_type}' is not a syncable live source.")

    job = create_job(f"sync_{source_type}", {"source_type": source_type})
    background_tasks.add_task(_sync_source_job, job["job_id"], source_type)
    return JobResponse(**job)


async def _sync_source_job(job_id: str, source_type: str):
    from app.db import SessionLocal
    db = SessionLocal()
    try:
        update_job(job_id, status="running", progress=0.05)
        connector = _build_connector(source_type)

        status = connector.test_connection()
        if not status.get("success"):
            update_job(job_id, status="failed", error=status.get("message", "Connection failed"))
            return

        update_job(job_id, progress=0.2, result={"step": "Fetching jobs"})
        jobs = connector.fetch_jobs()
        update_job(job_id, progress=0.5, result={"step": "Fetching applications"})
        applications = connector.fetch_applications()

        source = db.query(SourceAccount).filter(SourceAccount.source_type == source_type).first()
        if not source:
            source = SourceAccount(
                source_type=source_type,
                display_name=source_type.title(),
                status="connected",
            )
            db.add(source)
            db.flush()

        update_job(job_id, progress=0.7, result={"step": "Normalizing and storing"})
        records = _ingest_records(db, source, jobs, applications, source_type)

        source.last_sync_at = datetime.utcnow()
        source.records_total = records
        source.status = "connected"
        db.commit()

        log_action(db, "system", f"sync_{source_type}", after_json={"records": records})
        update_job(job_id, status="completed", progress=1.0, result={"records_synced": records, "source": source_type})
    except Exception as e:
        update_job(job_id, status="failed", error=str(e))
    finally:
        db.close()


def _ingest_records(db: Session, source: SourceAccount, jobs: list, applications: list, source_type: str) -> int:
    """Store normalized jobs and applications from a live connector sync."""
    total = 0

    for rj in jobs:
        norm = normalize_job(rj, source_type)
        company_name = norm.get("company") or "Unknown"
        company = db.query(Company).filter(Company.normalized_name == norm.get("normalized_company")).first()
        if not company and company_name:
            company = Company(
                name=company_name,
                normalized_name=norm.get("normalized_company", ""),
                source_account_id=source.id,
                external_id=norm.get("external_id"),
            )
            db.add(company)
            db.flush()

        if company and norm.get("external_id"):
            existing = db.query(JobRole).filter(
                JobRole.source_account_id == source.id,
                JobRole.external_id == norm["external_id"],
            ).first()
            if not existing:
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
        total += 1

    for ra in applications:
        norm_cand = normalize_candidate(ra, source_type)
        norm_app = normalize_application(ra, source_type)

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
            total += 1

    db.commit()
    return total


# ──────────────────────────────────────────────────────────────────────────────
# File Upload (CSV + Excel)
# ──────────────────────────────────────────────────────────────────────────────

@app.post("/sync/file", tags=["Sync"])
async def sync_file(
    file: UploadFile = File(...),
    confirm_import: bool = Query(False, description="Set true to actually import; false returns preview only"),
    db: Session = Depends(get_db),
):
    """Upload a CSV or Excel (.xlsx) file to import candidates/jobs."""
    from app.connectors.csv_connector import CSVConnector

    content = await file.read()
    filename = file.filename or "upload.csv"
    is_excel = filename.lower().endswith((".xlsx", ".xls"))

    connector = CSVConnector(content, filename)
    status = connector.test_connection()
    if not status.get("success"):
        raise HTTPException(400, status["message"])

    jobs = connector.fetch_jobs()
    candidates = connector.fetch_candidates()
    apps = connector.fetch_applications()

    preview = {
        "jobs": jobs[:5],
        "candidates": candidates[:5],
        "applications": apps[:5],
    }

    if not confirm_import:
        return {
            "filename": filename,
            "format": "excel" if is_excel else "csv",
            "columns": status.get("columns", []),
            "jobs_found": len(jobs),
            "candidates_found": len(candidates),
            "applications_found": len(apps),
            "message": "Preview ready. Set confirm_import=true to import.",
            "preview": preview,
        }

    # Confirmed import — find or create a CSV source account
    source = db.query(SourceAccount).filter(
        SourceAccount.source_type == "csv",
        SourceAccount.display_name == filename,
    ).first()
    if not source:
        source = SourceAccount(
            source_type="csv",
            display_name=filename,
            status="connected",
        )
        db.add(source)
        db.flush()

    records = _ingest_records(db, source, jobs, apps, "csv")
    source.last_sync_at = datetime.utcnow()
    source.records_total = records
    db.commit()

    log_action(db, "user", "csv_import", after_json={"filename": filename, "records": records})
    return {
        "filename": filename,
        "format": "excel" if is_excel else "csv",
        "jobs_found": len(jobs),
        "candidates_found": len(candidates),
        "applications_found": len(apps),
        "records_imported": records,
        "message": f"Imported {records} records from {filename}.",
    }


# Keep backwards-compat alias
@app.post("/sync/csv", tags=["Sync"])
async def sync_csv_legacy(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Deprecated — use /sync/file instead."""
    return await sync_file(file=file, confirm_import=False, db=db)


# ──────────────────────────────────────────────────────────────────────────────
# AgentBox Async Job Lifecycle
# ──────────────────────────────────────────────────────────────────────────────

SUPPORTED_TASKS = [
    "sync_all_sources", "normalize_import", "reconcile_candidates",
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
        elif task == "sync_all_sources":
            result = await _sync_all_live(job_id, db)
        else:
            result = {"message": f"Task '{task}' completed."}
        update_job(job_id, status="completed", progress=1.0, result=result)
    except Exception as e:
        update_job(job_id, status="failed", error=str(e))
    finally:
        db.close()


async def _full_pipeline_refresh(job_id: str, db: Session) -> Dict[str, Any]:
    update_job(job_id, progress=0.10, result={"step": "Syncing live sources"})
    sync_result = await _sync_all_live(job_id, db)

    update_job(job_id, progress=0.35, result={"step": "Normalizing jobs & pay rates"})
    await asyncio.sleep(0.05)

    update_job(job_id, progress=0.45, result={"step": "Mapping pipeline stages"})
    await asyncio.sleep(0.05)

    update_job(job_id, progress=0.55, result={"step": "Reconciling candidates"})
    dupes = find_duplicate_candidates(db)
    await asyncio.sleep(0.05)

    update_job(job_id, progress=0.65, result={"step": "Calculating metrics"})
    metrics = calculate_metrics(db)
    await asyncio.sleep(0.05)

    update_job(job_id, progress=0.75, result={"step": "Detecting anomalies"})
    anomaly_dicts = detect_all_anomalies(db)
    save_anomalies(db, anomaly_dicts)
    metrics["anomaly_count"] = len(anomaly_dicts)
    await asyncio.sleep(0.05)

    update_job(job_id, progress=0.85, result={"step": "Generating manager report"})
    anomalies_db = db.query(Anomaly).filter(Anomaly.status == "open").all()
    summary = generate_report(metrics, anomaly_dicts)
    narrative = generate_narrative_summary(metrics, anomalies_db)
    await asyncio.sleep(0.05)

    update_job(job_id, progress=0.95, result={"step": "Preparing export"})
    sheet_preview = generate_sheet_preview(db)
    actions = get_recommended_actions(metrics, anomalies_db)

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
        "sync": sync_result,
    }


async def _sync_all_live(job_id: str, db: Session) -> Dict[str, Any]:
    """
    Attempt sync from each configured live connector.
    Skips connectors with missing credentials (returns needs_credentials instead of failing).
    """
    total_records = 0
    connector_results: Dict[str, Any] = {}

    for source_type in ("greenhouse", "lever", "bullhorn"):
        connector = _build_connector(source_type)
        status = connector.test_connection()
        if not status.get("success"):
            connector_results[source_type] = status.get("status", "skipped")
            continue

        source = db.query(SourceAccount).filter(SourceAccount.source_type == source_type).first()
        if not source:
            connector_results[source_type] = "no_source_account"
            continue

        try:
            jobs = connector.fetch_jobs()
            applications = connector.fetch_applications()
            records = _ingest_records(db, source, jobs, applications, source_type)
            source.last_sync_at = datetime.utcnow()
            source.records_total = records
            source.status = "connected"
            db.commit()
            total_records += records
            connector_results[source_type] = f"ok:{records}"
        except Exception as e:
            connector_results[source_type] = f"error:{e}"

    return {"records_synced": total_records, "connectors": connector_results}


# ──────────────────────────────────────────────────────────────────────────────
# Onboarding
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/onboarding/status", tags=["Onboarding"])
def onboarding_status(db: Session = Depends(get_db)):
    """
    Return whether the instance has been set up.
    Checks: at least one source account exists, at least one connector configured.
    """
    sources = db.query(SourceAccount).all()
    has_sources = len(sources) > 0
    has_live_connector = settings.greenhouse_configured() or settings.lever_configured() or settings.bullhorn_configured()
    has_file_connector = any(s.source_type == "csv" for s in sources)
    has_candidates = db.query(Candidate).first() is not None

    steps = [
        {
            "key": "source_connected",
            "label": "Connect a data source",
            "complete": has_sources,
            "description": "Connect Greenhouse, Lever, Bullhorn, or upload a CSV/Excel file.",
        },
        {
            "key": "candidates_imported",
            "label": "Import candidate records",
            "complete": has_candidates,
            "description": "At least one candidate must be in the system.",
        },
        {
            "key": "llm_configured",
            "label": "Configure LLM provider",
            "complete": settings.llm_available(),
            "description": "Set GMI_MAAS_BASE_URL + GMI_MAAS_API_KEY (or LOCAL_LLM_*) for AI features.",
        },
    ]
    complete = all(s["complete"] for s in steps)
    return {
        "onboarding_complete": complete,
        "steps": steps,
        "sources": [
            {"id": s.id, "source_type": s.source_type, "display_name": s.display_name, "status": s.status}
            for s in sources
        ],
        "connector_status": {
            "greenhouse": "configured" if settings.greenhouse_configured() else "needs_credentials",
            "lever": "configured" if settings.lever_configured() else "needs_credentials",
            "bullhorn": "configured" if settings.bullhorn_configured() else "needs_credentials",
            "google_sheets": "configured" if settings.google_sheets_configured() else "needs_credentials",
        },
    }


# ──────────────────────────────────────────────────────────────────────────────
# Demo / Admin
# ──────────────────────────────────────────────────────────────────────────────

@app.post("/demo/seed", response_model=SeedResponse, tags=["Demo"])
def demo_seed(db: Session = Depends(get_db)):
    if db.query(SourceAccount).first():
        return SeedResponse(
            message="Already seeded. Use /demo/reset first.",
            sources_created=0, companies_created=0, roles_created=0,
            candidates_created=0, applications_created=0,
        )
    result = seed_demo_data(db)
    log_action(db, "user", "demo_seed", after_json=result)
    return SeedResponse(message="Demo data seeded successfully.", **result)


@app.post("/demo/reset", response_model=ResetResponse, tags=["Demo"])
def demo_reset(db: Session = Depends(get_db)):
    tables = reset_demo_data(db)
    return ResetResponse(message="Demo data reset. Run /demo/seed to re-populate.", tables_cleared=tables)


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
# Candidates
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/candidates", tags=["Candidates"])
def list_candidates(
    limit: int = Query(100, le=500),
    stage: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Candidate).filter(Candidate.is_merged_into == None)
    candidates = query.limit(limit).all()
    result = []
    for c in candidates:
        active_apps = [a for a in c.applications if a.status == "active"]
        latest_stage = active_apps[-1].canonical_stage if active_apps else None
        if stage and latest_stage != stage:
            continue
        result.append({
            "id": c.id, "full_name": c.full_name,
            "email_masked": c.email_display_masked,
            "phone_masked": c.phone_display_masked,
            "location": c.location, "current_title": c.current_title,
            "application_count": len(c.applications),
            "current_stage": latest_stage,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        })
    return {"candidates": result, "total": len(result)}


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


@app.get("/candidates/{candidate_id}", tags=["Candidates"])
def get_candidate(candidate_id: int, db: Session = Depends(get_db)):
    c = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not c:
        raise HTTPException(404, "Candidate not found")
    return {
        "id": c.id,
        "full_name": c.full_name,
        "email_masked": c.email_display_masked,
        "phone_masked": c.phone_display_masked,
        "location": c.location,
        "current_title": c.current_title,
        "current_company": c.current_company,
        "applications": [
            {
                "id": a.id,
                "job_role_id": a.job_role_id,
                "role_title": a.job_role.title if a.job_role else None,
                "company_name": a.job_role.company.name if (a.job_role and a.job_role.company) else None,
                "raw_stage": a.raw_stage,
                "canonical_stage": a.canonical_stage,
                "status": a.status,
                "applied_at": a.applied_at.isoformat() if a.applied_at else None,
                "last_activity_at": a.last_activity_at.isoformat() if a.last_activity_at else None,
                "recruiter_owner": a.recruiter_owner,
                "source": a.source,
            }
            for a in c.applications
        ],
    }


# ──────────────────────────────────────────────────────────────────────────────
# Roles — with candidate analysis
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/roles", tags=["Roles"])
def list_roles(db: Session = Depends(get_db)):
    return {"roles": calculate_role_metrics(db)}


@app.get("/roles/{role_id}/candidates", tags=["Roles"])
def role_candidates(role_id: int, db: Session = Depends(get_db)):
    """List candidates for a specific role, with AI analysis if LLM is available."""
    role = db.query(JobRole).filter(JobRole.id == role_id).first()
    if not role:
        raise HTTPException(404, "Role not found")

    apps = db.query(Application).filter(
        Application.job_role_id == role_id,
        Application.status == "active",
    ).all()

    candidates_data = []
    for app in apps:
        c = app.candidate
        if not c:
            continue
        candidates_data.append({
            "candidate_id": c.id,
            "full_name": c.full_name,
            "location": c.location,
            "current_title": c.current_title,
            "canonical_stage": app.canonical_stage,
            "raw_stage": app.raw_stage,
            "applied_at": app.applied_at.isoformat() if app.applied_at else None,
            "recruiter_owner": app.recruiter_owner,
        })

    analysis = None
    if settings.llm_available() and candidates_data:
        from app.services.llm import analyze_candidates_for_role
        analysis = analyze_candidates_for_role(role, candidates_data)

    return {
        "role": {
            "id": role.id,
            "title": role.title,
            "openings_count": role.openings_count,
            "status": role.status,
            "location_city": role.location_city,
            "location_state": role.location_state,
            "pay_min": role.pay_min,
            "pay_max": role.pay_max,
            "pay_unit": role.pay_unit,
        },
        "candidates": candidates_data,
        "candidate_count": len(candidates_data),
        "analysis": analysis,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Action Drafting
# ──────────────────────────────────────────────────────────────────────────────

@app.post("/actions/draft", tags=["Actions"])
def draft_action(request: Dict[str, Any], db: Session = Depends(get_db)):
    """
    Draft a recruiter action for a candidate.
    Supported action types: advance_stage, send_update, schedule_interview, reject, make_offer
    """
    from app.services.actions import draft_recruiter_action
    action_type = request.get("action_type", "send_update")
    candidate_id = request.get("candidate_id")
    context = request.get("context", {})

    candidate = None
    if candidate_id:
        candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()

    result = draft_recruiter_action(action_type, candidate, context, settings)
    log_action(db, "user", "draft_action", "candidate", candidate_id, after_json={"action_type": action_type})
    return result


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


@app.get("/settings/connectors", tags=["Settings"])
def connector_settings():
    """Return which connectors are configured (no credential values — just booleans)."""
    return {
        "greenhouse": {"configured": settings.greenhouse_configured()},
        "lever": {"configured": settings.lever_configured()},
        "bullhorn": {"configured": settings.bullhorn_configured()},
        "google_sheets": {"configured": settings.google_sheets_configured()},
        "gmi_maas": {"configured": settings.gmi_configured()},
    }
