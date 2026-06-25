from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseConnector(ABC):
    """Abstract base class for all recruiting data source connectors."""

    source_type: str = "unknown"
    display_name: str = "Unknown Source"
    is_demo: bool = False

    def __init__(self, credentials: Dict[str, Any] = None):
        self.credentials = credentials or {}

    @abstractmethod
    def test_connection(self) -> Dict[str, Any]:
        """Test connectivity to the source. Returns {success, message}."""
        pass

    @abstractmethod
    def fetch_jobs(self) -> List[Dict[str, Any]]:
        """Fetch raw job/role records from the source."""
        pass

    @abstractmethod
    def fetch_candidates(self) -> List[Dict[str, Any]]:
        """Fetch raw candidate records from the source."""
        pass

    @abstractmethod
    def fetch_applications(self) -> List[Dict[str, Any]]:
        """Fetch raw application records from the source."""
        pass

    def fetch_events(self) -> List[Dict[str, Any]]:
        """Fetch pipeline stage events. Optional — returns empty by default."""
        return []

    def normalize(self, raw_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Source-specific normalization. Default returns raw records."""
        return raw_records

    def get_status(self) -> str:
        """Returns connector status string."""
        return "demo" if self.is_demo else "needs_credentials"
