import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./pipelineops.db"
    ALLOW_WRITES: bool = False

    # ── Security ──────────────────────────────────────────────────────────────
    # Used to encrypt connector credentials at rest.
    # Generate: python -c "import secrets; print(secrets.token_hex(32))"
    ENCRYPTION_KEY: str = ""
    SECRET_KEY: str = ""        # JWT signing key (if auth is enabled)
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # ── GMI MaaS / AgentBox ───────────────────────────────────────────────────
    GMI_MAAS_BASE_URL: str = ""
    GMI_MAAS_API_KEY: str = ""
    GMI_MODELS: str = ""
    GMI_SELECTED_MODEL: str = ""
    GMI_AGENTBOX_DEPLOYMENT_MODE: str = ""
    GMI_AGENTBOX_MARKETPLACE_CATEGORY: str = "Data & Analytics"
    GMI_AGENTBOX_LISTING_STATUS: str = "Draft"

    # ── Local LLM fallback ────────────────────────────────────────────────────
    LOCAL_LLM_BASE_URL: str = ""
    LOCAL_LLM_API_KEY: str = ""
    LOCAL_LLM_MODEL: str = ""

    # ── Google Sheets ─────────────────────────────────────────────────────────
    # Single-line JSON contents of a service account key file.
    # Share the target spreadsheet with the service account email before use.
    GOOGLE_SHEETS_CREDENTIALS_JSON: str = ""
    GOOGLE_SHEETS_SPREADSHEET_ID: str = ""

    # ── Greenhouse Harvest API ────────────────────────────────────────────────
    # Obtain from: Greenhouse admin > Configure > Dev Center > API Credential Management
    GREENHOUSE_API_KEY: str = ""

    # ── Lever Data API ────────────────────────────────────────────────────────
    # Obtain from: Lever admin > Settings > Integrations & API > API Credentials
    LEVER_API_KEY: str = ""

    # ── Bullhorn REST API ─────────────────────────────────────────────────────
    # Requires a corporate Bullhorn subscription + OAuth app registration.
    # BULLHORN_PASSWORD is used only for initial OAuth token exchange and is never persisted.
    BULLHORN_CLIENT_ID: str = ""
    BULLHORN_CLIENT_SECRET: str = ""
    BULLHORN_USERNAME: str = ""
    BULLHORN_PASSWORD: str = ""   # used once for headless OAuth, not stored

    # ── Frontend ──────────────────────────────────────────────────────────────
    FRONTEND_API_BASE_URL: str = "http://localhost:8080"

    VERSION: str = "0.2.0"
    SERVICE_NAME: str = "PipelineOps Agent"

    class Config:
        env_file = ".env"
        extra = "ignore"

    # ── Derived helpers ───────────────────────────────────────────────────────

    def gmi_configured(self) -> bool:
        return bool(self.GMI_MAAS_BASE_URL and self.GMI_MAAS_API_KEY)

    def local_llm_configured(self) -> bool:
        return bool(self.LOCAL_LLM_BASE_URL and self.LOCAL_LLM_MODEL)

    def llm_available(self) -> bool:
        return self.gmi_configured() or self.local_llm_configured()

    def get_llm_base_url(self) -> str:
        if self.gmi_configured():
            url = self.GMI_MAAS_BASE_URL.rstrip("/")
            return url if url.endswith("/v1") else url + "/v1"
        if self.local_llm_configured():
            url = self.LOCAL_LLM_BASE_URL.rstrip("/")
            return url if url.endswith("/v1") else url + "/v1"
        return ""

    def get_llm_api_key(self) -> str:
        if self.gmi_configured():
            return self.GMI_MAAS_API_KEY
        return self.LOCAL_LLM_API_KEY or "demo"

    def get_llm_model(self) -> str:
        if self.gmi_configured():
            if self.GMI_SELECTED_MODEL:
                return self.GMI_SELECTED_MODEL
            if self.GMI_MODELS:
                return self.GMI_MODELS.split(",")[0].strip()
        if self.local_llm_configured():
            return self.LOCAL_LLM_MODEL
        return "fallback"

    def google_sheets_configured(self) -> bool:
        return bool(self.GOOGLE_SHEETS_CREDENTIALS_JSON and self.GOOGLE_SHEETS_SPREADSHEET_ID)

    def greenhouse_configured(self) -> bool:
        return bool(self.GREENHOUSE_API_KEY)

    def lever_configured(self) -> bool:
        return bool(self.LEVER_API_KEY)

    def bullhorn_configured(self) -> bool:
        return bool(self.BULLHORN_CLIENT_ID and self.BULLHORN_CLIENT_SECRET and self.BULLHORN_USERNAME)


@lru_cache()
def get_settings() -> Settings:
    return Settings()
