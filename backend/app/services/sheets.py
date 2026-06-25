"""
Google Sheets export service.
Auth: Service Account JSON (server-to-server, no user interaction required).

Setup:
  1. Create a service account in Google Cloud Console.
  2. Enable the Google Sheets API for the project.
  3. Download the JSON key file.
  4. Share the target spreadsheet with the service account email (Editor permission).
  5. Set GOOGLE_SHEETS_CREDENTIALS_JSON (single-line JSON contents) and GOOGLE_SHEETS_SPREADSHEET_ID in .env.

Rate limits: 300 read / 60 write requests per minute per project.
"""
from __future__ import annotations

import csv
import io
import json
import logging
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.config import get_settings
from app.services.exports import generate_csv_export, generate_sheet_preview

logger = logging.getLogger(__name__)
settings = get_settings()

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def _get_sheets_service():
    """Build authenticated Google Sheets service from service account JSON."""
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build

    info = json.loads(settings.GOOGLE_SHEETS_CREDENTIALS_JSON)
    creds = Credentials.from_service_account_info(info, scopes=SCOPES)
    return build("sheets", "v4", credentials=creds)


def _csv_to_rows(csv_text: str) -> List[List[str]]:
    reader = csv.reader(io.StringIO(csv_text))
    return list(reader)


def _ensure_sheet_tab(service, spreadsheet_id: str, title: str) -> int:
    """Add a new sheet tab if it doesn't exist. Returns the sheetId."""
    meta = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    existing = {s["properties"]["title"]: s["properties"]["sheetId"] for s in meta.get("sheets", [])}
    if title in existing:
        return existing[title]
    body = {"requests": [{"addSheet": {"properties": {"title": title}}}]}
    resp = service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()
    return resp["replies"][0]["addSheet"]["properties"]["sheetId"]


def _write_tab(service, spreadsheet_id: str, tab_title: str, rows: List[List[str]]):
    """Write rows to a named tab, clearing it first."""
    _ensure_sheet_tab(service, spreadsheet_id, tab_title)
    range_name = f"'{tab_title}'!A1"
    # Clear existing content
    service.spreadsheets().values().clear(
        spreadsheetId=spreadsheet_id, range=range_name
    ).execute()
    # Write new data
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=range_name,
        valueInputOption="RAW",
        body={"values": rows},
    ).execute()


TAB_LABELS = {
    "pipeline_summary": "Pipeline Summary",
    "role_detail": "Role Detail",
    "candidate_stage_detail": "Candidate Stage Detail",
    "anomalies": "Anomalies",
}


def export_to_google_sheets(db: Session) -> Dict[str, Any]:
    """Export pipeline data to Google Sheets if credentials are configured."""
    if not settings.google_sheets_configured():
        preview = generate_sheet_preview(db)
        return {
            "success": False,
            "status": "needs_credentials",
            "message": (
                "Google Sheets not configured. "
                "Set GOOGLE_SHEETS_CREDENTIALS_JSON and GOOGLE_SHEETS_SPREADSHEET_ID in .env. "
                "See CONNECTOR_AUDIT.md for setup instructions."
            ),
            "preview": preview,
            "download_url": "/exports/download",
        }

    try:
        return _real_sheets_export(db)
    except ImportError:
        return {
            "success": False,
            "status": "missing_dependency",
            "message": "google-api-python-client not installed. Run: pip install google-api-python-client google-auth",
        }
    except Exception as e:
        logger.error("Google Sheets export failed: %s", e)
        return {
            "success": False,
            "status": "error",
            "message": f"Google Sheets export failed: {e}",
            "preview": generate_sheet_preview(db),
        }


def _real_sheets_export(db: Session) -> Dict[str, Any]:
    service = _get_sheets_service()
    spreadsheet_id = settings.GOOGLE_SHEETS_SPREADSHEET_ID
    sheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"

    csv_data = generate_csv_export(db)
    tabs_written: List[str] = []

    for key, csv_text in csv_data.items():
        tab_title = TAB_LABELS.get(key, key.replace("_", " ").title())
        rows = _csv_to_rows(csv_text)
        if rows:
            _write_tab(service, spreadsheet_id, tab_title, rows)
            tabs_written.append(tab_title)

    logger.info("Google Sheets export complete: %s tabs → %s", len(tabs_written), sheet_url)
    return {
        "success": True,
        "status": "exported",
        "format": "google_sheets",
        "message": f"Exported {len(tabs_written)} tab(s) to Google Sheets.",
        "sheet_url": sheet_url,
        "tabs_written": tabs_written,
    }


def read_from_google_sheets(spreadsheet_id: str, range_name: str = "Sheet1!A:Z") -> List[Dict[str, Any]]:
    """
    Read rows from a Google Sheet and return as list-of-dicts.
    First row is treated as headers.
    """
    if not settings.google_sheets_configured():
        return []
    try:
        service = _get_sheets_service()
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id, range=range_name
        ).execute()
        values = result.get("values", [])
        if not values:
            return []
        headers = values[0]
        rows: List[Dict] = []
        for row in values[1:]:
            padded = row + [""] * (len(headers) - len(row))
            rows.append({headers[i]: padded[i] for i in range(len(headers))})
        return rows
    except Exception as e:
        logger.error("Google Sheets read failed: %s", e)
        return []
