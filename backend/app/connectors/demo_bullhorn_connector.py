"""Demo connector simulating Bullhorn ATS data format.
NOTE: This is synthetic demo data only. Not a real Bullhorn API integration.
"""
from typing import Any, Dict, List
from app.connectors.base import BaseConnector


DEMO_JOB_ORDERS = [
    {"entity": "JobOrder", "id": 4001, "title": "Medical Assistant", "clientCorporation": {"id": 201, "name": "Northstar Health"}, "payRate": 25, "salary": None, "numOpenings": 5, "status": "Accepting Candidates", "dateAdded": "2026-04-30", "owner": {"name": "Rachel Moore"}},
    {"entity": "JobOrder", "id": 4002, "title": "Medical Assistant", "clientCorporation": {"id": 201, "name": "Northstar Health"}, "payRate": 28, "salary": None, "numOpenings": 5, "status": "Accepting Candidates", "dateAdded": "2026-05-02", "owner": {"name": "Rachel Moore"}},  # Conflicting pay rate — intentional demo anomaly
]

DEMO_CANDIDATES_BH = [
    {"id": 6001, "firstName": "Natalie", "lastName": "Johnson", "email": "natalie.j@email.com", "mobile": "602-555-0601", "city": "Phoenix", "state": "AZ", "occupation": "Medical Assistant"},
    {"id": 6002, "firstName": "Omar", "lastName": "Hassan", "email": "o.hassan@email.com", "mobile": "602-555-0602", "city": "Phoenix", "state": "AZ", "occupation": "Phlebotomist"},
    {"id": 6003, "firstName": "Crystal", "lastName": "Brooks", "email": "c.brooks@email.com", "mobile": "602-555-0603", "city": "Scottsdale", "state": "AZ", "occupation": "Medical Office Specialist"},
    {"id": 6004, "firstName": "Hector", "lastName": "Ramirez", "email": "h.ramirez@email.com", "mobile": "602-555-0604", "city": "Phoenix", "state": "AZ", "occupation": "Clinical Assistant"},
    {"id": 6005, "firstName": "Tanya", "lastName": "White", "email": "tanya.white@email.com", "mobile": "602-555-0605", "city": "Mesa", "state": "AZ", "occupation": "Medical Assistant"},
]

DEMO_PLACEMENTS_BH = [
    {"id": 7001, "candidate": {"id": 6001}, "jobOrder": {"id": 4001}, "status": "Approved", "dateAdded": "2026-05-19", "payRate": 25, "employmentType": "Contract"},
    {"id": 7002, "candidate": {"id": 6002}, "jobOrder": {"id": 4001}, "status": "Interview", "dateAdded": "2026-05-22", "payRate": None, "employmentType": "Contract"},
    {"id": 7003, "candidate": {"id": 6003}, "jobOrder": {"id": 4001}, "status": "Submitted", "dateAdded": "2026-05-20", "payRate": None},
    {"id": 7004, "candidate": {"id": 6004}, "jobOrder": {"id": 4001}, "status": "New Lead", "dateAdded": "2026-06-01"},
    {"id": 7005, "candidate": {"id": 6005}, "jobOrder": {"id": 4001}, "status": "Offer Extended", "dateAdded": "2026-05-25", "payRate": None},  # Offer without amount — intentional anomaly
]


class DemoBullhornConnector(BaseConnector):
    source_type = "bullhorn"
    display_name = "Bullhorn (Demo)"
    is_demo = True

    def test_connection(self) -> Dict[str, Any]:
        return {"success": True, "message": "Demo mode — no real credentials required."}

    def fetch_jobs(self) -> List[Dict[str, Any]]:
        return [{
            "id": j["id"],
            "title": j["title"],
            "company": j["clientCorporation"]["name"],
            "pay_min": j.get("payRate"),
            "pay_max": j.get("payRate"),
            "pay_unit": "hourly" if j.get("payRate") else "unknown",
            "openings": j.get("numOpenings", 1),
            "status": "open" if j.get("status") == "Accepting Candidates" else "closed",
            "recruiter": j.get("owner", {}).get("name"),
            "source_type": self.source_type,
        } for j in DEMO_JOB_ORDERS]

    def fetch_candidates(self) -> List[Dict[str, Any]]:
        return [{
            "id": c["id"],
            "full_name": f"{c['firstName']} {c['lastName']}",
            "email": c["email"],
            "phone": c.get("mobile", ""),
            "location": f"{c.get('city', '')}, {c.get('state', '')}".strip(", "),
            "current_title": c.get("occupation", ""),
        } for c in DEMO_CANDIDATES_BH]

    def fetch_applications(self) -> List[Dict[str, Any]]:
        return [{
            "applicationId": str(p["id"]),
            "candidateId": str(p["candidate"]["id"]),
            "jobId": str(p["jobOrder"]["id"]),
            "stage": p.get("status", ""),
            "offerAmount": p.get("payRate"),
            "appliedAt": p.get("dateAdded"),
        } for p in DEMO_PLACEMENTS_BH]
