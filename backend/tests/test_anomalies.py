import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db import Base
from app.models import Company, JobRole, Candidate, Application, SourceAccount
from app.services.anomalies import (
    _check_missing_pay_rate, _check_stale_roles,
    _check_offer_no_amount, _check_high_applicant_low_submit,
)


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    src = SourceAccount(source_type="csv", display_name="Test", status="demo")
    session.add(src)
    session.flush()
    company = Company(name="TestCorp", normalized_name="testcorp")
    session.add(company)
    session.flush()

    session.src_id = src.id
    session.company_id = company.id
    yield session
    session.close()


def make_role(db, **kwargs):
    defaults = dict(
        company_id=db.company_id,
        title="Test Role",
        normalized_title="test role",
        status="open",
        pay_unit="unknown",
        remote_type="onsite",
        updated_at=datetime.utcnow(),
        created_at=datetime.utcnow(),
    )
    defaults.update(kwargs)
    role = JobRole(**defaults)
    db.add(role)
    db.flush()
    return role


def make_candidate(db, name="Test Candidate"):
    c = Candidate(full_name=name, source_account_id=db.src_id)
    db.add(c)
    db.flush()
    return c


class TestMissingPayRate:
    def test_detects_missing_pay(self, db):
        make_role(db, pay_min=None, pay_max=None)
        db.commit()
        anomalies = _check_missing_pay_rate(db)
        assert len(anomalies) == 1
        assert anomalies[0]["category"] == "missing_pay_rate"
        assert anomalies[0]["severity"] == "medium"

    def test_no_anomaly_when_pay_set(self, db):
        make_role(db, pay_min=18.0, pay_max=22.0, pay_unit="hourly")
        db.commit()
        anomalies = _check_missing_pay_rate(db)
        assert len(anomalies) == 0

    def test_closed_role_not_flagged(self, db):
        make_role(db, pay_min=None, pay_max=None, status="closed")
        db.commit()
        anomalies = _check_missing_pay_rate(db)
        assert len(anomalies) == 0


class TestStaleRoles:
    def test_detects_stale(self, db):
        make_role(db, updated_at=datetime.utcnow() - timedelta(days=20))
        db.commit()
        anomalies = _check_stale_roles(db)
        assert len(anomalies) == 1
        assert "stale_role" in anomalies[0]["category"]

    def test_high_severity_very_stale(self, db):
        make_role(db, updated_at=datetime.utcnow() - timedelta(days=25))
        db.commit()
        anomalies = _check_stale_roles(db)
        assert anomalies[0]["severity"] == "high"

    def test_recent_not_stale(self, db):
        make_role(db, updated_at=datetime.utcnow() - timedelta(days=5))
        db.commit()
        anomalies = _check_stale_roles(db)
        assert len(anomalies) == 0


class TestOfferNoAmount:
    def test_detects_offer_without_amount(self, db):
        role = make_role(db)
        c = make_candidate(db)
        app = Application(candidate_id=c.id, job_role_id=role.id,
                          canonical_stage="offer", offer_amount=None,
                          status="active", source="test", raw_stage="offer")
        db.add(app)
        db.commit()
        anomalies = _check_offer_no_amount(db)
        assert len(anomalies) == 1
        assert anomalies[0]["severity"] == "high"

    def test_no_anomaly_when_amount_set(self, db):
        role = make_role(db)
        c = make_candidate(db)
        app = Application(candidate_id=c.id, job_role_id=role.id,
                          canonical_stage="offer", offer_amount=45000.0,
                          status="active", source="test", raw_stage="offer")
        db.add(app)
        db.commit()
        anomalies = _check_offer_no_amount(db)
        assert len(anomalies) == 0


class TestHighApplicantLowSubmit:
    def test_detects_bottleneck(self, db):
        role = make_role(db)
        for i in range(6):
            c = make_candidate(db, name=f"Candidate {i}")
            app = Application(candidate_id=c.id, job_role_id=role.id,
                              canonical_stage="applied", status="active",
                              source="test", raw_stage="applied")
            db.add(app)
        db.commit()
        anomalies = _check_high_applicant_low_submit(db)
        assert len(anomalies) == 1
        assert anomalies[0]["severity"] == "high"

    def test_no_anomaly_with_submissions(self, db):
        role = make_role(db)
        for i, stage in enumerate(["applied"] * 3 + ["submitted_to_client"] * 3):
            c = make_candidate(db, name=f"Candidate {i}")
            app = Application(candidate_id=c.id, job_role_id=role.id,
                              canonical_stage=stage, status="active",
                              source="test", raw_stage=stage)
            db.add(app)
        db.commit()
        anomalies = _check_high_applicant_low_submit(db)
        assert len(anomalies) == 0
