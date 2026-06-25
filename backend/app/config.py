import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./pipelineops.db"
    ALLOW_WRITES: bool = False

    GMI_MAAS_BASE_URL: str = ""
    GMI_MAAS_API_KEY: str = ""
    GMI_MODELS: str = ""
    GMI_SELECTED_MODEL: str = ""
    GMI_AGENTBOX_DEPLOYMENT_MODE: str = ""
    GMI_AGENTBOX_MARKETPLACE_CATEGORY: str = "Data & Analytics"
    GMI_AGENTBOX_LISTING_STATUS: str = "Draft"

    LOCAL_LLM_BASE_URL: str = ""
    LOCAL_LLM_API_KEY: str = ""
    LOCAL_LLM_MODEL: str = ""

    GOOGLE_SHEETS_CREDENTIALS_JSON: str = ""
    GOOGLE_SHEETS_SPREADSHEET_ID: str = ""

    FRONTEND_API_BASE_URL: str = "http://localhost:8080"

    VERSION: str = "0.1.0"
    SERVICE_NAME: str = "PipelineOps Agent"

    class Config:
        env_file = ".env"
        extra = "ignore"

    def gmi_configured(self) -> bool:
        return bool(self.GMI_MAAS_BASE_URL and self.GMI_MAAS_API_KEY)

    def local_llm_configured(self) -> bool:
        return bool(self.LOCAL_LLM_BASE_URL and self.LOCAL_LLM_MODEL)

    def llm_available(self) -> bool:
        return self.gmi_configured() or self.local_llm_configured()

    def get_llm_base_url(self) -> str:
        if self.gmi_configured():
            url = self.GMI_MAAS_BASE_URL.rstrip("/")
            if url.endswith("/v1"):
                return url
            return url + "/v1"
        if self.local_llm_configured():
            url = self.LOCAL_LLM_BASE_URL.rstrip("/")
            if url.endswith("/v1"):
                return url
            return url + "/v1"
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


@lru_cache()
def get_settings() -> Settings:
    return Settings()
