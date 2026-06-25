"""Demo connector simulating Monster-style job board data.
NOTE: Synthetic demo data only. Not a real Monster API integration.
"""
from typing import Any, Dict, List
from app.connectors.base import BaseConnector


DEMO_JOBS = [
    {"monster_job_id": "mon_001", "job_title": "Robotics Technician", "job_location": "San Jose, CA", "compensation": "up to $45/hr", "job_type": "Contract", "job_status": "open", "posted": "2026-04-29", "account_manager": "David Chen"},
]

DEMO_APPLICANTS = [
    {"monster_id": "mon_app_001", "job_id": "mon_001", "first": "Andre", "last": "Martin", "email_addr": "a.martin@email.com", "phone_number": "408-555-0801", "city_state": "San Jose, CA", "current_job": "Electronics Technician", "app_status": "screened", "apply_ts": "2026-05-02"},
    {"monster_id": "mon_app_002", "job_id": "mon_001", "first": "Priya", "last": "Sharma", "email_addr": "priya.s@email.com", "phone_number": "408-555-0802", "city_state": "Santa Clara, CA", "current_job": "Automation Technician", "app_status": "submitted", "apply_ts": "2026-05-05"},
    {"monster_id": "mon_app_003", "job_id": "mon_001", "first": "Marcus", "last": "Bell", "email_addr": "marcus.bell@email.com", "phone_number": "408-555-0803", "city_state": "Fremont, CA", "current_job": "Field Technician", "app_status": "client review", "apply_ts": "2026-05-07"},
]


class DemoMonsterConnector(BaseConnector):
    source_type = "monster"
    display_name = "Monster (Demo)"
    is_demo = True

    def test_connection(self) -> Dict[str, Any]:
        return {"success": True, "message": "Demo mode — no real credentials required."}

    def fetch_jobs(self) -> List[Dict[str, Any]]:
        return [{
            "id": j["monster_job_id"],
            "title": j["job_title"],
            "location": j["job_location"],
            "pay_raw": j.get("compensation"),
            "status": j.get("job_status", "open"),
            "recruiter": j.get("account_manager"),
        } for j in DEMO_JOBS]

    def fetch_candidates(self) -> List[Dict[str, Any]]:
        return [{
            "id": a["monster_id"],
            "full_name": f"{a['first']} {a['last']}",
            "email": a["email_addr"],
            "phone": a["phone_number"],
            "location": a["city_state"],
            "current_title": a["current_job"],
        } for a in DEMO_APPLICANTS]

    def fetch_applications(self) -> List[Dict[str, Any]]:
        return [{
            "applicationId": a["monster_id"],
            "candidateId": a["monster_id"],
            "jobId": a["job_id"],
            "name": f"{a['first']} {a['last']}",
            "email": a["email_addr"],
            "phone": a["phone_number"],
            "stage": a["app_status"],
            "appliedAt": a.get("apply_ts"),
        } for a in DEMO_APPLICANTS]
