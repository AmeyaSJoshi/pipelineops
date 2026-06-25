"""
Encrypt/decrypt connector credentials stored in SourceAccount.credentials_encrypted.
Uses Fernet (AES-128-CBC + HMAC) from the cryptography package.
ENCRYPTION_KEY must be set in production. Dev falls back to a stable derived key.
"""
import base64
import hashlib
import json

from cryptography.fernet import Fernet, InvalidToken

from app.config import get_settings


def _fernet() -> Fernet:
    settings = get_settings()
    key = (settings.ENCRYPTION_KEY or "").strip()
    if key:
        # Accept either a raw 32-byte base64url Fernet key, or any string we derive from
        try:
            return Fernet(key.encode())
        except Exception:
            pass
        # Derive a valid 32-byte Fernet key from whatever string was provided
        derived = base64.urlsafe_b64encode(hashlib.sha256(key.encode()).digest())
        return Fernet(derived)
    # Dev-only stable fallback (NOT secure — warn loudly)
    import warnings
    warnings.warn("ENCRYPTION_KEY not set — using insecure dev key. Set ENCRYPTION_KEY in production.")
    dev_key = base64.urlsafe_b64encode(hashlib.sha256(b"dev-pipelineops-insecure").digest())
    return Fernet(dev_key)


def encrypt(data: dict) -> str:
    return _fernet().encrypt(json.dumps(data).encode()).decode()


def decrypt(encrypted: str) -> dict:
    try:
        return json.loads(_fernet().decrypt(encrypted.encode()))
    except (InvalidToken, Exception) as e:
        raise ValueError(f"Failed to decrypt credentials: {e}")


# ── Field definitions per connector type ──────────────────────────────────────

CONNECTOR_FIELDS = {
    "greenhouse": [
        {
            "key": "api_key",
            "label": "Harvest API Key",
            "type": "password",
            "placeholder": "Your Greenhouse Harvest API key",
            "help": "Greenhouse → Settings → Dev Center → API Credential Management → Create New Credential (Harvest API key)",
            "docs_url": "https://developers.greenhouse.io/harvest",
        },
    ],
    "lever": [
        {
            "key": "api_key",
            "label": "API Key",
            "type": "password",
            "placeholder": "Your Lever API key",
            "help": "Lever → Settings → Integrations & API → API Credentials → Generate New Key",
            "docs_url": "https://hire.lever.co/developer/documentation",
        },
    ],
    "bullhorn": [
        {
            "key": "client_id",
            "label": "Client ID",
            "type": "text",
            "placeholder": "bullhorn_client_id",
            "help": "Provided by Bullhorn during API onboarding. Contact support@bullhorn.com.",
        },
        {
            "key": "client_secret",
            "label": "Client Secret",
            "type": "password",
            "placeholder": "bullhorn_client_secret",
        },
        {
            "key": "username",
            "label": "Username",
            "type": "text",
            "placeholder": "your@bullhorn.com",
        },
        {
            "key": "password",
            "label": "Password",
            "type": "password",
            "placeholder": "Bullhorn account password",
            "help": "Password is used once for OAuth and immediately cleared. It is never stored.",
        },
    ],
    "google_sheets": [
        {
            "key": "oauth_client_id",
            "label": "OAuth Client ID",
            "type": "text",
            "placeholder": "123456789-abc.apps.googleusercontent.com",
            "help": "Google Cloud Console → APIs & Services → Credentials → Create OAuth 2.0 Client ID (Web application). Add http://localhost:8080/connectors/google_sheets/oauth/callback as an authorized redirect URI.",
            "docs_url": "https://console.cloud.google.com/apis/credentials",
        },
        {
            "key": "oauth_client_secret",
            "label": "OAuth Client Secret",
            "type": "password",
            "placeholder": "GOCSPX-…",
            "help": "Shown on the same credentials page as the Client ID.",
        },
        {
            "key": "spreadsheet_id",
            "label": "Spreadsheet ID",
            "type": "text",
            "placeholder": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms",
            "help": "The ID from your Google Sheets URL: docs.google.com/spreadsheets/d/[THIS_PART]/edit",
        },
    ],
}


def required_keys(source_type: str) -> list[str]:
    return [f["key"] for f in CONNECTOR_FIELDS.get(source_type, [])]
