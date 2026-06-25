"""
Lever Data API v1 connector.
Official docs: https://hire.lever.co/developer/documentation
Auth: HTTP Basic with API key as username, empty password.
Rate limit: 10 req/s. Pagination via cursor offset in JSON response.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx

from app.connectors.base import BaseConnector

logger = logging.getLogger(__name__)

LEVER_BASE = "https://api.lever.co/v1"


class LeverConnector(BaseConnector):
    source_type = "lever"

    def __init__(self, api_key: str = ""):
        self.api_key = api_key.strip()

    def _client(self) -> httpx.Client:
        return httpx.Client(
            auth=(self.api_key, ""),
            timeout=30,
        )

    def _paginate(self, path: str, params: Optional[Dict[str, Any]] = None) -> List[Dict]:
        """Cursor-based pagination for Lever API."""
        if params is None:
            params = {}
        params.setdefault("limit", 100)
        results: List[Dict] = []
        with self._client() as client:
            while True:
                resp = client.get(f"{LEVER_BASE}{path}", params=params)
                resp.raise_for_status()
                body = resp.json()
                data = body.get("data", [])
                results.extend(data)
                if not body.get("hasNext") or not data:
                    break
                # Advance cursor to the last item's id
                params["offset"] = body.get("next")
                if not params["offset"]:
                    break
        return results

    def test_connection(self) -> Dict[str, Any]:
        if not self.api_key:
            return {
                "success": False,
                "status": "needs_credentials",
                "message": "LEVER_API_KEY not set. Obtain from Lever admin: Settings > Integrations & API > API Credentials.",
            }
        try:
            with self._client() as client:
                resp = client.get(f"{LEVER_BASE}/postings", params={"limit": 1})
                resp.raise_for_status()
            return {"success": True, "status": "connected", "message": "Lever Data API connected."}
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (401, 403):
                return {"success": False, "status": "auth_error", "message": "Invalid Lever API key or insufficient permissions."}
            return {"success": False, "status": "error", "message": str(e)}
        except Exception as e:
            return {"success": False, "status": "error", "message": str(e)}

    def fetch_jobs(self) -> List[Dict[str, Any]]:
        if not self.api_key:
            return []
        try:
            raw = self._paginate("/postings", {"state": "published"})
            jobs: List[Dict] = []
            for p in raw:
                location = (p.get("workplaceType") or "")
                location_tag = next(
                    (t.get("text", "") for t in (p.get("tags") or []) if "," in t.get("text", "")),
                    p.get("categories", {}).get("location", "") if isinstance(p.get("categories"), dict) else ""
                )
                salary_range = p.get("salaryRange") or {}
                pay_min = salary_range.get("min")
                pay_max = salary_range.get("max")
                pay_unit = salary_range.get("interval", "salary")
                jobs.append({
                    "id": p.get("id", ""),
                    "title": p.get("text", ""),
                    "company": p.get("hiringOrganization", {}).get("name", "") if isinstance(p.get("hiringOrganization"), dict) else "",
                    "location": location_tag or location,
                    "department": (p.get("categories") or {}).get("department", "") if isinstance(p.get("categories"), dict) else "",
                    "status": p.get("state", "published"),
                    "pay": f"{pay_min}-{pay_max} {pay_unit}" if pay_min and pay_max else "",
                    "created_at": p.get("createdAt"),
                    "updated_at": p.get("updatedAt"),
                    "_source": "lever",
                })
            return jobs
        except Exception as e:
            logger.error("Lever fetch_jobs error: %s", e)
            return []

    def fetch_candidates(self) -> List[Dict[str, Any]]:
        """Lever calls these 'contacts' — return distinct candidate records."""
        if not self.api_key:
            return []
        try:
            raw = self._paginate("/contacts")
            candidates: List[Dict] = []
            for c in raw:
                emails = c.get("emails") or []
                email = emails[0] if emails else ""
                phones = c.get("phones") or []
                phone = phones[0].get("value", "") if phones and isinstance(phones[0], dict) else (phones[0] if phones else "")
                candidates.append({
                    "id": c.get("id", ""),
                    "full_name": c.get("name", ""),
                    "email": email,
                    "phone": phone,
                    "location": c.get("location", ""),
                    "current_title": c.get("headline", ""),
                    "_source": "lever",
                })
            return candidates
        except Exception as e:
            logger.error("Lever fetch_candidates error: %s", e)
            return []

    def fetch_applications(self) -> List[Dict[str, Any]]:
        """Lever 'opportunities' are the combined candidate+application entity."""
        if not self.api_key:
            return []
        try:
            raw = self._paginate("/opportunities")
            applications: List[Dict] = []
            for opp in raw:
                contact = opp.get("contact") or {}
                emails = contact.get("emails") or opp.get("emails") or []
                email = emails[0] if emails else ""
                phones = contact.get("phones") or opp.get("phones") or []
                if phones:
                    phone_entry = phones[0]
                    phone = phone_entry.get("value", phone_entry) if isinstance(phone_entry, dict) else phone_entry
                else:
                    phone = ""
                stage_obj = opp.get("stage") or {}
                stage_name = stage_obj.get("text", "") if isinstance(stage_obj, dict) else ""
                posting = (opp.get("applications") or [{}])[0]
                applications.append({
                    "id": opp.get("id", ""),
                    "full_name": opp.get("name", ""),
                    "email": email,
                    "phone": phone,
                    "current_title": opp.get("headline", ""),
                    "jobId": posting.get("posting", "") if isinstance(posting, dict) else "",
                    "stage": stage_name,
                    "status": "active" if not opp.get("archived") else "archived",
                    "appliedAt": opp.get("createdAt"),
                    "lastActivityAt": opp.get("lastInteractionAt"),
                    "_source": "lever",
                })
            return applications
        except Exception as e:
            logger.error("Lever fetch_applications error: %s", e)
            return []
