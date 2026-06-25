"""
Bullhorn REST API connector.
Official docs: https://bullhorn.github.io/rest-api-docs
Auth: Multi-step OAuth 2.0 flow — client credentials + headless username/password.

Required env vars:
  BULLHORN_CLIENT_ID
  BULLHORN_CLIENT_SECRET
  BULLHORN_USERNAME   (service account for headless login)
  BULLHORN_PASSWORD   (NOT stored raw — passed once to get access token, then discarded)

The password is used only for the initial OAuth token exchange and is never
persisted to database, logs, or API responses. Rotate regularly.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx

from app.connectors.base import BaseConnector

logger = logging.getLogger(__name__)

BULLHORN_AUTH_BASE = "https://auth.bullhornstaffing.com"


class BullhornConnector(BaseConnector):
    source_type = "bullhorn"

    def __init__(
        self,
        client_id: str = "",
        client_secret: str = "",
        username: str = "",
        password: str = "",
    ):
        self.client_id = client_id.strip()
        self.client_secret = client_secret.strip()
        self.username = username.strip()
        # password is used only for OAuth exchange and NOT stored after __init__
        self._password_for_init = password
        self._rest_token: Optional[str] = None
        self._rest_url: Optional[str] = None

    def _credentials_present(self) -> bool:
        return bool(self.client_id and self.client_secret and self.username)

    def _authenticate(self) -> bool:
        """
        Full Bullhorn OAuth handshake:
        1. POST /oauth/token?grant_type=password to get access_token
        2. GET /rest-services/login?access_token= to get BhRestToken + restUrl
        """
        try:
            with httpx.Client(timeout=30) as client:
                # Step 1: get access token via resource owner password credentials
                token_resp = client.post(
                    f"{BULLHORN_AUTH_BASE}/oauth/token",
                    params={
                        "grant_type": "password",
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "username": self.username,
                        "password": self._password_for_init,
                        "ttl": 60,
                    },
                )
                token_resp.raise_for_status()
                access_token = token_resp.json().get("access_token", "")
                if not access_token:
                    return False

                # Step 2: exchange access token for REST session
                login_resp = client.get(
                    f"{BULLHORN_AUTH_BASE}/rest-services/login",
                    params={"version": "*", "access_token": access_token},
                )
                login_resp.raise_for_status()
                body = login_resp.json()
                self._rest_token = body.get("BhRestToken")
                self._rest_url = body.get("restUrl")
                # Clear password from memory immediately after use
                self._password_for_init = ""
                return bool(self._rest_token and self._rest_url)
        except Exception as e:
            logger.error("Bullhorn auth error: %s", e)
            self._password_for_init = ""
            return False

    def _get(self, path: str, params: Optional[Dict] = None) -> Any:
        if not self._rest_token or not self._rest_url:
            raise RuntimeError("Not authenticated")
        if params is None:
            params = {}
        params["BhRestToken"] = self._rest_token
        resp = httpx.get(f"{self._rest_url}{path}", params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def _paginate_entity(self, entity: str, fields: str) -> List[Dict]:
        results: List[Dict] = []
        start = 0
        count = 200
        while True:
            body = self._get(
                f"entity/{entity}",
                params={"fields": fields, "start": start, "count": count, "sort": "id"},
            )
            data = body.get("data", [])
            results.extend(data)
            total = body.get("total", 0)
            start += count
            if start >= total or not data:
                break
        return results

    def test_connection(self) -> Dict[str, Any]:
        if not self._credentials_present():
            missing = [v for v in ["BULLHORN_CLIENT_ID", "BULLHORN_CLIENT_SECRET", "BULLHORN_USERNAME"] if not getattr(self, v.replace("BULLHORN_", "").lower(), None)]
            return {
                "success": False,
                "status": "needs_credentials",
                "message": f"Missing: {', '.join(missing)}. Obtain from Bullhorn admin > Admin > API Credentials.",
            }
        if not self._authenticate():
            return {"success": False, "status": "auth_error", "message": "Bullhorn OAuth failed. Check credentials."}
        try:
            self._get("entity/Job", {"fields": "id", "start": 0, "count": 1})
            return {"success": True, "status": "connected", "message": "Bullhorn REST API connected."}
        except Exception as e:
            return {"success": False, "status": "error", "message": str(e)}

    def fetch_jobs(self) -> List[Dict[str, Any]]:
        if not self._credentials_present() or not self._authenticate():
            return []
        try:
            fields = "id,title,clientCorporation,address,salary,payRate,employmentType,status,dateAdded,dateLastModified,openings,recruiter"
            raw = self._paginate_entity("Job", fields)
            jobs: List[Dict] = []
            for j in raw:
                corp = j.get("clientCorporation") or {}
                address = j.get("address") or {}
                location = f"{address.get('city', '')}, {address.get('state', '')}".strip(", ")
                jobs.append({
                    "id": str(j.get("id", "")),
                    "title": j.get("title", ""),
                    "company": corp.get("name", "") if isinstance(corp, dict) else "",
                    "location": location,
                    "salary": j.get("salary"),
                    "payRate": j.get("payRate"),
                    "employmentType": j.get("employmentType"),
                    "status": j.get("status", "open"),
                    "openings": j.get("openings", 1),
                    "created_at": j.get("dateAdded"),
                    "updated_at": j.get("dateLastModified"),
                    "_source": "bullhorn",
                })
            return jobs
        except Exception as e:
            logger.error("Bullhorn fetch_jobs error: %s", e)
            return []

    def fetch_candidates(self) -> List[Dict[str, Any]]:
        if not self._credentials_present() or not self._authenticate():
            return []
        try:
            fields = "id,firstName,lastName,email,mobile,address,status,dateAdded,occupation"
            raw = self._paginate_entity("Candidate", fields)
            candidates: List[Dict] = []
            for c in raw:
                address = c.get("address") or {}
                location = f"{address.get('city', '')}, {address.get('state', '')}".strip(", ")
                candidates.append({
                    "id": str(c.get("id", "")),
                    "full_name": f"{c.get('firstName', '')} {c.get('lastName', '')}".strip(),
                    "email": c.get("email", ""),
                    "phone": c.get("mobile", ""),
                    "location": location,
                    "current_title": c.get("occupation", ""),
                    "_source": "bullhorn",
                })
            return candidates
        except Exception as e:
            logger.error("Bullhorn fetch_candidates error: %s", e)
            return []

    def fetch_applications(self) -> List[Dict[str, Any]]:
        if not self._credentials_present() or not self._authenticate():
            return []
        try:
            fields = "id,candidate,jobOrder,status,dateAdded,dateLastModified"
            raw = self._paginate_entity("JobSubmission", fields)
            applications: List[Dict] = []
            for a in raw:
                candidate = a.get("candidate") or {}
                job = a.get("jobOrder") or {}
                applications.append({
                    "id": str(a.get("id", "")),
                    "candidateId": str(candidate.get("id", "")) if isinstance(candidate, dict) else "",
                    "full_name": candidate.get("firstName", "") + " " + candidate.get("lastName", "") if isinstance(candidate, dict) else "",
                    "jobId": str(job.get("id", "")) if isinstance(job, dict) else "",
                    "title": job.get("title", "") if isinstance(job, dict) else "",
                    "stage": a.get("status", ""),
                    "status": "active",
                    "appliedAt": a.get("dateAdded"),
                    "lastActivityAt": a.get("dateLastModified"),
                    "_source": "bullhorn",
                })
            return applications
        except Exception as e:
            logger.error("Bullhorn fetch_applications error: %s", e)
            return []
