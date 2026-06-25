"""
CSV and Excel (.xlsx) upload connector.
No external API required — parse file contents directly.
Supports auto-detection by filename extension or MIME type.
"""
import csv
import io
from typing import Any, Dict, List, Optional

from app.connectors.base import BaseConnector
from app.services.normalization import normalize_job, normalize_candidate, normalize_application
from app.services.llm import map_csv_headers


def _rows_from_xlsx(content: bytes) -> tuple[List[str], List[Dict]]:
    """Parse Excel .xlsx bytes into (headers, list-of-dicts)."""
    try:
        import openpyxl
    except ImportError as exc:
        raise ImportError("openpyxl is required for Excel support. Run: pip install openpyxl") from exc

    wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return [], []

    headers = [str(h).strip() if h is not None else f"col_{i}" for i, h in enumerate(rows[0])]
    data: List[Dict] = []
    for row in rows[1:]:
        if all(v is None for v in row):
            continue  # skip blank rows (handles merged cells / gaps)
        data.append({headers[i]: (str(v).strip() if v is not None else "") for i, v in enumerate(row)})
    return headers, data


def _rows_from_csv(content: str) -> tuple[List[str], List[Dict]]:
    reader = csv.DictReader(io.StringIO(content))
    headers = list(reader.fieldnames or [])
    rows = [row for row in reader if any(v.strip() for v in row.values())]
    return headers, rows


class CSVConnector(BaseConnector):
    source_type = "csv"
    display_name = "CSV / Excel Upload"
    is_demo = False

    def __init__(
        self,
        content: Any,              # str for CSV, bytes for Excel
        filename: str = "upload.csv",
        credentials: Optional[Dict] = None,
    ):
        super().__init__(credentials)
        self._raw = content
        self.filename = filename
        self._rows: Optional[List[Dict]] = None
        self._headers: Optional[List[str]] = None
        self._header_map: Optional[Dict[str, str]] = None

    def _is_excel(self) -> bool:
        name = (self.filename or "").lower()
        return name.endswith(".xlsx") or name.endswith(".xls")

    def _parse(self):
        if self._rows is not None:
            return
        if self._is_excel():
            raw_bytes = self._raw if isinstance(self._raw, bytes) else self._raw.encode("latin-1")
            self._headers, self._rows = _rows_from_xlsx(raw_bytes)
        else:
            text = self._raw if isinstance(self._raw, str) else self._raw.decode("utf-8-sig")
            self._headers, self._rows = _rows_from_csv(text)
        self._header_map = map_csv_headers(self._headers, self._rows[:3])

    def _mapped(self, row: Dict, canonical: str) -> Any:
        for header, mapped in (self._header_map or {}).items():
            if mapped == canonical and header in row:
                return row[header]
        return row.get(canonical)

    def test_connection(self) -> Dict[str, Any]:
        try:
            self._parse()
            fmt = "Excel" if self._is_excel() else "CSV"
            return {
                "success": True,
                "format": fmt,
                "message": f"{fmt} parsed: {len(self._rows)} data rows, {len(self._headers)} columns.",
                "columns": self._headers,
            }
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
                "salary": self._mapped(row, "pay_rate") or self._mapped(row, "salary") or "",
                "status": self._mapped(row, "status") or "open",
                "recruiter": self._mapped(row, "recruiter"),
                "openings": self._mapped(row, "openings") or 1,
            })
        return jobs

    def fetch_candidates(self) -> List[Dict[str, Any]]:
        self._parse()
        candidates = []
        seen_emails: set = set()
        for i, row in enumerate(self._rows):
            name = self._mapped(row, "applicant_name") or self._mapped(row, "full_name") or self._mapped(row, "name")
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
                "current_title": self._mapped(row, "current_title") or self._mapped(row, "title") or "",
            })
        return candidates

    def fetch_applications(self) -> List[Dict[str, Any]]:
        self._parse()
        apps = []
        for i, row in enumerate(self._rows):
            name = self._mapped(row, "applicant_name") or self._mapped(row, "full_name") or self._mapped(row, "name")
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
                "appliedAt": self._mapped(row, "applied_date") or self._mapped(row, "apply_date"),
                "recruiter": self._mapped(row, "recruiter"),
                "notes": self._mapped(row, "notes"),
            })
        return apps
