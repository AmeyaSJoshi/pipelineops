import pytest
from app.services.normalization import (
    parse_pay_range, parse_location, normalize_title, normalize_company,
    hash_email, mask_email, mask_phone, canonicalize_stage, detect_remote_type,
)


# ── Pay parsing ───────────────────────────────────────────────────────────────

class TestPayParsing:
    def test_hourly_range(self):
        mn, mx, unit = parse_pay_range("$18 - $22 an hour")
        assert mn == 18
        assert mx == 22
        assert unit == "hourly"

    def test_hourly_range_slash(self):
        mn, mx, unit = parse_pay_range("$18-$22/hr")
        assert mn == 18
        assert mx == 22
        assert unit == "hourly"

    def test_salary_k(self):
        mn, mx, unit = parse_pay_range("$70k-$85k")
        assert mn == 70000
        assert mx == 85000
        assert unit == "salary"

    def test_up_to(self):
        mn, mx, unit = parse_pay_range("up to $45/hr")
        assert mx == 45
        assert unit == "hourly"

    def test_full_salary(self):
        mn, mx, unit = parse_pay_range("$120,000 - $150,000")
        assert mn == 120000
        assert mx == 150000
        assert unit == "salary"

    def test_doe(self):
        mn, mx, unit = parse_pay_range("DOE")
        assert mn is None
        assert mx is None
        assert unit == "unknown"

    def test_empty(self):
        mn, mx, unit = parse_pay_range("")
        assert mn is None
        assert mx is None

    def test_none(self):
        mn, mx, unit = parse_pay_range(None)
        assert mn is None
        assert mx is None

    def test_hourly_single(self):
        mn, mx, unit = parse_pay_range("$25/hr")
        assert mx == 25
        assert unit == "hourly"


# ── Location parsing ──────────────────────────────────────────────────────────

class TestLocationParsing:
    def test_city_state(self):
        loc = parse_location("Dallas, TX")
        assert loc["city"] == "Dallas"
        assert loc["state"] == "TX"
        assert loc["remote_type"] == "onsite"

    def test_remote(self):
        loc = parse_location("Remote")
        assert loc["remote_type"] == "remote"
        assert loc["city"] is None

    def test_us_remote(self):
        loc = parse_location("United States Remote")
        assert loc["remote_type"] == "remote"

    def test_hybrid(self):
        loc = parse_location("Hybrid - Chicago, IL")
        assert loc["remote_type"] == "hybrid"
        assert loc["state"] == "IL"

    def test_san_jose(self):
        loc = parse_location("San Jose, CA")
        assert loc["city"] == "San Jose"
        assert loc["state"] == "CA"


# ── Stage mapping ─────────────────────────────────────────────────────────────

class TestStageMapping:
    def test_sent_to_client(self):
        assert canonicalize_stage("sent to client") == "submitted_to_client"

    def test_phone_screen(self):
        assert canonicalize_stage("phone screen") == "recruiter_screen"

    def test_offer_extended(self):
        assert canonicalize_stage("offer extended") == "offer"

    def test_hired(self):
        assert canonicalize_stage("hired") == "placed"

    def test_not_selected(self):
        assert canonicalize_stage("not selected") == "rejected"

    def test_applied(self):
        assert canonicalize_stage("applied") == "applied"

    def test_new_applicant(self):
        assert canonicalize_stage("new applicant") == "applied"

    def test_interview(self):
        assert canonicalize_stage("interview") == "interview_scheduled"

    def test_submitted(self):
        assert canonicalize_stage("submitted") == "submitted_to_client"

    def test_hiring_manager_review(self):
        assert canonicalize_stage("hiring manager review") == "client_review"

    def test_unknown(self):
        assert canonicalize_stage("some_weird_stage_xyz") == "unknown"

    def test_empty(self):
        assert canonicalize_stage("") == "unknown"

    def test_case_insensitive(self):
        assert canonicalize_stage("Phone Screen") == "recruiter_screen"


# ── Email / phone masking ─────────────────────────────────────────────────────

class TestMasking:
    def test_mask_email(self):
        result = mask_email("john.doe@example.com")
        assert "@" in result
        assert "john" not in result
        assert result.endswith(".com")

    def test_hash_email_consistent(self):
        h1 = hash_email("test@example.com")
        h2 = hash_email("TEST@EXAMPLE.COM")
        assert h1 == h2  # case-normalized

    def test_mask_phone(self):
        result = mask_phone("214-555-0101")
        assert "0101" in result
        assert result.startswith("***")

    def test_mask_none(self):
        assert mask_email(None) is None
        assert mask_phone(None) is None


# ── Title / company normalization ─────────────────────────────────────────────

class TestNormalization:
    def test_normalize_title(self):
        assert normalize_title("warehouse ASSOCIATE") == "Warehouse Associate"

    def test_normalize_company_strips_suffix(self):
        result = normalize_company("Acme Logistics Inc.")
        assert "inc" not in result.lower()

    def test_detect_remote(self):
        assert detect_remote_type("Remote position") == "remote"
        assert detect_remote_type("Hybrid - Chicago") == "hybrid"
        assert detect_remote_type("Onsite Dallas") == "onsite"
