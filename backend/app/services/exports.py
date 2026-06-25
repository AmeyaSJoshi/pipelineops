import csv
import io
from datetime import datetime
from typing import Any, Dict, List
from sqlalchemy.orm import Session
from app.services.reporting import calculate_metrics, calculate_role_metrics
from app.models import Application, Candidate, Anomaly


def generate_csv_export(db: Session) -> Dict[str, str]:
    """Generate CSV content for all 4 export tabs."""
    return {
        "pipeline_summary": _pipeline_summary_csv(db),
        "role_detail": _role_detail_csv(db),
        "candidate_stage_detail": _candidate_stage_csv(db),
        "anomalies": _anomalies_csv(db),
    }


def _pipeline_summary_csv(db: Session) -> str:
    metrics = calculate_metrics(db)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Client", "Open Roles", "Active Candidates", "Submitted", "Interviews", "Offers", "Placements", "Hit Rate", "Stale Roles", "Issues"])
    roles_by_client = metrics.get("roles_by_client", {})
    for client, count in roles_by_client.items():
        writer.writerow([
            client, count,
            metrics.get("active_candidates", 0),
            metrics.get("submitted_to_client_count", 0),
            metrics.get("interview_count", 0),
            metrics.get("offer_count", 0),
            metrics.get("placement_count", 0),
            f"{metrics.get('overall_hit_rate', 0):.1%}",
            metrics.get("stale_role_count", 0),
            metrics.get("anomaly_count", 0),
        ])
    return output.getvalue()


def _role_detail_csv(db: Session) -> str:
    roles = calculate_role_metrics(db)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Role ID", "Client", "Title", "Location", "Pay", "Openings",
        "Status", "Applicants", "Submitted", "Interviews", "Offers",
        "Placements", "Hit Rate", "Last Updated", "Recruiter"
    ])
    for r in roles:
        writer.writerow([
            r["id"], r["company_name"], r["title"], r["location"],
            r["pay_display"], r["openings_count"], r["status"],
            r["applicant_count"], r["submitted_count"], r["interview_count"],
            r["offer_count"], r["placement_count"],
            f"{r['hit_rate']:.1%}", r["last_updated"], r["recruiter_owner"] or ""
        ])
    return output.getvalue()


def _candidate_stage_csv(db: Session) -> str:
    apps = db.query(Application).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Candidate", "Masked Email", "Role", "Client", "Source",
        "Canonical Stage", "Raw Stage", "Last Activity", "Recruiter", "Issue Flag"
    ])
    for app in apps:
        candidate = app.candidate
        role = app.job_role
        name = candidate.full_name if candidate else "Unknown"
        email = candidate.email_display_masked if candidate else ""
        role_title = role.title if role else "Unknown"
        company = role.company.name if role and role.company else "Unknown"
        last_act = app.last_activity_at.isoformat() if app.last_activity_at else ""
        issue = ""
        if app.canonical_stage == "offer" and not app.offer_amount:
            issue = "Missing offer amount"
        elif app.canonical_stage == "unknown":
            issue = "Unmapped stage"
        writer.writerow([
            name, email, role_title, company,
            app.source or "", app.canonical_stage, app.raw_stage or "",
            last_act, app.recruiter_owner or "", issue
        ])
    return output.getvalue()


def _anomalies_csv(db: Session) -> str:
    anomalies = db.query(Anomaly).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Severity", "Category", "Entity", "Problem", "Recommended Fix", "Status"])
    for a in anomalies:
        entity = f"{a.related_entity_type} #{a.related_entity_id}" if a.related_entity_type else ""
        writer.writerow([
            a.severity, a.category, entity,
            a.title, a.recommended_fix, a.status
        ])
    return output.getvalue()


def generate_sheet_preview(db: Session) -> Dict[str, Any]:
    """Generate a mock spreadsheet preview structure for the frontend."""
    roles = calculate_role_metrics(db)[:10]
    metrics = calculate_metrics(db)
    anomalies = db.query(Anomaly).filter(Anomaly.status == "open").limit(10).all()

    return {
        "tabs": [
            {
                "name": "Pipeline Summary",
                "headers": ["Client", "Open Roles", "Submitted", "Interviews", "Offers", "Hit Rate"],
                "rows": [
                    [client, count, metrics.get("submitted_to_client_count", 0),
                     metrics.get("interview_count", 0), metrics.get("offer_count", 0),
                     f"{metrics.get('overall_hit_rate', 0):.1%}"]
                    for client, count in metrics.get("roles_by_client", {}).items()
                ][:10],
            },
            {
                "name": "Role Detail",
                "headers": ["Title", "Client", "Location", "Pay", "Applicants", "Submitted", "Hit Rate"],
                "rows": [
                    [r["title"], r["company_name"], r["location"],
                     r["pay_display"], r["applicant_count"], r["submitted_count"],
                     f"{r['hit_rate']:.1%}"]
                    for r in roles
                ],
            },
            {
                "name": "Anomalies",
                "headers": ["Severity", "Category", "Issue", "Recommended Fix"],
                "rows": [
                    [a.severity, a.category, a.title, a.recommended_fix]
                    for a in anomalies
                ],
            }
        ],
        "generated_at": datetime.utcnow().isoformat(),
        "note": "Demo export generated locally. Connect Google Sheets credentials to sync to a real spreadsheet.",
    }
