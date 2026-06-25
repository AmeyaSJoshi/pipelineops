"""Demo connector simulating Greenhouse ATS data format.
NOTE: This is synthetic demo data only. Not a real Greenhouse API integration.
"""
from typing import Any, Dict, List
from app.connectors.base import BaseConnector


DEMO_JOBS = [
    {
        "id": 3001,
        "name": "Robotics Technician",
        "offices": [{"name": "San Jose"}],
        "location": {"name": "San Jose, CA"},
        "status": "open",
        "custom_fields": {"pay_range": "$35 - $45 an hour", "openings": 3},
        "hiring_team": {"recruiter": "David Chen"},
        "opened_at": "2026-04-28",
    },
    {
        "id": 3002,
        "name": "Java Backend Engineer",
        "offices": [{"name": "Remote"}],
        "location": {"name": "Remote"},
        "status": "open",
        "custom_fields": {"pay_range": "$120,000 - $150,000", "openings": 2},
        "hiring_team": {"recruiter": "Priya Shah"},
        "opened_at": "2026-05-05",
    },
]

DEMO_APPLICATIONS = [
    {"id": 9001, "candidate": {"id": 5001, "first_name": "Michael", "last_name": "Torres", "email_addresses": [{"value": "michael.torres@email.com"}], "phone_numbers": [{"value": "408-555-0301"}]}, "job": {"id": 3001}, "current_stage": {"name": "Phone Screen"}, "applied_at": "2026-05-10", "last_activity_at": "2026-05-18", "recruiter": {"name": "David Chen"}},
    {"id": 9002, "candidate": {"id": 5002, "first_name": "Rachel", "last_name": "Nguyen", "email_addresses": [{"value": "r.nguyen@email.com"}], "phone_numbers": [{"value": "408-555-0302"}]}, "job": {"id": 3001}, "current_stage": {"name": "Hiring Manager Review"}, "applied_at": "2026-05-12", "last_activity_at": "2026-05-20", "recruiter": {"name": "David Chen"}},
    {"id": 9003, "candidate": {"id": 5003, "first_name": "Kevin", "last_name": "Patel", "email_addresses": [{"value": "k.patel@email.com"}], "phone_numbers": [{"value": "415-555-0303"}]}, "job": {"id": 3001}, "current_stage": {"name": "Offer"}, "applied_at": "2026-05-08", "last_activity_at": "2026-05-21", "recruiter": {"name": "David Chen"}, "offer": {"amount": None}},
    {"id": 9004, "candidate": {"id": 5004, "first_name": "Sophia", "last_name": "Lee", "email_addresses": [{"value": "sophia.lee@email.com"}], "phone_numbers": [{"value": "650-555-0401"}]}, "job": {"id": 3002}, "current_stage": {"name": "Technical Screen"}, "applied_at": "2026-05-15", "last_activity_at": "2026-05-22", "recruiter": {"name": "Priya Shah"}},
    {"id": 9005, "candidate": {"id": 5005, "first_name": "Daniel", "last_name": "Wu", "email_addresses": [{"value": "d.wu@email.com"}], "phone_numbers": [{"value": "650-555-0402"}]}, "job": {"id": 3002}, "current_stage": {"name": "Hired"}, "applied_at": "2026-05-01", "last_activity_at": "2026-05-24", "recruiter": {"name": "Priya Shah"}, "offer": {"amount": None}},
]


class DemoGreenhouseConnector(BaseConnector):
    source_type = "greenhouse"
    display_name = "Greenhouse (Demo)"
    is_demo = True

    def test_connection(self) -> Dict[str, Any]:
        return {"success": True, "message": "Demo mode — no real credentials required."}

    def fetch_jobs(self) -> List[Dict[str, Any]]:
        return DEMO_JOBS

    def fetch_candidates(self) -> List[Dict[str, Any]]:
        return [app["candidate"] for app in DEMO_APPLICATIONS]

    def fetch_applications(self) -> List[Dict[str, Any]]:
        normalized = []
        for app in DEMO_APPLICATIONS:
            cand = app["candidate"]
            stage = app.get("current_stage", {}).get("name", "")
            offer_data = app.get("offer", {})
            normalized.append({
                "applicationId": str(app["id"]),
                "candidateId": str(cand["id"]),
                "jobId": str(app["job"]["id"]),
                "name": f"{cand['first_name']} {cand['last_name']}",
                "email": cand["email_addresses"][0]["value"] if cand.get("email_addresses") else "",
                "phone": cand["phone_numbers"][0]["value"] if cand.get("phone_numbers") else "",
                "stage": stage,
                "appliedAt": app.get("applied_at"),
                "lastActivityAt": app.get("last_activity_at"),
                "recruiter": app.get("recruiter", {}).get("name"),
                "offerAmount": offer_data.get("amount") if offer_data else None,
            })
        return normalized
