"""Combines traffic and incident data for the traffic overview page (SD-1)."""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.modules.incidents import service as incidents_service
from app.modules.incidents.schemas import PublicIncidentOut
from app.modules.overview.schemas import OverviewOut
from app.modules.traffic import service as traffic_service
from app.modules.traffic.levels import worst_level
from app.modules.traffic.schemas import TrafficConditionOut


def build_overview(db: Session) -> OverviewOut:
    conditions = traffic_service.get_latest_conditions(db)
    incidents = incidents_service.list_public_incidents(db)
    roads_out = [TrafficConditionOut.from_condition(c) for c in conditions]
    incidents_out = [PublicIncidentOut.from_incident(i) for i in incidents]
    return OverviewOut(
        generated_at=datetime.now(timezone.utc),
        has_data=bool(conditions),
        simulated=any(c.is_simulated for c in conditions) or any(i.is_simulated for i in incidents),
        worst_level=worst_level(c.level for c in conditions),
        roads=roads_out,
        incidents=incidents_out,
    )
