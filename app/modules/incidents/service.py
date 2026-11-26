from typing import Sequence

from sqlalchemy.orm import Session

from app.modules.incidents import repository
from app.modules.incidents.models import Incident, IncidentStatus


def list_public_incidents(db: Session) -> Sequence[Incident]:
    """Business rule: road users only see Verified incidents (Resolved ones are gone)."""
    return repository.list_with_status(db, IncidentStatus.VERIFIED)
