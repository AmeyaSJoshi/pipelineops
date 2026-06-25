import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# StaticPool ensures all connections share the same in-memory SQLite database
TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Patch db engine before importing app
import app.db as db_module
db_module.engine = test_engine
db_module.SessionLocal = TestSessionLocal

from app.db import Base, get_db
from app.main import app

app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(test_engine)
    yield
    # Clear data between tests without dropping schema
    with test_engine.connect() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())
        conn.commit()


client = TestClient(app)


class TestHealth:
    def test_health_ok(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["agentbox_ready"] is True
        assert data["database"] == "ok"
        assert "version" in data

    def test_health_gmi_not_configured(self):
        resp = client.get("/health")
        data = resp.json()
        assert data["gmi_maas_configured"] is False
        assert "fallback" in data["message"].lower() or "missing" in data["message"].lower()


class TestJobLifecycle:
    def test_run_returns_202(self):
        resp = client.post("/run", json={"task": "detect_anomalies", "params": {}})
        assert resp.status_code == 202
        data = resp.json()
        assert "job_id" in data
        assert data["status"] == "pending"

    def test_get_job_status(self):
        resp = client.post("/run", json={"task": "detect_anomalies", "params": {}})
        job_id = resp.json()["job_id"]
        status_resp = client.get(f"/jobs/{job_id}")
        assert status_resp.status_code == 200
        assert status_resp.json()["job_id"] == job_id

    def test_unknown_task_returns_400(self):
        resp = client.post("/run", json={"task": "invalid_task_xyz", "params": {}})
        assert resp.status_code == 400

    def test_missing_job_returns_404(self):
        resp = client.get("/jobs/nonexistent-job-id-12345")
        assert resp.status_code == 404


class TestDemoEndpoints:
    def test_seed(self):
        resp = client.post("/demo/seed")
        assert resp.status_code == 200
        data = resp.json()
        assert data["sources_created"] > 0
        assert data["candidates_created"] > 0

    def test_reset(self):
        client.post("/demo/seed")
        resp = client.post("/demo/reset")
        assert resp.status_code == 200
        assert "tables_cleared" in resp.json()

    def test_sources_after_seed(self):
        client.post("/demo/seed")
        resp = client.get("/sources")
        assert resp.status_code == 200
        sources = resp.json()["sources"]
        assert len(sources) > 0

    def test_metrics_after_seed(self):
        client.post("/demo/seed")
        resp = client.get("/metrics")
        assert resp.status_code == 200
        m = resp.json()
        assert "open_roles" in m
        assert m["open_roles"] >= 0


class TestReports:
    def test_report_summary(self):
        client.post("/demo/seed")
        resp = client.get("/reports/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert "metrics" in data
        assert "narrative_summary" in data

    def test_anomaly_update(self):
        client.post("/demo/seed")
        import time; time.sleep(0.5)
        # Detect anomalies synchronously via dedicated endpoint
        from app.db import SessionLocal
        with TestSessionLocal() as db:
            from app.services.anomalies import detect_all_anomalies, save_anomalies
            anomaly_dicts = detect_all_anomalies(db)
            save_anomalies(db, anomaly_dicts)
        anomalies = client.get("/reports/anomalies").json()["anomalies"]
        if anomalies:
            aid = anomalies[0]["id"]
            resp = client.patch(f"/reports/anomalies/{aid}", json={"status": "ignored"})
            assert resp.status_code == 200
            assert resp.json()["status"] == "ignored"


class TestChat:
    def test_chat_returns_response(self):
        client.post("/demo/seed")
        resp = client.post("/agent/chat", json={"message": "Which roles are stale?"})
        assert resp.status_code == 200
        data = resp.json()
        assert "response" in data
        assert len(data["response"]) > 0
        assert data["mode"] in ("demo_fallback", "gmi_maas")

    def test_chat_empty_db(self):
        resp = client.post("/agent/chat", json={"message": "How many open roles?"})
        assert resp.status_code == 200
