"""Demo connector simulating Indeed-style job board data format.
NOTE: This is synthetic demo data only. Not a real Indeed API integration.
"""
from typing import Any, Dict, List
from app.connectors.base import BaseConnector


DEMO_JOBS = [
    {
        "jobPostingId": "indeed_job_001",
        "jobTitle": "Warehouse Associate",
        "jobLocation": "Dallas, TX",
        "salary": "$18 - $22 an hour",
        "employmentType": "Full-time",
        "status": "open",
        "postedDate": "2026-05-20",
        "recruiter": "Sarah Mitchell",
    },
    {
        "jobPostingId": "indeed_job_002",
        "jobTitle": "Retail Shift Lead",
        "jobLocation": "Denver, CO",
        "salary": "$20 - $24 an hour",
        "employmentType": "Full-time",
        "status": "open",
        "postedDate": "2026-05-25",
        "recruiter": "Marcus Webb",
    },
]

DEMO_CANDIDATES = [
    {"candidateId": "indeed_cand_001", "name": "James Rivera", "email": "james.rivera@email.com", "phone": "214-555-0101", "location": "Dallas, TX", "currentTitle": "Warehouse Worker", "appliedJobId": "indeed_job_001"},
    {"candidateId": "indeed_cand_002", "name": "Linda Park", "email": "linda.park@email.com", "phone": "214-555-0102", "location": "Dallas, TX", "currentTitle": "Logistics Associate", "appliedJobId": "indeed_job_001"},
    {"candidateId": "indeed_cand_003", "name": "Carlos Mendez", "email": "c.mendez@email.com", "phone": "214-555-0103", "location": "Fort Worth, TX", "currentTitle": "Warehouse Team Lead", "appliedJobId": "indeed_job_001"},
    {"candidateId": "indeed_cand_004", "name": "Tyrone Jackson", "email": "tyronej@email.com", "phone": "303-555-0201", "location": "Denver, CO", "currentTitle": "Shift Supervisor", "appliedJobId": "indeed_job_002"},
    {"candidateId": "indeed_cand_005", "name": "Ashley Kim", "email": "ashley.kim@email.com", "phone": "303-555-0202", "location": "Denver, CO", "currentTitle": "Retail Associate", "appliedJobId": "indeed_job_002"},
    # Duplicate — same person as indeed_cand_001 with different capitalization (intentional demo anomaly)
    {"candidateId": "indeed_cand_006", "name": "james rivera", "email": "James.Rivera@Email.com", "phone": "214-555-0101", "location": "Dallas, TX", "currentTitle": "Warehouse Worker", "appliedJobId": "indeed_job_001"},
]

DEMO_APPLICATIONS = [
    {"applicationId": "indeed_app_001", "candidateId": "indeed_cand_001", "jobPostingId": "indeed_job_001", "status": "phone screen", "appliedDate": "2026-05-21"},
    {"applicationId": "indeed_app_002", "candidateId": "indeed_cand_002", "jobPostingId": "indeed_job_001", "status": "applied", "appliedDate": "2026-05-22"},
    {"applicationId": "indeed_app_003", "candidateId": "indeed_cand_003", "jobPostingId": "indeed_job_001", "status": "sent to client", "appliedDate": "2026-05-23"},
    {"applicationId": "indeed_app_004", "candidateId": "indeed_cand_004", "jobPostingId": "indeed_job_002", "status": "interview", "appliedDate": "2026-05-26"},
    {"applicationId": "indeed_app_005", "candidateId": "indeed_cand_005", "jobPostingId": "indeed_job_002", "status": "applied", "appliedDate": "2026-05-28"},
    {"applicationId": "indeed_app_006", "candidateId": "indeed_cand_006", "jobPostingId": "indeed_job_001", "status": "applied", "appliedDate": "2026-05-29"},
]


class DemoIndeedConnector(BaseConnector):
    source_type = "indeed"
    display_name = "Indeed (Demo)"
    is_demo = True

    def test_connection(self) -> Dict[str, Any]:
        return {"success": True, "message": "Demo mode — no real credentials required."}

    def fetch_jobs(self) -> List[Dict[str, Any]]:
        return DEMO_JOBS

    def fetch_candidates(self) -> List[Dict[str, Any]]:
        return DEMO_CANDIDATES

    def fetch_applications(self) -> List[Dict[str, Any]]:
        return DEMO_APPLICATIONS
