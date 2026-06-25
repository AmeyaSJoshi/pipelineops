from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from app.models import JobRole, Application, Candidate, Anomaly, Company


ACTIVE_STAGES = [
    "applied", "recruiter_screen", "qualified",
    "submitted_to_client", "client_review",
    "interview_scheduled", "interview_completed",
    "offer", "placed",
]
SUBMITTED_STAGES = ["submitted_to_client", "client_review", "interview_scheduled", "interview_completed", "offer", "placed"]
INTERVIEW_STAGES = ["interview_scheduled", "interview_completed", "offer", "placed"]
OFFER_STAGES = ["offer", "placed"]
PLACED_STAGES = ["placed"]


def _safe_rate(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 4)


def calculate_metrics(db: Session) -> Dict[str, Any]:
    roles = db.query(JobRole).filter(JobRole.status == "open").all()
    all_apps = db.query(Application).filter(Application.status == "active").all()
    candidates = db.query(Candidate).filter(Candidate.is_merged_into == None).all()
    anomalies = db.query(Anomaly).filter(Anomaly.status == "open").all()

    open_roles = len(roles)
    active_candidates = len([c for c in candidates if any(
        a.canonical_stage in ACTIVE_STAGES for a in c.applications
    )])

    total_apps = len(all_apps)
    submitted = sum(1 for a in all_apps if a.canonical_stage in SUBMITTED_STAGES)
    interviews = sum(1 for a in all_apps if a.canonical_stage in INTERVIEW_STAGES)
    offers = sum(1 for a in all_apps if a.canonical_stage in OFFER_STAGES)
    placements = sum(1 for a in all_apps if a.canonical_stage in PLACED_STAGES)

    stale_cutoff = datetime.utcnow() - timedelta(days=14)
    stale_roles = sum(1 for r in roles if r.updated_at < stale_cutoff)

    missing_pay = sum(1 for r in roles if r.pay_min is None and r.pay_max is None)

    # Pay rate avg for roles that have data
    pay_values = [r.pay_max for r in roles if r.pay_max]
    avg_pay = round(sum(pay_values) / len(pay_values), 2) if pay_values else None

    # Roles by client
    roles_by_client: Dict[str, int] = {}
    for role in roles:
        client = role.company.name if role.company else "Unknown"
        roles_by_client[client] = roles_by_client.get(client, 0) + 1

    # Candidates by stage
    candidates_by_stage: Dict[str, int] = {}
    for app in all_apps:
        stage = app.canonical_stage or "unknown"
        candidates_by_stage[stage] = candidates_by_stage.get(stage, 0) + 1

    return {
        "open_roles": open_roles,
        "active_candidates": active_candidates,
        "total_applications": total_apps,
        "applicants_per_role": round(total_apps / open_roles, 1) if open_roles else 0,
        "submitted_to_client_count": submitted,
        "interview_count": interviews,
        "offer_count": offers,
        "placement_count": placements,
        "submit_rate": _safe_rate(submitted, total_apps),
        "interview_rate": _safe_rate(interviews, submitted),
        "offer_rate": _safe_rate(offers, interviews),
        "placement_rate": _safe_rate(placements, offers),
        "overall_hit_rate": _safe_rate(placements, total_apps),
        "stale_role_count": stale_roles,
        "missing_pay_rate_count": missing_pay,
        "duplicate_candidate_count": 0,  # updated after reconciliation
        "average_pay_rate": avg_pay,
        "roles_by_client": roles_by_client,
        "candidates_by_stage": candidates_by_stage,
        "anomaly_count": len(anomalies),
    }


def calculate_role_metrics(db: Session) -> List[Dict[str, Any]]:
    roles = db.query(JobRole).all()
    result = []
    for role in roles:
        apps = role.applications
        total = len(apps)
        submitted = sum(1 for a in apps if a.canonical_stage in SUBMITTED_STAGES)
        interviews = sum(1 for a in apps if a.canonical_stage in INTERVIEW_STAGES)
        offers = sum(1 for a in apps if a.canonical_stage in OFFER_STAGES)
        placed = sum(1 for a in apps if a.canonical_stage in PLACED_STAGES)
        hit_rate = _safe_rate(placed, total)
        pay_display = _format_pay(role.pay_min, role.pay_max, role.pay_unit)
        location = _format_location(role.location_city, role.location_state, role.remote_type)
        result.append({
            "id": role.id,
            "title": role.title,
            "normalized_title": role.normalized_title,
            "company_id": role.company_id,
            "company_name": role.company.name if role.company else "Unknown",
            "location": location,
            "location_city": role.location_city,
            "location_state": role.location_state,
            "remote_type": role.remote_type,
            "pay_display": pay_display,
            "pay_min": role.pay_min,
            "pay_max": role.pay_max,
            "pay_unit": role.pay_unit,
            "openings_count": role.openings_count,
            "status": role.status,
            "recruiter_owner": role.recruiter_owner,
            "applicant_count": total,
            "submitted_count": submitted,
            "interview_count": interviews,
            "offer_count": offers,
            "placement_count": placed,
            "hit_rate": hit_rate,
            "last_updated": role.updated_at.isoformat(),
            "created_at": role.created_at.isoformat(),
        })
    return result


def _format_pay(pay_min, pay_max, pay_unit) -> str:
    if pay_unit == "unknown" and not pay_min and not pay_max:
        return "Not specified"
    suffix = "/hr" if pay_unit == "hourly" else ("/yr" if pay_unit == "salary" else "")
    if pay_min and pay_max:
        if pay_unit == "salary":
            return f"${pay_min/1000:.0f}k–${pay_max/1000:.0f}k{suffix}"
        return f"${pay_min:.0f}–${pay_max:.0f}{suffix}"
    if pay_max:
        return f"Up to ${pay_max:.0f}{suffix}"
    return "Not specified"


def _format_location(city, state, remote_type) -> str:
    if remote_type == "remote":
        return "Remote"
    if remote_type == "hybrid" and city and state:
        return f"Hybrid - {city}, {state}"
    if city and state:
        return f"{city}, {state}"
    if city:
        return city
    return "Unknown"


def generate_narrative_summary(metrics: Dict[str, Any], anomalies: List[Any]) -> str:
    open_roles = metrics.get("open_roles", 0)
    active_cands = metrics.get("active_candidates", 0)
    submitted = metrics.get("submitted_to_client_count", 0)
    interviews = metrics.get("interview_count", 0)
    offers = metrics.get("offer_count", 0)
    placed = metrics.get("placement_count", 0)
    stale = metrics.get("stale_role_count", 0)
    anomaly_count = metrics.get("anomaly_count", 0)
    hit_rate = metrics.get("overall_hit_rate", 0)
    submit_rate = metrics.get("submit_rate", 0)

    high_anomalies = [a for a in anomalies if a.severity == "high"] if anomalies else []

    parts = [
        f"Pipeline Overview: {open_roles} open roles with {active_cands} active candidates.",
        f"Funnel: {submitted} submitted to clients → {interviews} in interviews → {offers} offers → {placed} placements.",
        f"Submit rate: {submit_rate:.1%}, Overall hit rate: {hit_rate:.1%}.",
    ]

    if stale > 0:
        parts.append(f"⚠ {stale} roles are stale (no updates in 14+ days) and need attention.")

    if len(high_anomalies) > 0:
        parts.append(f"🚨 {len(high_anomalies)} high-severity issues detected requiring immediate action.")

    if anomaly_count > 0:
        parts.append(f"Total issues found: {anomaly_count}. Review the Anomalies tab for recommended fixes.")

    if placed == 0 and offers > 0:
        parts.append("Offers have been extended but no placements confirmed — follow up with candidates on start dates.")
    elif placed > 0:
        parts.append(f"✓ {placed} placement{'s' if placed > 1 else ''} confirmed this cycle.")

    return " ".join(parts)


def get_recommended_actions(metrics: Dict[str, Any], anomalies: List[Any]) -> List[str]:
    actions = []
    if metrics.get("stale_role_count", 0) > 0:
        actions.append(f"Review {metrics['stale_role_count']} stale open roles and confirm status with clients.")
    if metrics.get("missing_pay_rate_count", 0) > 0:
        actions.append(f"Add pay rates to {metrics['missing_pay_rate_count']} roles missing compensation info.")
    submitted = metrics.get("submitted_to_client_count", 0)
    interviews = metrics.get("interview_count", 0)
    if submitted > 0 and interviews == 0:
        actions.append("Follow up with clients on submitted candidates — no interviews have been scheduled yet.")
    offers = metrics.get("offer_count", 0)
    placed = metrics.get("placement_count", 0)
    if offers > 0 and placed == 0:
        actions.append("Offers are outstanding — confirm start dates and close placements.")
    if metrics.get("submit_rate", 0) < 0.15:
        actions.append("Submit rate is below 15% — review screening criteria to increase qualified submissions.")
    if not actions:
        actions.append("Pipeline looks healthy — maintain current candidate flow and monitor for new anomalies.")
    return actions
