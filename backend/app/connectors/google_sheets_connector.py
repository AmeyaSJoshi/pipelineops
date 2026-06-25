"""Google Sheets connector — requires GOOGLE_SHEETS_CREDENTIALS_JSON and GOOGLE_SHEETS_SPREADSHEET_ID.
Falls back to demo mode if credentials are not configured.
"""
from typing import Any, Dict, List
from app.connectors.base import BaseConnector
from app.config import get_settings

settings = get_settings()


class GoogleSheetsConnector(BaseConnector):
    source_type = "google_sheets"
    display_name = "Google Sheets"
    is_demo = False

    def test_connection(self) -> Dict[str, Any]:
        if not settings.google_sheets_configured():
            return {"success": False, "message": "Google Sheets not configured. Add GOOGLE_SHEETS_CREDENTIALS_JSON and GOOGLE_SHEETS_SPREADSHEET_ID to your .env file."}
        try:
            service = self._get_service()
            result = service.spreadsheets().get(spreadsheetId=settings.GOOGLE_SHEETS_SPREADSHEET_ID).execute()
            return {"success": True, "message": f"Connected to sheet: {result.get('properties', {}).get('title', 'Unknown')}"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def _get_service(self):
        import json
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build
        creds = Credentials.from_service_account_info(
            json.loads(settings.GOOGLE_SHEETS_CREDENTIALS_JSON),
            scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
        )
        return build("sheets", "v4", credentials=creds)

    def _read_sheet(self, range_name: str = "Sheet1!A:Z") -> List[List[str]]:
        service = self._get_service()
        result = service.spreadsheets().values().get(
            spreadsheetId=settings.GOOGLE_SHEETS_SPREADSHEET_ID,
            range=range_name
        ).execute()
        return result.get("values", [])

    def fetch_jobs(self) -> List[Dict[str, Any]]:
        if not settings.google_sheets_configured():
            return []
        rows = self._read_sheet()
        if not rows:
            return []
        headers = [h.lower().strip() for h in rows[0]]
        jobs = []
        for i, row in enumerate(rows[1:], 1):
            record = dict(zip(headers, row))
            title = record.get("title") or record.get("job title") or record.get("position")
            if title:
                jobs.append({
                    "id": f"sheets_{i}",
                    "title": title,
                    "company": record.get("company") or record.get("client"),
                    "location": record.get("location"),
                    "salary": record.get("pay") or record.get("salary") or record.get("pay rate"),
                    "status": record.get("status") or "open",
                    "recruiter": record.get("recruiter"),
                    "openings": record.get("openings") or 1,
                })
        return jobs

    def fetch_candidates(self) -> List[Dict[str, Any]]:
        return []

    def fetch_applications(self) -> List[Dict[str, Any]]:
        return []
