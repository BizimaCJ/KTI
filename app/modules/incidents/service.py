from datetime import datetime, timedelta, timezone
from typing import Optional, Sequence

from sqlalchemy.orm import Session

from app.modules.incidents import repository
from app.modules.incidents.models import Incident, IncidentStatus
from app.modules.incidents.schemas import IncidentReportIn
from app.modules.incidents.status import can_transition
from app.modules.network.models import Road

DUPLICATE_WINDOW_MINUTES = 15


class IncidentError(Exception):
    """Base class for rule violations. `status_code` tells the router how to answer."""

    status_code = 400


class UnknownRoad(IncidentError):
    status_code = 422


class DuplicateReport(IncidentError):
    status_code = 409


class IncidentNotFound(IncidentError):
    status_code = 404


class StatusChangeNotAllowed(IncidentError):
    status_code = 409


def reference_for(incident: Incident) -> str:
    return f"KTI-{incident.id:05d}"


def list_public_incidents(db: Session) -> Sequence[Incident]:
    """Business rule: road users only see Verified incidents (Resolved ones are gone)."""
    return repository.list_with_status(db, IncidentStatus.VERIFIED)


def submit_report(db: Session, data: IncidentReportIn, now: Optional[datetime] = None) -> Incident:
    """Save a road user's report with status Submitted (FR 3).

    Business rules: the road must exist, and the same kind of report on the same road
    within the last 15 minutes is treated as a duplicate. Users can never verify their own report.
    """
    now = now or datetime.now(timezone.utc)
    if db.get(Road, data.road_id) is None:
        raise UnknownRoad("Please choose one of the listed roads.")
    since = now - timedelta(minutes=DUPLICATE_WINDOW_MINUTES)
    if repository.find_recent_duplicate(db, data.road_id, data.type, since):
        raise DuplicateReport(
            "This incident was reported a moment ago and is already being handled. Thank you."
        )
    incident = Incident(
        type=data.type,
        road_id=data.road_id,
        description=data.description,
        reporter_name=data.reporter_name,
        reporter_contact=data.reporter_contact,
        status=IncidentStatus.SUBMITTED,
        reported_at=now,
        is_simulated=False,
    )
    return repository.add(db, incident)


def change_status(
    db: Session, incident_id: int, new_status: IncidentStatus, reason: Optional[str] = None
) -> Incident:
    """Move an incident along the allowed lifecycle (SRS 4.3.1). Used by the admin tools."""
    incident = repository.get(db, incident_id)
    if incident is None:
        raise IncidentNotFound("No incident with that reference.")
    if not can_transition(incident.status, new_status):
        raise StatusChangeNotAllowed(
            f"Cannot change an incident from {incident.status.value} to {new_status.value}."
        )
    incident.status = new_status
    if new_status == IncidentStatus.VERIFIED:
        incident.verified_at = datetime.now(timezone.utc)
    if new_status == IncidentStatus.REJECTED:
        incident.rejection_reason = reason
    db.flush()
    return incident
