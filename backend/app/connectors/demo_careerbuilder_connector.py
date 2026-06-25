"""Demo connector simulating CareerBuilder-style job board data.
NOTE: Synthetic demo data only. Not a real CareerBuilder API integration.
"""
from typing import Any, Dict, List
from app.connectors.base import BaseConnector


DEMO_JOBS = [
    {"JobDID": "cb_job_001", "JobTitle": "Warehouse Associate", "Location": "Dallas, TX", "PayInfoMin": 18, "PayInfoMax": 22, "PayInfoType": "Hourly", "JobStatus": "Active", "PostedDate": "2026-05-18", "ContactName": "Sarah Mitchell"},
    {"JobDID": "cb_job_002", "JobTitle": "Retail Shift Lead", "Location": "Denver, CO", "PayInfoMin": 20, "PayInfoMax": 24, "PayInfoType": "Hourly", "JobStatus": "Active", "PostedDate": "2026-05-22", "ContactName": "Marcus Webb"},
]

DEMO_APPLICATIONS = [
    {"ApplicationID": "cb_app_001", "JobDID": "cb_job_001", "CandidateName": "Steven Garcia", "Email": "s.garcia@email.com", "Phone": "214-555-0701", "Location": "Dallas, TX", "Status": "Application Received", "ApplyDate": "2026-05-23"},
    {"ApplicationID": "cb_app_002", "JobDID": "cb_job_001", "CandidateName": "Maria Gonzalez", "Email": "maria.g@email.com", "Phone": "214-555-0702", "Location": "Dallas, TX", "Status": "Screened", "ApplyDate": "2026-05-24"},
    {"ApplicationID": "cb_app_003", "JobDID": "cb_job_002", "CandidateName": "Robert Kim", "Email": "r.kim@email.com", "Phone": "303-555-0301", "Location": "Denver, CO", "Status": "Sent to Client", "ApplyDate": "2026-05-26"},
    {"ApplicationID": "cb_app_004", "JobDID": "cb_job_002", "CandidateName": "Jennifer Walsh", "Email": "j.walsh@email.com", "Phone": "303-555-0302", "Location": "Littleton, CO", "Status": "Not Selected", "ApplyDate": "2026-05-27"},
]


class DemoCareerBuilderConnector(BaseConnector):
    source_type = "careerbuilder"
    display_name = "CareerBuilder (Demo)"
    is_demo = True

    def test_connection(self) -> Dict[str, Any]:
        return {"success": True, "message": "Demo mode — no real credentials required."}

    def fetch_jobs(self) -> List[Dict[str, Any]]:
        return [{
            "id": j["JobDID"],
            "title": j["JobTitle"],
            "location": j["Location"],
            "pay_min": j.get("PayInfoMin"),
            "pay_max": j.get("PayInfoMax"),
            "pay_unit": "hourly" if j.get("PayInfoType") == "Hourly" else "salary",
            "status": "open" if j.get("JobStatus") == "Active" else "closed",
            "recruiter": j.get("ContactName"),
        } for j in DEMO_JOBS]

    def fetch_candidates(self) -> List[Dict[str, Any]]:
        return [{
            "id": a["ApplicationID"],
            "full_name": a["CandidateName"],
            "email": a["Email"],
            "phone": a["Phone"],
            "location": a["Location"],
        } for a in DEMO_APPLICATIONS]

    def fetch_applications(self) -> List[Dict[str, Any]]:
        return [{
            "applicationId": a["ApplicationID"],
            "candidateId": a["ApplicationID"],
            "jobId": a["JobDID"],
            "name": a["CandidateName"],
            "email": a["Email"],
            "phone": a["Phone"],
            "stage": a["Status"],
            "appliedAt": a.get("ApplyDate"),
        } for a in DEMO_APPLICATIONS]
