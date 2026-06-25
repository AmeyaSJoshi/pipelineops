"""
Greenhouse Harvest API v1 connector.
Official docs: https://developers.greenhouse.io/harvest
Auth: HTTP Basic with API key as username, empty password.
Rate limit: 50 req/s. Pagination via Link header or ?page=N&per_page=500.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List

import httpx

from app.connectors.base import BaseConnector

logger = logging.getLogger(__name__)

HARVEST_BASE = "https://harvest.greenhouse.io/v1"


class GreenhouseConnector(BaseConnector):
    source_type = "greenhouse"

    def __init__(self, api_key: str = ""):
        self.api_key = api_key.strip()

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _client(self) -> httpx.Client:
        return httpx.Client(
            auth=(self.api_key, ""),
            headers={"On-Behalf-Of": "pipelineops-agent"},
            timeout=30,
        )

    def _paginate(self, path: str, params: Dict[str, Any] | None = None) -> List[Dict]:
        """Fetch all pages from a Greenhouse endpoint."""
        if params is None:
            params = {}
        params.setdefault("per_page", 500)
        results: List[Dict] = []
        page = 1
        with self._client() as client:
            while True:
                params["page"] = page
                resp = client.get(f"{HARVEST_BASE}{path}", params=params)
                resp.raise_for_status()
                data = resp.json()
                if not data:
                    break
                results.extend(data)
                # Greenhouse uses Link header for pagination
                link_header = resp.headers.get("link", "")
                if 'rel="next"' not in link_header:
                    break
                page += 1
        return results

    # ── BaseConnector interface ───────────────────────────────────────────────

    def test_connection(self) -> Dict[str, Any]:
        if not self.api_key:
            return {
                "success": False,
                "status": "needs_credentials",
                "message": "GREENHOUSE_API_KEY not set. Obtain from Greenhouse admin: Configure > Dev Center > API Credential Management.",
            }
        try:
            with self._client() as client:
                resp = client.get(f"{HARVEST_BASE}/jobs", params={"per_page": 1, "page": 1})
                resp.raise_for_status()
            return {"success": True, "status": "connected", "message": "Greenhouse Harvest API connected."}
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                return {"success": False, "status": "auth_error", "message": "Invalid Greenhouse API key."}
            return {"success": False, "status": "error", "message": str(e)}
        except Exception as e:
            return {"success": False, "status": "error", "message": str(e)}

    def fetch_jobs(self) -> List[Dict[str, Any]]:
        if not self.api_key:
            return []
        try:
            raw = self._paginate("/jobs", {"status": "open"})
            jobs: List[Dict] = []
            for j in raw:
                offices = j.get("offices") or []
                location = offices[0].get("name", "") if offices else ""
                departments = j.get("departments") or []
                dept = departments[0].get("name", "") if departments else ""
                openings = j.get("openings") or []
                open_count = sum(1 for o in openings if o.get("status") == "open") or len(openings) or 1
                jobs.append({
                    "id": str(j["id"]),
                    "title": j.get("name", ""),
                    "company": j.get("company_name") or "",
                    "location": location,
                    "department": dept,
                    "status": j.get("status", "open"),
                    "openings": open_count,
                    "created_at": j.get("created_at"),
                    "updated_at": j.get("updated_at"),
                    "_source": "greenhouse",
                })
            return jobs
        except Exception as e:
            logger.error("Greenhouse fetch_jobs error: %s", e)
            return []

    def fetch_candidates(self) -> List[Dict[str, Any]]:
        if not self.api_key:
            return []
        try:
            raw = self._paginate("/candidates")
            candidates: List[Dict] = []
            for c in raw:
                emails = c.get("email_addresses") or []
                email = emails[0].get("value", "") if emails else ""
                phones = c.get("phone_numbers") or []
                phone = phones[0].get("value", "") if phones else ""
                addresses = c.get("addresses") or []
                location = addresses[0].get("value", "") if addresses else ""
                candidates.append({
                    "id": str(c["id"]),
                    "full_name": f"{c.get('first_name', '')} {c.get('last_name', '')}".strip(),
                    "email": email,
                    "phone": phone,
                    "location": location,
                    "current_title": None,  # Greenhouse candidates don't have current_title at top level
                    "_source": "greenhouse",
                })
            return candidates
        except Exception as e:
            logger.error("Greenhouse fetch_candidates error: %s", e)
            return []

    def fetch_applications(self) -> List[Dict[str, Any]]:
        if not self.api_key:
            return []
        try:
            raw = self._paginate("/applications")
            applications: List[Dict] = []
            for a in raw:
                candidate = a.get("candidate") or {}
                emails = candidate.get("email_addresses") or []
                email = emails[0].get("value", "") if emails else ""
                phones = candidate.get("phone_numbers") or []
                phone = phones[0].get("value", "") if phones else ""
                current_stage = a.get("current_stage") or {}
                stage_name = current_stage.get("name", "") if isinstance(current_stage, dict) else ""
                job = (a.get("jobs") or [{}])[0]
                applications.append({
                    "id": str(a["id"]),
                    "full_name": f"{candidate.get('first_name', '')} {candidate.get('last_name', '')}".strip(),
                    "email": email,
                    "phone": phone,
                    "jobId": str(job.get("id", "")),
                    "title": job.get("name", ""),
                    "stage": stage_name,
                    "status": a.get("status", "active"),
                    "appliedAt": a.get("applied_at"),
                    "lastActivityAt": a.get("last_activity_at"),
                    "candidateId": str(candidate.get("id", "")),
                    "_source": "greenhouse",
                })
            return applications
        except Exception as e:
            logger.error("Greenhouse fetch_applications error: %s", e)
            return []
