"""
Connector registry.

BLOCKED connectors (Indeed, CareerBuilder, Monster, Dice):
  No official public API verified as of 2026-06-25.
  See CONNECTOR_AUDIT.md for details.
  These return structured blocked-state responses — no fake data.

LIVE connectors (Greenhouse, Lever, Bullhorn):
  Real API calls. Require credentials in env. Degrade gracefully if creds absent.

FILE connectors (CSV, Excel):
  Direct file upload. No external API.
"""
from app.connectors.base import BaseConnector
from app.connectors.csv_connector import CSVConnector

# Real API-backed connectors
from app.connectors.greenhouse_connector import GreenhouseConnector
from app.connectors.lever_connector import LeverConnector
from app.connectors.bullhorn_connector import BullhornConnector

# Blocked stubs — no fake data
from app.connectors.indeed_connector import IndeedConnector
from app.connectors.careerbuilder_connector import CareerBuilderConnector
from app.connectors.monster_connector import MonsterConnector
from app.connectors.dice_connector import DiceConnector

# Blocked connector base
from app.connectors.blocked_connector import BlockedConnector


def build_live_connectors(settings) -> dict:
    """
    Instantiate live connectors using credentials from settings.
    Returns dict of {source_type: connector_instance}.
    Connectors with missing creds will return needs_credentials status but won't crash.
    """
    return {
        "greenhouse": GreenhouseConnector(
            api_key=getattr(settings, "GREENHOUSE_API_KEY", ""),
        ),
        "lever": LeverConnector(
            api_key=getattr(settings, "LEVER_API_KEY", ""),
        ),
        "bullhorn": BullhornConnector(
            client_id=getattr(settings, "BULLHORN_CLIENT_ID", ""),
            client_secret=getattr(settings, "BULLHORN_CLIENT_SECRET", ""),
            username=getattr(settings, "BULLHORN_USERNAME", ""),
            password=getattr(settings, "BULLHORN_PASSWORD", ""),
        ),
    }


BLOCKED_CONNECTORS = {
    "indeed": IndeedConnector,
    "careerbuilder": CareerBuilderConnector,
    "monster": MonsterConnector,
    "dice": DiceConnector,
}

LIVE_CONNECTOR_CLASSES = {
    "greenhouse": GreenhouseConnector,
    "lever": LeverConnector,
    "bullhorn": BullhornConnector,
}

ALL_SOURCE_TYPES = list(LIVE_CONNECTOR_CLASSES.keys()) + list(BLOCKED_CONNECTORS.keys()) + ["csv"]

__all__ = [
    "BaseConnector",
    "BlockedConnector",
    "CSVConnector",
    "GreenhouseConnector",
    "LeverConnector",
    "BullhornConnector",
    "IndeedConnector",
    "CareerBuilderConnector",
    "MonsterConnector",
    "DiceConnector",
    "build_live_connectors",
    "BLOCKED_CONNECTORS",
    "LIVE_CONNECTOR_CLASSES",
    "ALL_SOURCE_TYPES",
]
