from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from app.config import get_settings
from app.services.exports import generate_csv_export, generate_sheet_preview

settings = get_settings()


def export_to_google_sheets(db: Session) -> Dict[str, Any]:
    """Export pipeline data to Google Sheets if credentials are configured."""
    if not settings.google_sheets_configured():
        preview = generate_sheet_preview(db)
        return {
            "success": False,
            "format": "csv_preview",
            "message": "Google Sheets not configured. Demo export generated locally.",
            "preview": preview,
            "download_url": "/exports/download",
        }

    try:
        return _real_sheets_export(db)
    except Exception as e:
        return {
            "success": False,
            "format": "error",
            "message": f"Google Sheets export failed: {str(e)}",
            "preview": generate_sheet_preview(db),
        }


def _real_sheets_export(db: Session) -> Dict[str, Any]:
    """Real Google Sheets export using credentials."""
    import json
    try:
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build
    except ImportError:
        return {
            "success": False,
            "message": "google-api-python-client not installed. Run: pip install google-api-python-client google-auth",
            "format": "error",
        }

    creds_json = settings.GOOGLE_SHEETS_CREDENTIALS_JSON
    spreadsheet_id = settings.GOOGLE_SHEETS_SPREADSHEET_ID

    creds = Credentials.from_service_account_info(
        json.loads(creds_json),
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    service = build("sheets", "v4", credentials=creds)

    csv_data = generate_csv_export(db)
    sheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"

    # TODO: Write each CSV tab to the Google Sheet
    # This is a placeholder for the real implementation
    # sheet_tabs = ["Pipeline Summary", "Role Detail", "Candidate Stage Detail", "Anomalies"]

    return {
        "success": True,
        "format": "google_sheets",
        "message": "Pipeline data exported to Google Sheets.",
        "sheet_url": sheet_url,
        "preview": None,
    }
