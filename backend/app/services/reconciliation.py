from typing import List, Dict, Any
from difflib import SequenceMatcher
from sqlalchemy.orm import Session
from app.models import Candidate, Application


def _name_similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


def find_duplicate_candidates(db: Session) -> List[Dict[str, Any]]:
    candidates = db.query(Candidate).filter(Candidate.is_merged_into == None).all()
    suggestions = []
    checked = set()

    for i, a in enumerate(candidates):
        for j, b in enumerate(candidates):
            if i >= j:
                continue
            pair_key = (min(a.id, b.id), max(a.id, b.id))
            if pair_key in checked:
                continue
            checked.add(pair_key)

            confidence, reason = _compute_merge_confidence(a, b)
            if confidence >= 0.80:
                suggestions.append({
                    "candidate_a": _candidate_safe(a),
                    "candidate_b": _candidate_safe(b),
                    "confidence": round(confidence, 2),
                    "reason": reason,
                    "recommended_action": "merge" if confidence >= 0.90 else "review",
                })

    suggestions.sort(key=lambda x: x["confidence"], reverse=True)
    return suggestions


def _compute_merge_confidence(a: Candidate, b: Candidate) -> tuple:
    reasons = []
    score = 0.0

    # Exact email hash match
    if a.email_hash and b.email_hash and a.email_hash == b.email_hash:
        score = max(score, 0.97)
        reasons.append("Same email address")

    # Exact phone hash match
    if a.phone_hash and b.phone_hash and a.phone_hash == b.phone_hash:
        score = max(score, 0.92)
        reasons.append("Same phone number")

    name_sim = _name_similarity(a.full_name, b.full_name)

    # Same name + same location
    if name_sim >= 0.85 and a.location and b.location and a.location.lower() == b.location.lower():
        score = max(score, 0.88)
        reasons.append(f"Similar name ({name_sim:.0%}) and same location")

    # Same name + same current title
    if name_sim >= 0.85 and a.current_title and b.current_title:
        title_sim = _name_similarity(a.current_title, b.current_title)
        if title_sim >= 0.8:
            score = max(score, 0.82)
            reasons.append(f"Similar name and matching current title")

    # Very similar name alone
    if name_sim >= 0.95 and not reasons:
        score = max(score, 0.75)
        reasons.append(f"Very similar name ({name_sim:.0%})")

    return score, ". ".join(reasons) if reasons else "No strong match"


def _candidate_safe(c: Candidate) -> Dict[str, Any]:
    return {
        "id": c.id,
        "full_name": c.full_name,
        "email_masked": c.email_display_masked,
        "phone_masked": c.phone_display_masked,
        "location": c.location,
        "current_title": c.current_title,
        "current_company": c.current_company,
        "created_at": str(c.created_at),
    }


def merge_candidates(db: Session, primary_id: int, secondary_id: int, actor: str = "user") -> Dict[str, Any]:
    primary = db.query(Candidate).filter(Candidate.id == primary_id).first()
    secondary = db.query(Candidate).filter(Candidate.id == secondary_id).first()

    if not primary or not secondary:
        return {"success": False, "error": "Candidate not found"}

    # Reassign all applications from secondary to primary
    apps = db.query(Application).filter(Application.candidate_id == secondary_id).all()
    for app in apps:
        app.candidate_id = primary_id

    # Mark secondary as merged
    secondary.is_merged_into = primary_id

    # Merge email/phone data if primary is missing it
    if not primary.email_hash and secondary.email_hash:
        primary.email_hash = secondary.email_hash
        primary.email_display_masked = secondary.email_display_masked
    if not primary.phone_hash and secondary.phone_hash:
        primary.phone_hash = secondary.phone_hash
        primary.phone_display_masked = secondary.phone_display_masked

    db.commit()

    from app.services.audit import log_action
    log_action(db, actor, "merge_candidates", "candidate", primary_id,
               before_json={"secondary_id": secondary_id},
               after_json={"applications_reassigned": len(apps)})

    return {
        "success": True,
        "primary_id": primary_id,
        "secondary_id": secondary_id,
        "applications_reassigned": len(apps),
    }
