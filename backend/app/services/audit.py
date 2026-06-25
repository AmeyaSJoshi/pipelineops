from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from app.models import AuditLog


def log_action(
    db: Session,
    actor: str,
    action: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    before_json: Optional[Dict[str, Any]] = None,
    after_json: Optional[Dict[str, Any]] = None,
) -> AuditLog:
    entry = AuditLog(
        actor=actor,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        before_json=before_json,
        after_json=after_json,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
