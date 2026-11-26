from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.modules.incidents import service
from app.modules.incidents.schemas import PublicIncidentOut

router = APIRouter(prefix="/api/incidents", tags=["incidents"])


@router.get("", response_model=List[PublicIncidentOut])
def public_incidents(db: Session = Depends(get_db)):
    """Verified incidents that are not resolved (FR 2)."""
    return [PublicIncidentOut.from_incident(i) for i in service.list_public_incidents(db)]
