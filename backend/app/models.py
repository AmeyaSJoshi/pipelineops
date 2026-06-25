from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from app.db import Base


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    users = relationship("User", back_populates="org")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, default="")
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    org = relationship("Organization", back_populates="users")


class SourceAccount(Base):
    __tablename__ = "source_accounts"

    id = Column(Integer, primary_key=True, index=True)
    source_type = Column(String, nullable=False)  # csv|google_sheets|greenhouse|lever|bullhorn|indeed|careerbuilder|monster|dice|manual
    display_name = Column(String, nullable=False)
    status = Column(String, default="needs_credentials")  # connected|demo|needs_credentials|error|disabled
    credentials_encrypted = Column(Text, nullable=True)  # placeholder for encrypted creds
    last_sync_at = Column(DateTime, nullable=True)
    records_total = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    sync_runs = relationship("SyncRun", back_populates="source_account")
    external_records = relationship("ExternalRecord", back_populates="source_account")


class SyncRun(Base):
    __tablename__ = "sync_runs"

    id = Column(Integer, primary_key=True, index=True)
    source_account_id = Column(Integer, ForeignKey("source_accounts.id"), nullable=False)
    status = Column(String, default="pending")  # pending|running|completed|failed
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    records_seen = Column(Integer, default=0)
    records_created = Column(Integer, default=0)
    records_updated = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)

    source_account = relationship("SourceAccount", back_populates="sync_runs")


class ExternalRecord(Base):
    __tablename__ = "external_records"

    id = Column(Integer, primary_key=True, index=True)
    source_account_id = Column(Integer, ForeignKey("source_accounts.id"), nullable=False)
    external_id = Column(String, nullable=True)
    external_type = Column(String, nullable=False)  # job|candidate|application|stage_event
    raw_json = Column(JSON, nullable=False)
    content_hash = Column(String, nullable=True)
    first_seen_at = Column(DateTime, default=datetime.utcnow)
    last_seen_at = Column(DateTime, default=datetime.utcnow)

    source_account = relationship("SourceAccount", back_populates="external_records")


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    normalized_name = Column(String, nullable=False)
    source_account_id = Column(Integer, ForeignKey("source_accounts.id"), nullable=True)
    external_id = Column(String, nullable=True)

    job_roles = relationship("JobRole", back_populates="company")


class JobRole(Base):
    __tablename__ = "job_roles"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String, nullable=True)
    source_account_id = Column(Integer, ForeignKey("source_accounts.id"), nullable=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    title = Column(String, nullable=False)
    normalized_title = Column(String, nullable=True)
    location_city = Column(String, nullable=True)
    location_state = Column(String, nullable=True)
    location_country = Column(String, default="US")
    remote_type = Column(String, default="unknown")  # onsite|hybrid|remote|unknown
    pay_min = Column(Float, nullable=True)
    pay_max = Column(Float, nullable=True)
    pay_unit = Column(String, default="unknown")  # hourly|salary|contract|unknown
    openings_count = Column(Integer, default=1)
    employment_type = Column(String, nullable=True)
    status = Column(String, default="open")  # open|paused|closed|filled|unknown
    recruiter_owner = Column(String, nullable=True)
    client_stage = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    source_updated_at = Column(DateTime, nullable=True)

    company = relationship("Company", back_populates="job_roles")
    applications = relationship("Application", back_populates="job_role")


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String, nullable=True)
    source_account_id = Column(Integer, ForeignKey("source_accounts.id"), nullable=True)
    full_name = Column(String, nullable=False)
    email_hash = Column(String, nullable=True)
    email_display_masked = Column(String, nullable=True)
    phone_hash = Column(String, nullable=True)
    phone_display_masked = Column(String, nullable=True)
    location = Column(String, nullable=True)
    current_title = Column(String, nullable=True)
    current_company = Column(String, nullable=True)
    is_merged_into = Column(Integer, ForeignKey("candidates.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    applications = relationship("Application", back_populates="candidate")


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String, nullable=True)
    source_account_id = Column(Integer, ForeignKey("source_accounts.id"), nullable=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    job_role_id = Column(Integer, ForeignKey("job_roles.id"), nullable=True)
    source = Column(String, nullable=True)
    raw_stage = Column(String, nullable=True)
    canonical_stage = Column(String, default="unknown")
    status = Column(String, default="active")
    applied_at = Column(DateTime, nullable=True)
    last_activity_at = Column(DateTime, nullable=True)
    recruiter_owner = Column(String, nullable=True)
    rejection_reason = Column(String, nullable=True)
    offer_amount = Column(Float, nullable=True)
    notes_summary = Column(Text, nullable=True)

    candidate = relationship("Candidate", back_populates="applications")
    job_role = relationship("JobRole", back_populates="applications")
    pipeline_events = relationship("PipelineEvent", back_populates="application")


class PipelineEvent(Base):
    __tablename__ = "pipeline_events"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    event_type = Column(String, nullable=False)
    from_stage = Column(String, nullable=True)
    to_stage = Column(String, nullable=True)
    occurred_at = Column(DateTime, default=datetime.utcnow)
    source = Column(String, nullable=True)
    raw_json = Column(JSON, nullable=True)

    application = relationship("Application", back_populates="pipeline_events")


class Anomaly(Base):
    __tablename__ = "anomalies"

    id = Column(Integer, primary_key=True, index=True)
    severity = Column(String, nullable=False)  # low|medium|high
    category = Column(String, nullable=False)
    title = Column(String, nullable=False)
    explanation = Column(Text, nullable=False)
    recommended_fix = Column(Text, nullable=False)
    related_entity_type = Column(String, nullable=True)
    related_entity_id = Column(Integer, nullable=True)
    status = Column(String, default="open")  # open|approved|ignored|resolved
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)


class ReportSnapshot(Base):
    __tablename__ = "report_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    generated_at = Column(DateTime, default=datetime.utcnow)
    date_range_start = Column(DateTime, nullable=True)
    date_range_end = Column(DateTime, nullable=True)
    metrics_json = Column(JSON, nullable=True)
    narrative_summary = Column(Text, nullable=True)
    exported_to_sheet_url = Column(String, nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    actor = Column(String, default="system")
    action = Column(String, nullable=False)
    entity_type = Column(String, nullable=True)
    entity_id = Column(Integer, nullable=True)
    before_json = Column(JSON, nullable=True)
    after_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
