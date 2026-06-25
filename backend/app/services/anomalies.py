from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import JobRole, Application, Candidate, Anomaly


STALE_DAYS = 14


def detect_all_anomalies(db: Session) -> List[Dict[str, Any]]:
    anomalies = []
    anomalies.extend(_check_missing_pay_rate(db))
    anomalies.extend(_check_stale_roles(db))
    anomalies.extend(_check_offer_no_amount(db))
    anomalies.extend(_check_interview_no_date(db))
    anomalies.extend(_check_high_applicant_low_submit(db))
    anomalies.extend(_check_submitted_no_response(db))
    anomalies.extend(_check_duplicate_submissions(db))
    anomalies.extend(_check_offer_no_start_date(db))
    anomalies.extend(_check_role_status_conflict(db))
    return anomalies


def _check_missing_pay_rate(db: Session) -> List[Dict[str, Any]]:
    roles = db.query(JobRole).filter(
        JobRole.status == "open",
        JobRole.pay_min == None,
        JobRole.pay_max == None
    ).all()
    result = []
    for role in roles:
        company = role.company.name if role.company else "Unknown"
        result.append({
            "severity": "medium",
            "category": "missing_pay_rate",
            "title": f"{role.title} at {company} has no pay rate",
            "explanation": f"The open role '{role.title}' for {company} does not have a pay rate set. This may reduce candidate quality and response rates.",
            "recommended_fix": "Add pay rate information to the job posting or ATS record.",
            "related_entity_type": "job_role",
            "related_entity_id": role.id,
            "status": "open",
        })
    return result


def _check_stale_roles(db: Session) -> List[Dict[str, Any]]:
    cutoff = datetime.utcnow() - timedelta(days=STALE_DAYS)
    roles = db.query(JobRole).filter(
        JobRole.status == "open",
        JobRole.updated_at < cutoff
    ).all()
    result = []
    for role in roles:
        days_stale = (datetime.utcnow() - role.updated_at).days
        company = role.company.name if role.company else "Unknown"
        result.append({
            "severity": "high" if days_stale > 21 else "medium",
            "category": "stale_role",
            "title": f"{role.title} has not been updated in {days_stale} days",
            "explanation": f"The role '{role.title}' for {company} is still marked open but has had no candidate movement or source update in over {days_stale} days.",
            "recommended_fix": "Confirm whether the role is still active with the client or mark it paused/closed.",
            "related_entity_type": "job_role",
            "related_entity_id": role.id,
            "status": "open",
        })
    return result


def _check_offer_no_amount(db: Session) -> List[Dict[str, Any]]:
    apps = db.query(Application).filter(
        Application.canonical_stage == "offer",
        Application.offer_amount == None
    ).all()
    result = []
    for app in apps:
        candidate = app.candidate
        role = app.job_role
        name = candidate.full_name if candidate else "Unknown"
        title = role.title if role else "Unknown Role"
        result.append({
            "severity": "high",
            "category": "offer_missing_compensation",
            "title": f"Offer for {name} on {title} has no amount",
            "explanation": f"Application #{app.id} is in 'offer' stage but no offer amount is recorded. This makes it impossible to track offer data or client reporting.",
            "recommended_fix": "Add offer amount to the application record.",
            "related_entity_type": "application",
            "related_entity_id": app.id,
            "status": "open",
        })
    return result


def _check_interview_no_date(db: Session) -> List[Dict[str, Any]]:
    apps = db.query(Application).filter(
        Application.canonical_stage.in_(["interview_scheduled", "interview_completed"]),
        Application.last_activity_at == None
    ).all()
    result = []
    for app in apps:
        candidate = app.candidate
        role = app.job_role
        name = candidate.full_name if candidate else "Unknown"
        title = role.title if role else "Unknown Role"
        result.append({
            "severity": "medium",
            "category": "missing_interview_date",
            "title": f"{name} is in interview stage for {title} but has no interview date",
            "explanation": "The candidate is marked as interviewing but no interview date or last activity date is recorded.",
            "recommended_fix": "Update the application with the interview date or verify stage accuracy.",
            "related_entity_type": "application",
            "related_entity_id": app.id,
            "status": "open",
        })
    return result


def _check_high_applicant_low_submit(db: Session) -> List[Dict[str, Any]]:
    result = []
    roles = db.query(JobRole).filter(JobRole.status == "open").all()
    for role in roles:
        apps = role.applications
        total = len(apps)
        submitted = sum(1 for a in apps if a.canonical_stage in [
            "submitted_to_client", "client_review", "interview_scheduled",
            "interview_completed", "offer", "placed"
        ])
        if total >= 5 and submitted == 0:
            company = role.company.name if role.company else "Unknown"
            result.append({
                "severity": "high",
                "category": "high_applicant_zero_submit",
                "title": f"{role.title} has {total} applicants but 0 submitted to {company}",
                "explanation": f"This role has {total} applicants but none have been submitted to the client. This is a major pipeline bottleneck.",
                "recommended_fix": "Review applicants and submit qualified candidates to the client immediately.",
                "related_entity_type": "job_role",
                "related_entity_id": role.id,
                "status": "open",
            })
    return result


def _check_submitted_no_response(db: Session) -> List[Dict[str, Any]]:
    cutoff = datetime.utcnow() - timedelta(days=7)
    apps = db.query(Application).filter(
        Application.canonical_stage == "submitted_to_client",
        Application.last_activity_at < cutoff
    ).all()
    result = []
    for app in apps:
        if app.last_activity_at:
            days = (datetime.utcnow() - app.last_activity_at).days
            candidate = app.candidate
            role = app.job_role
            name = candidate.full_name if candidate else "Unknown"
            title = role.title if role else "Unknown Role"
            result.append({
                "severity": "medium",
                "category": "submitted_no_response",
                "title": f"{name} submitted to {title} {days} days ago with no client response",
                "explanation": f"Candidate was submitted to client {days} days ago but there has been no stage update or client feedback.",
                "recommended_fix": "Follow up with the client to get feedback on the submitted candidate.",
                "related_entity_type": "application",
                "related_entity_id": app.id,
                "status": "open",
            })
    return result


def _check_duplicate_submissions(db: Session) -> List[Dict[str, Any]]:
    # Check for same candidate_id + job_role_id with multiple applications
    from sqlalchemy import and_
    subq = (
        db.query(Application.candidate_id, Application.job_role_id, func.count().label("cnt"))
        .filter(Application.job_role_id != None)
        .group_by(Application.candidate_id, Application.job_role_id)
        .having(func.count() > 1)
        .subquery()
    )
    dupes = db.query(subq).all()
    result = []
    for row in dupes:
        cand_id, role_id, cnt = row
        candidate = db.query(Candidate).filter(Candidate.id == cand_id).first()
        role = db.query(JobRole).filter(JobRole.id == role_id).first()
        name = candidate.full_name if candidate else f"Candidate {cand_id}"
        title = role.title if role else f"Role {role_id}"
        result.append({
            "severity": "medium",
            "category": "duplicate_submission",
            "title": f"{name} submitted {cnt}x to {title}",
            "explanation": f"The same candidate appears {cnt} times on this role, likely from multiple source imports.",
            "recommended_fix": "Review and deduplicate application records, keeping the most recent.",
            "related_entity_type": "candidate",
            "related_entity_id": cand_id,
            "status": "open",
        })
    return result


def _check_offer_no_start_date(db: Session) -> List[Dict[str, Any]]:
    cutoff = datetime.utcnow() - timedelta(days=5)
    apps = db.query(Application).filter(
        Application.canonical_stage == "placed",
        Application.offer_amount == None
    ).all()
    result = []
    for app in apps:
        candidate = app.candidate
        role = app.job_role
        name = candidate.full_name if candidate else "Unknown"
        title = role.title if role else "Unknown Role"
        result.append({
            "severity": "medium",
            "category": "placement_missing_compensation",
            "title": f"Placed candidate {name} on {title} has no pay info",
            "explanation": "This candidate is marked as placed but no offer amount or pay rate is recorded. This blocks accurate placement reporting.",
            "recommended_fix": "Add compensation details to the placement record.",
            "related_entity_type": "application",
            "related_entity_id": app.id,
            "status": "open",
        })
    return result


def _check_role_status_conflict(db: Session) -> List[Dict[str, Any]]:
    # Find roles marked open that have no applications in 14+ days
    cutoff = datetime.utcnow() - timedelta(days=STALE_DAYS)
    roles = db.query(JobRole).filter(
        JobRole.status == "open",
        JobRole.created_at < cutoff
    ).all()
    result = []
    for role in roles:
        apps = role.applications
        if apps:
            last_active = max((a.last_activity_at for a in apps if a.last_activity_at), default=None)
            if last_active and last_active < cutoff:
                days = (datetime.utcnow() - last_active).days
                company = role.company.name if role.company else "Unknown"
                result.append({
                    "severity": "low",
                    "category": "role_no_recent_activity",
                    "title": f"{role.title} for {company} has no candidate activity in {days} days",
                    "explanation": f"This open role has candidates but no stage updates in {days} days, suggesting a stalled pipeline.",
                    "recommended_fix": "Review candidate stages and push stuck candidates forward or update their status.",
                    "related_entity_type": "job_role",
                    "related_entity_id": role.id,
                    "status": "open",
                })
    return result


def save_anomalies(db: Session, anomaly_dicts: List[Dict[str, Any]]) -> int:
    # Clear old open anomalies and replace
    db.query(Anomaly).filter(Anomaly.status == "open").delete()
    created = 0
    for a in anomaly_dicts:
        anomaly = Anomaly(
            severity=a["severity"],
            category=a["category"],
            title=a["title"],
            explanation=a["explanation"],
            recommended_fix=a["recommended_fix"],
            related_entity_type=a.get("related_entity_type"),
            related_entity_id=a.get("related_entity_id"),
            status="open",
        )
        db.add(anomaly)
        created += 1
    db.commit()
    return created
