from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str
    agentbox_ready: bool
    gmi_maas_configured: bool
    message: str
    database: str
    version: str


class JobStartRequest(BaseModel):
    task: str
    params: Optional[Dict[str, Any]] = {}


class JobResponse(BaseModel):
    job_id: str
    status: str
    progress: int = 0
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class SourceAccountOut(BaseModel):
    id: int
    source_type: str
    display_name: str
    status: str
    last_sync_at: Optional[datetime]
    records_total: int
    created_at: datetime

    class Config:
        from_attributes = True


class CompanyOut(BaseModel):
    id: int
    name: str
    normalized_name: str

    class Config:
        from_attributes = True


class JobRoleOut(BaseModel):
    id: int
    title: str
    normalized_title: Optional[str]
    company_id: int
    company_name: Optional[str] = None
    location_city: Optional[str]
    location_state: Optional[str]
    remote_type: str
    pay_min: Optional[float]
    pay_max: Optional[float]
    pay_unit: str
    openings_count: int
    status: str
    recruiter_owner: Optional[str]
    client_stage: Optional[str]
    created_at: datetime
    updated_at: datetime
    applicant_count: Optional[int] = 0
    submitted_count: Optional[int] = 0
    interview_count: Optional[int] = 0
    offer_count: Optional[int] = 0
    placement_count: Optional[int] = 0

    class Config:
        from_attributes = True


class CandidateOut(BaseModel):
    id: int
    full_name: str
    email_display_masked: Optional[str]
    phone_display_masked: Optional[str]
    location: Optional[str]
    current_title: Optional[str]
    current_company: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ApplicationOut(BaseModel):
    id: int
    candidate_id: int
    candidate_name: Optional[str] = None
    job_role_id: Optional[int]
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    source: Optional[str]
    raw_stage: Optional[str]
    canonical_stage: str
    status: str
    applied_at: Optional[datetime]
    last_activity_at: Optional[datetime]
    recruiter_owner: Optional[str]
    offer_amount: Optional[float]

    class Config:
        from_attributes = True


class AnomalyOut(BaseModel):
    id: int
    severity: str
    category: str
    title: str
    explanation: str
    recommended_fix: str
    related_entity_type: Optional[str]
    related_entity_id: Optional[int]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class AnomalyUpdate(BaseModel):
    status: str  # approved|ignored|resolved


class MergeCandidate(BaseModel):
    candidate_a: Dict[str, Any]
    candidate_b: Dict[str, Any]
    confidence: float
    reason: str
    recommended_action: str


class MetricsResponse(BaseModel):
    open_roles: int
    active_candidates: int
    applicants_per_role: float
    submitted_to_client_count: int
    interview_count: int
    offer_count: int
    placement_count: int
    submit_rate: float
    interview_rate: float
    offer_rate: float
    placement_rate: float
    overall_hit_rate: float
    stale_role_count: int
    missing_pay_rate_count: int
    duplicate_candidate_count: int
    roles_by_client: Dict[str, int]
    candidates_by_stage: Dict[str, int]
    average_pay_rate: Optional[float]


class ReportSummaryResponse(BaseModel):
    generated_at: datetime
    metrics: MetricsResponse
    narrative_summary: str
    anomaly_count: int
    top_anomalies: List[AnomalyOut]
    pipeline_data: List[JobRoleOut]
    recommended_actions: List[str]


class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[Dict[str, str]]] = []


class ChatResponse(BaseModel):
    response: str
    sources: List[str] = []
    mode: str = "demo"


class ExportRequest(BaseModel):
    format: str = "csv"  # csv|google_sheets


class ExportResponse(BaseModel):
    success: bool
    format: str
    message: str
    download_url: Optional[str] = None
    sheet_url: Optional[str] = None
    preview: Optional[Dict[str, Any]] = None


class SeedResponse(BaseModel):
    message: str
    sources_created: int
    companies_created: int
    roles_created: int
    candidates_created: int
    applications_created: int


class ResetResponse(BaseModel):
    message: str
    tables_cleared: List[str]


class GMISettingsResponse(BaseModel):
    gmi_maas_configured: bool
    gmi_base_url: Optional[str]
    gmi_model: Optional[str]
    agentbox_ready: bool
    deployment_mode: str
    listing_status: str
    google_sheets_configured: bool
    allow_writes: bool
