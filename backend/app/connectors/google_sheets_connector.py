"""
Google Sheets connector.
Supports two auth modes (checked in order):
  1. OAuth tokens stored in SourceAccount.credentials_encrypted (via "Sign in with Google")
  2. Service account JSON from GOOGLE_SHEETS_CREDENTIALS_JSON env var (legacy)
"""
import time
from typing import Any, Dict, List, Optional

from app.connectors.base import BaseConnector
from app.config import get_settings

settings = get_settings()


def _load_db_creds() -> Optional[dict]:
    """Load decrypted Google credentials from the SourceAccount table."""
    try:
        from app.db import SessionLocal
        from app.models import SourceAccount
        from app.services.credentials import decrypt
        db = SessionLocal()
        try:
            src = db.query(SourceAccount).filter(
                SourceAccount.source_type == "google_sheets"
            ).first()
            if src and src.credentials_encrypted:
                return decrypt(src.credentials_encrypted)
        finally:
            db.close()
    except Exception:
        pass
    return None


class GoogleSheetsConnector(BaseConnector):
    source_type = "google_sheets"
    display_name = "Google Sheets"
    is_demo = False

    def _get_service(self):
        from googleapiclient.discovery import build

        creds = self._get_credentials()
        return build("sheets", "v4", credentials=creds)

    def _get_credentials(self):
        """Return google.oauth2 Credentials — OAuth first, service account fallback."""
        db_creds = _load_db_creds()

        # ── OAuth path ────────────────────────────────────────────────────────
        if db_creds and db_creds.get("access_token"):
            import httpx
            from google.oauth2.credentials import Credentials
            from google.auth.transport.requests import Request as GoogleRequest

            client_id = db_creds.get("oauth_client_id", "")
            client_secret = db_creds.get("oauth_client_secret", "")
            access_token = db_creds["access_token"]
            refresh_token = db_creds.get("refresh_token", "")
            expiry_ts = db_creds.get("token_expiry", 0)

            import datetime
            expiry = datetime.datetime.utcfromtimestamp(expiry_ts) if expiry_ts else None

            gc = Credentials(
                token=access_token,
                refresh_token=refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=client_id,
                client_secret=client_secret,
                scopes=["https://www.googleapis.com/auth/spreadsheets"],
                expiry=expiry,
            )

            # Refresh if expired
            if gc.expired and gc.refresh_token:
                try:
                    import google.auth.transport.requests
                    gc.refresh(google.auth.transport.requests.Request())
                    # Persist refreshed token
                    self._persist_refreshed_token(db_creds, gc)
                except Exception:
                    pass

            return gc

        # ── Service account fallback ──────────────────────────────────────────
        if settings.GOOGLE_SHEETS_CREDENTIALS_JSON:
            import json
            from google.oauth2.service_account import Credentials
            return Credentials.from_service_account_info(
                json.loads(settings.GOOGLE_SHEETS_CREDENTIALS_JSON),
                scopes=["https://www.googleapis.com/auth/spreadsheets"],
            )

        raise ValueError(
            "Google Sheets not configured. Connect via 'Sign in with Google' on the Sources page."
        )

    def _persist_refreshed_token(self, stored: dict, gc) -> None:
        """Write refreshed access token back to the DB."""
        try:
            from app.db import SessionLocal
            from app.models import SourceAccount
            from app.services.credentials import encrypt, decrypt
            db = SessionLocal()
            try:
                src = db.query(SourceAccount).filter(
                    SourceAccount.source_type == "google_sheets"
                ).first()
                if src and src.credentials_encrypted:
                    data = decrypt(src.credentials_encrypted)
                    data["access_token"] = gc.token
                    if gc.expiry:
                        data["token_expiry"] = gc.expiry.timestamp()
                    src.credentials_encrypted = encrypt(data)
                    db.commit()
            finally:
                db.close()
        except Exception:
            pass

    def _spreadsheet_id(self) -> str:
        db_creds = _load_db_creds()
        if db_creds:
            sid = db_creds.get("spreadsheet_id", "")
            if sid:
                return sid
        return settings.GOOGLE_SHEETS_SPREADSHEET_ID or ""

    def test_connection(self) -> Dict[str, Any]:
        try:
            service = self._get_service()
            sid = self._spreadsheet_id()
            if not sid:
                return {"success": False, "message": "Spreadsheet ID not set."}
            result = service.spreadsheets().get(spreadsheetId=sid).execute()
            title = result.get("properties", {}).get("title", "Unknown")
            return {"success": True, "message": f"Connected to: {title}"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def _read_sheet(self, range_name: str = "Sheet1!A:Z") -> List[List[str]]:
        service = self._get_service()
        sid = self._spreadsheet_id()
        result = service.spreadsheets().values().get(
            spreadsheetId=sid, range=range_name
        ).execute()
        return result.get("values", [])

    def fetch_jobs(self) -> List[Dict[str, Any]]:
        try:
            rows = self._read_sheet()
        except Exception:
            return []
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
