from datetime import datetime
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.modules.incidents.models import Incident, IncidentStatus, IncidentType


def list_with_status(db: Session, status: IncidentStatus) -> Sequence[Incident]:
    stmt = (
        select(Incident)
        .where(Incident.status == status)
        .options(joinedload(Incident.road), joinedload(Incident.intersection))
        .order_by(Incident.reported_at.desc(), Incident.id.desc())
    )
    return db.scalars(stmt).all()


def find_active_simulated(db: Session, road_id: Optional[int] = None) -> Sequence[Incident]:
    stmt = select(Incident).where(
        Incident.is_simulated.is_(True), Incident.status == IncidentStatus.VERIFIED
    )
    if road_id is not None:
        stmt = stmt.where(Incident.road_id == road_id)
    return db.scalars(stmt).all()


def add(db: Session, incident: Incident) -> Incident:
    db.add(incident)
    db.flush()
    return incident


def get(db: Session, incident_id: int) -> Optional[Incident]:
    return db.get(Incident, incident_id)


def find_recent_duplicate(
    db: Session, road_id: int, incident_type: IncidentType, since: datetime
) -> Optional[Incident]:
    """A report of the same type on the same road that is still open and was made recently."""
    stmt = select(Incident).where(
        Incident.road_id == road_id,
        Incident.type == incident_type,
        Incident.reported_at >= since,
        Incident.status.in_([IncidentStatus.SUBMITTED, IncidentStatus.UNDER_REVIEW, IncidentStatus.VERIFIED]),
    )
    return db.scalars(stmt).first()
