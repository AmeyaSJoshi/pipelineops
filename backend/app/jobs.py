"""In-memory async job store for MVP. TODO: Replace with Redis/Celery for production."""
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

_job_store: Dict[str, Dict[str, Any]] = {}


def create_job(task: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
    job_id = str(uuid.uuid4())
    job = {
        "job_id": job_id,
        "task": task,
        "params": params or {},
        "status": "pending",
        "progress": 0,
        "result": None,
        "error": None,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }
    _job_store[job_id] = job
    return job


def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    return _job_store.get(job_id)


def update_job(job_id: str, **kwargs) -> Optional[Dict[str, Any]]:
    job = _job_store.get(job_id)
    if not job:
        return None
    job.update(kwargs)
    job["updated_at"] = datetime.utcnow().isoformat()
    return job


def list_jobs(limit: int = 20) -> list:
    jobs = sorted(_job_store.values(), key=lambda j: j["created_at"], reverse=True)
    return jobs[:limit]
