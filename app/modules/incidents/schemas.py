from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.modules.incidents.models import Incident, IncidentStatus, IncidentType


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


class IncidentReportIn(BaseModel):
    """What a road user sends when reporting an incident (FR 3)."""

    type: IncidentType
    road_id: int
    description: str = Field(min_length=10, max_length=500)
    reporter_name: Optional[str] = Field(default=None, max_length=120)
    reporter_contact: Optional[str] = Field(default=None, max_length=160)

    @field_validator("description", "reporter_name", "reporter_contact", mode="before")
    @classmethod
    def strip_text(cls, value):
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value

    @field_validator("description")
    @classmethod
    def description_required(cls, value):
        if not value:
            raise ValueError("Please describe what you saw (at least 10 characters).")
        return value


class IncidentReportOut(BaseModel):
    """Confirmation shown after a report is saved. Nothing private is echoed back."""

    reference: str
    status: IncidentStatus
    message: str
