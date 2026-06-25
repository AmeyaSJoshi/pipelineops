from app.connectors.base import BaseConnector
from app.connectors.csv_connector import CSVConnector
from app.connectors.demo_indeed_connector import DemoIndeedConnector
from app.connectors.demo_careerbuilder_connector import DemoCareerBuilderConnector
from app.connectors.demo_monster_connector import DemoMonsterConnector
from app.connectors.demo_dice_connector import DemoDiceConnector
from app.connectors.demo_greenhouse_connector import DemoGreenhouseConnector
from app.connectors.demo_lever_connector import DemoLeverConnector
from app.connectors.demo_bullhorn_connector import DemoBullhornConnector

DEMO_CONNECTORS = {
    "indeed": DemoIndeedConnector,
    "careerbuilder": DemoCareerBuilderConnector,
    "monster": DemoMonsterConnector,
    "dice": DemoDiceConnector,
    "greenhouse": DemoGreenhouseConnector,
    "lever": DemoLeverConnector,
    "bullhorn": DemoBullhornConnector,
}

__all__ = [
    "BaseConnector",
    "CSVConnector",
    "DemoIndeedConnector",
    "DemoCareerBuilderConnector",
    "DemoMonsterConnector",
    "DemoDiceConnector",
    "DemoGreenhouseConnector",
    "DemoLeverConnector",
    "DemoBullhornConnector",
    "DEMO_CONNECTORS",
]
