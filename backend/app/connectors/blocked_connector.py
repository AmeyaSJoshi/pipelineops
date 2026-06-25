"""
Base class for connectors that are blocked due to no official public API.
Returns a structured blocked-state response instead of fake data.
"""
from __future__ import annotations

from typing import Any, Dict, List

from app.connectors.base import BaseConnector


class BlockedConnector(BaseConnector):
    """
    Connector for sources with no official public API.
    Returns blocked-state metadata instead of data.
    """
    source_type: str = "blocked"
    block_reason: str = "No official public API available."
    path_to_unblock: str = "Contact the vendor's partner program."
    workaround: str = "Export data manually as CSV and upload via the CSV connector."

    def test_connection(self) -> Dict[str, Any]:
        return {
            "success": False,
            "status": "blocked",
            "source": self.source_type,
            "reason": self.block_reason,
            "path_to_unblock": self.path_to_unblock,
            "workaround": self.workaround,
        }

    def fetch_jobs(self) -> List[Dict[str, Any]]:
        return []

    def fetch_candidates(self) -> List[Dict[str, Any]]:
        return []

    def fetch_applications(self) -> List[Dict[str, Any]]:
        return []

    def connector_status(self) -> Dict[str, Any]:
        return {
            "source": self.source_type,
            "status": "blocked",
            "reason": self.block_reason,
            "path_to_unblock": self.path_to_unblock,
            "workaround": self.workaround,
            "jobs": [],
            "candidates": [],
            "applications": [],
        }
