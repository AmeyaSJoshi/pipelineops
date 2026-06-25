import pytest
from app.services.reporting import _safe_rate, calculate_metrics, calculate_role_metrics
from app.db import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


class TestSafeRate:
    def test_normal(self):
        assert _safe_rate(3, 10) == 0.3

    def test_zero_denominator(self):
        assert _safe_rate(5, 0) == 0.0

    def test_zero_numerator(self):
        assert _safe_rate(0, 10) == 0.0

    def test_placement_rate_avoids_zero_div(self):
        assert _safe_rate(0, 0) == 0.0


class TestStaleRoleCount:
    def test_stale_role_detected(self, db):
        from app.models import Company, JobRole, SourceAccount
        src = SourceAccount(source_type="csv", display_name="CSV", status="demo")
        db.add(src)
        db.flush()
        company = Company(name="Acme", normalized_name="acme")
        db.add(company)
        db.flush()
        stale_role = JobRole(
            company_id=company.id,
            title="Old Role",
            normalized_title="old role",
            status="open",
            pay_unit="unknown",
            remote_type="onsite",
            updated_at=datetime.utcnow() - timedelta(days=20),
            created_at=datetime.utcnow() - timedelta(days=30),
        )
        db.add(stale_role)
        db.commit()

        metrics = calculate_metrics(db)
        assert metrics["stale_role_count"] >= 1

    def test_recent_role_not_stale(self, db):
        from app.models import Company, JobRole, SourceAccount
        src = SourceAccount(source_type="csv", display_name="CSV", status="demo")
        db.add(src)
        db.flush()
        company = Company(name="FreshCo", normalized_name="freshco")
        db.add(company)
        db.flush()
        fresh_role = JobRole(
            company_id=company.id,
            title="New Role",
            normalized_title="new role",
            status="open",
            pay_unit="unknown",
            remote_type="onsite",
            updated_at=datetime.utcnow() - timedelta(days=3),
            created_at=datetime.utcnow() - timedelta(days=5),
        )
        db.add(fresh_role)
        db.commit()

        metrics = calculate_metrics(db)
        assert metrics["stale_role_count"] == 0


class TestHitRate:
    def test_hit_rate_is_placements_over_applicants(self, db):
        from app.models import Company, JobRole, Candidate, Application, SourceAccount
        src = SourceAccount(source_type="csv", display_name="CSV", status="demo")
        db.add(src)
        db.flush()
        company = Company(name="TestCo", normalized_name="testco")
        db.add(company)
        db.flush()
        role = JobRole(company_id=company.id, title="Test Role", normalized_title="test role",
                       status="open", pay_unit="unknown", remote_type="onsite",
                       updated_at=datetime.utcnow(), created_at=datetime.utcnow())
        db.add(role)
        db.flush()

        stages = ["applied", "applied", "applied", "applied", "placed"]
        for i, stage in enumerate(stages):
            c = Candidate(full_name=f"Candidate {i}", source_account_id=src.id)
            db.add(c)
            db.flush()
            app = Application(candidate_id=c.id, job_role_id=role.id,
                               canonical_stage=stage, status="active",
                               source="test", raw_stage=stage)
            db.add(app)

        db.commit()
        metrics = calculate_metrics(db)
        assert metrics["placement_count"] == 1
        assert metrics["overall_hit_rate"] == pytest.approx(1/5, rel=0.01)
