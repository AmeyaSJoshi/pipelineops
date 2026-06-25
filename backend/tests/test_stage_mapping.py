"""Dedicated stage mapping tests per spec section 25."""
import pytest
from app.services.normalization import canonicalize_stage


class TestJobBoardStages:
    def test_applied(self):
        assert canonicalize_stage("applied") == "applied"

    def test_new_applicant(self):
        assert canonicalize_stage("new applicant") == "applied"

    def test_application_received(self):
        assert canonicalize_stage("application received") == "applied"

    def test_screened(self):
        assert canonicalize_stage("screened") == "recruiter_screen"

    def test_not_selected(self):
        assert canonicalize_stage("not selected") == "rejected"

    def test_archived(self):
        assert canonicalize_stage("archive") == "rejected"

    def test_rejected(self):
        assert canonicalize_stage("rejected") == "rejected"


class TestStaffingClientStages:
    def test_sent_to_client(self):
        assert canonicalize_stage("sent to client") == "submitted_to_client"

    def test_submitted(self):
        assert canonicalize_stage("submitted") == "submitted_to_client"

    def test_client_review(self):
        assert canonicalize_stage("client review") == "client_review"

    def test_interview(self):
        assert canonicalize_stage("interview") == "interview_scheduled"

    def test_offer_extended(self):
        assert canonicalize_stage("offer extended") == "offer"

    def test_start_date_confirmed(self):
        assert canonicalize_stage("start date confirmed") == "placed"


class TestATSStages:
    def test_phone_screen(self):
        assert canonicalize_stage("phone screen") == "recruiter_screen"

    def test_hiring_manager_review(self):
        assert canonicalize_stage("hiring manager review") == "client_review"

    def test_onsite(self):
        assert canonicalize_stage("onsite") == "interview_scheduled"

    def test_interview_complete(self):
        assert canonicalize_stage("interview complete") == "interview_completed"

    def test_offer(self):
        assert canonicalize_stage("offer") == "offer"

    def test_hired(self):
        assert canonicalize_stage("hired") == "placed"

    def test_approved(self):
        assert canonicalize_stage("approved") == "placed"

    def test_technical_screen(self):
        assert canonicalize_stage("technical screen") == "recruiter_screen"

    def test_hiring_manager_screen(self):
        assert canonicalize_stage("hiring manager screen") == "client_review"


class TestEdgeCases:
    def test_empty_string(self):
        assert canonicalize_stage("") == "unknown"

    def test_none_returns_unknown(self):
        assert canonicalize_stage(None) == "unknown"

    def test_case_insensitive(self):
        assert canonicalize_stage("PHONE SCREEN") == "recruiter_screen"
        assert canonicalize_stage("Sent To Client") == "submitted_to_client"
        assert canonicalize_stage("HIRED") == "placed"

    def test_completely_unknown(self):
        assert canonicalize_stage("some_random_stage_xyz") == "unknown"

    def test_new_lead(self):
        assert canonicalize_stage("new lead") == "new_lead"

    def test_withdrawn(self):
        assert canonicalize_stage("withdrawn") == "withdrawn"
        assert canonicalize_stage("candidate withdrew") == "withdrawn"
