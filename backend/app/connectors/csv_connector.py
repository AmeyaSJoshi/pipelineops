import csv
import io
from typing import Any, Dict, List, Optional
from app.connectors.base import BaseConnector
from app.services.normalization import normalize_job, normalize_candidate, normalize_application
from app.services.llm import map_csv_headers


class CSVConnector(BaseConnector):
    source_type = "csv"
    display_name = "CSV Upload"
    is_demo = False

    def __init__(self, csv_content: str, filename: str = "upload.csv", credentials: Dict = None):
        super().__init__(credentials)
        self.csv_content = csv_content
        self.filename = filename
        self._rows: Optional[List[Dict]] = None
        self._headers: Optional[List[str]] = None
        self._header_map: Optional[Dict[str, str]] = None

    def _parse(self):
        if self._rows is not None:
            return
        reader = csv.DictReader(io.StringIO(self.csv_content))
        self._headers = reader.fieldnames or []
        self._rows = list(reader)
        self._header_map = map_csv_headers(self._headers, self._rows[:3])

    def _mapped(self, row: Dict, canonical: str) -> Any:
        for header, mapped in (self._header_map or {}).items():
            if mapped == canonical and header in row:
                return row[header]
        return row.get(canonical)

    def test_connection(self) -> Dict[str, Any]:
        try:
            self._parse()
            return {"success": True, "message": f"CSV parsed successfully. {len(self._rows)} rows, {len(self._headers)} columns."}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def fetch_jobs(self) -> List[Dict[str, Any]]:
        self._parse()
        jobs = []
        for i, row in enumerate(self._rows):
            title = self._mapped(row, "job_title") or self._mapped(row, "title")
            if not title:
                continue
            jobs.append({
                "id": f"csv_{i}",
                "title": title,
                "company": self._mapped(row, "company") or "",
                "location": self._mapped(row, "location") or "",
                "salary": self._mapped(row, "pay_rate") or "",
                "status": self._mapped(row, "status") or "open",
                "recruiter": self._mapped(row, "recruiter"),
                "openings": self._mapped(row, "openings") or 1,
            })
        return jobs

    def fetch_candidates(self) -> List[Dict[str, Any]]:
        self._parse()
        candidates = []
        seen_emails = set()
        for i, row in enumerate(self._rows):
            name = self._mapped(row, "applicant_name") or self._mapped(row, "name")
            if not name:
                continue
            email = self._mapped(row, "email") or ""
            if email and email in seen_emails:
                continue
            if email:
                seen_emails.add(email)
            candidates.append({
                "id": f"csv_cand_{i}",
                "full_name": name,
                "email": email,
                "phone": self._mapped(row, "phone") or "",
                "location": self._mapped(row, "location") or "",
                "current_title": self._mapped(row, "current_title") or "",
            })
        return candidates

    def fetch_applications(self) -> List[Dict[str, Any]]:
        self._parse()
        apps = []
        for i, row in enumerate(self._rows):
            name = self._mapped(row, "applicant_name") or self._mapped(row, "name")
            if not name:
                continue
            apps.append({
                "applicationId": f"csv_app_{i}",
                "candidateId": f"csv_cand_{i}",
                "jobId": f"csv_{i}",
                "name": name,
                "email": self._mapped(row, "email") or "",
                "phone": self._mapped(row, "phone") or "",
                "stage": self._mapped(row, "stage") or self._mapped(row, "status") or "",
                "appliedAt": self._mapped(row, "applied_date"),
                "recruiter": self._mapped(row, "recruiter"),
                "notes": self._mapped(row, "notes"),
            })
        return apps
