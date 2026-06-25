"""Demo connector simulating Lever ATS data format.
NOTE: This is synthetic demo data only. Not a real Lever API integration.
"""
from typing import Any, Dict, List
from app.connectors.base import BaseConnector


DEMO_POSTINGS = [
    {
        "id": "lever_post_001",
        "text": "Staff Accountant",
        "categories": {"location": "Chicago, IL", "team": "Finance"},
        "salaryRange": {"min": 70000, "max": 85000, "currency": "USD"},
        "state": "published",
        "createdAt": 1716000000000,
        "owner": {"name": "Jordan Blake"},
    },
]

DEMO_OPPORTUNITIES = [
    {"id": "lever_opp_001", "posting": "lever_post_001", "name": "Patricia Flores", "emails": ["p.flores@email.com"], "phones": [{"value": "312-555-0501"}], "location": "Chicago, IL", "headline": "Senior Accountant", "stage": {"text": "Hiring Manager Screen"}, "createdAt": 1716120000000, "lastInteractionAt": 1717500000000, "owner": {"name": "Jordan Blake"}},
    {"id": "lever_opp_002", "posting": "lever_post_001", "name": "Brian Scott", "emails": ["brian.scott@email.com"], "phones": [{"value": "312-555-0502"}], "location": "Chicago, IL", "headline": "Accountant II", "stage": {"text": "Offer Extended"}, "createdAt": 1716200000000, "lastInteractionAt": 1717600000000, "owner": {"name": "Jordan Blake"}, "offer": {"salary": None}},
    {"id": "lever_opp_003", "posting": "lever_post_001", "name": "Megan Turner", "emails": ["m.turner@email.com"], "phones": [{"value": "312-555-0503"}], "location": "Evanston, IL", "headline": "Staff Accountant", "stage": {"text": "Applied"}, "createdAt": 1717000000000, "lastInteractionAt": None, "owner": {"name": "Jordan Blake"}},
    {"id": "lever_opp_004", "posting": "lever_post_001", "name": "Alex Thompson", "emails": ["alex.t@email.com"], "phones": [{"value": "312-555-0504"}], "location": "Chicago, IL", "headline": "Financial Analyst", "stage": {"text": "New Applicant"}, "createdAt": 1717200000000, "lastInteractionAt": None, "owner": {"name": "Jordan Blake"}},
]


class DemoLeverConnector(BaseConnector):
    source_type = "lever"
    display_name = "Lever (Demo)"
    is_demo = True

    def test_connection(self) -> Dict[str, Any]:
        return {"success": True, "message": "Demo mode — no real credentials required."}

    def fetch_jobs(self) -> List[Dict[str, Any]]:
        return [{
            "id": p["id"],
            "title": p["text"],
            "location": p["categories"].get("location", ""),
            "pay_min": p.get("salaryRange", {}).get("min"),
            "pay_max": p.get("salaryRange", {}).get("max"),
            "pay_unit": "salary",
            "status": "open" if p.get("state") == "published" else "closed",
            "recruiter": p.get("owner", {}).get("name"),
        } for p in DEMO_POSTINGS]

    def fetch_candidates(self) -> List[Dict[str, Any]]:
        return [{
            "id": o["id"],
            "full_name": o["name"],
            "email": o["emails"][0] if o.get("emails") else "",
            "phone": o["phones"][0]["value"] if o.get("phones") else "",
            "location": o.get("location", ""),
            "current_title": o.get("headline", ""),
        } for o in DEMO_OPPORTUNITIES]

    def fetch_applications(self) -> List[Dict[str, Any]]:
        from datetime import datetime
        normalized = []
        for o in DEMO_OPPORTUNITIES:
            stage = o.get("stage", {}).get("text", "")
            last_ts = o.get("lastInteractionAt")
            last_dt = datetime.utcfromtimestamp(last_ts / 1000).isoformat() if last_ts else None
            offer = o.get("offer", {})
            normalized.append({
                "applicationId": o["id"],
                "candidateId": o["id"],
                "jobId": o.get("posting"),
                "name": o["name"],
                "email": o["emails"][0] if o.get("emails") else "",
                "phone": o["phones"][0]["value"] if o.get("phones") else "",
                "stage": stage,
                "lastActivityAt": last_dt,
                "recruiter": o.get("owner", {}).get("name"),
                "offerAmount": offer.get("salary") if offer else None,
            })
        return normalized
