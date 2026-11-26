from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.modules.incidents.models import Incident, IncidentType


class PublicIncidentOut(BaseModel):
    """What the public may see. Reporter details and rejection reasons are never included."""

    id: int
    type: IncidentType
    description: str
    road_id: int
    road_name: str
    intersection_name: Optional[str]
    reported_at: datetime
    verified_at: Optional[datetime]
    is_simulated: bool

    @classmethod
    def from_incident(cls, i: Incident) -> "PublicIncidentOut":
        return cls(
            id=i.id,
            type=i.type,
            description=i.description,
            road_id=i.road_id,
            road_name=i.road.name,
            intersection_name=i.intersection.name if i.intersection else None,
            reported_at=i.reported_at,
            verified_at=i.verified_at,
            is_simulated=i.is_simulated,
        )
