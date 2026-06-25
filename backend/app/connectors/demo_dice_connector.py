"""Demo connector simulating Dice.com-style tech job board data.
NOTE: Synthetic demo data only. Not a real Dice API integration.
"""
from typing import Any, Dict, List
from app.connectors.base import BaseConnector


DEMO_JOBS = [
    {
        "dice_id": "dice_001",
        "title": "Java Backend Engineer",
        "employer": "BluePeak Retail",
        "location_city": "Remote",
        "location_state": "",
        "telecommute": True,
        "salary_from": 120000,
        "salary_to": 150000,
        "salary_period": "Annual",
        "employment_type": "FULLTIME",
        "status": "open",
        "date_posted": "2026-05-10",
        "recruiter_name": "Priya Shah",
    }
]

DEMO_CANDIDATES = [
    {"dice_profile_id": "dice_cand_001", "name": "Ethan Clark", "email": "ethan.clark@email.com", "phone": "512-555-0901", "location": "Austin, TX", "title": "Senior Java Developer", "applied_to": "dice_001", "application_status": "new applicant", "apply_date": "2026-05-12"},
    {"dice_profile_id": "dice_cand_002", "name": "Samantha Reid", "email": "s.reid@email.com", "phone": "512-555-0902", "location": "Remote", "title": "Backend Engineer", "applied_to": "dice_001", "application_status": "phone screen", "apply_date": "2026-05-14"},
    {"dice_profile_id": "dice_cand_003", "name": "Vijay Krishnan", "email": "v.krishnan@email.com", "phone": "512-555-0903", "location": "Dallas, TX", "title": "Java Engineer", "applied_to": "dice_001", "application_status": "sent to client", "apply_date": "2026-05-15"},
    {"dice_profile_id": "dice_cand_004", "name": "Emily Foster", "email": "emily.foster@email.com", "phone": "512-555-0904", "location": "Remote", "title": "Software Engineer", "applied_to": "dice_001", "application_status": "interview", "apply_date": "2026-05-16"},
]


class DemoDiceConnector(BaseConnector):
    source_type = "dice"
    display_name = "Dice (Demo)"
    is_demo = True

    def test_connection(self) -> Dict[str, Any]:
        return {"success": True, "message": "Demo mode — no real credentials required."}

    def fetch_jobs(self) -> List[Dict[str, Any]]:
        return [{
            "id": j["dice_id"],
            "title": j["title"],
            "company": j["employer"],
            "location": "Remote" if j.get("telecommute") else f"{j.get('location_city', '')}, {j.get('location_state', '')}",
            "pay_min": j.get("salary_from"),
            "pay_max": j.get("salary_to"),
            "pay_unit": "salary" if j.get("salary_period") == "Annual" else "hourly",
            "status": j.get("status", "open"),
            "recruiter": j.get("recruiter_name"),
        } for j in DEMO_JOBS]

    def fetch_candidates(self) -> List[Dict[str, Any]]:
        return [{
            "id": c["dice_profile_id"],
            "full_name": c["name"],
            "email": c["email"],
            "phone": c["phone"],
            "location": c["location"],
            "current_title": c["title"],
        } for c in DEMO_CANDIDATES]

    def fetch_applications(self) -> List[Dict[str, Any]]:
        return [{
            "applicationId": c["dice_profile_id"],
            "candidateId": c["dice_profile_id"],
            "jobId": c["applied_to"],
            "name": c["name"],
            "email": c["email"],
            "phone": c["phone"],
            "stage": c["application_status"],
            "appliedAt": c.get("apply_date"),
        } for c in DEMO_CANDIDATES]
