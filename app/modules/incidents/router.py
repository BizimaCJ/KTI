from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.modules.incidents import service
from app.modules.incidents.models import IncidentStatus
from app.modules.incidents.schemas import IncidentReportIn, IncidentReportOut, PublicIncidentOut

router = APIRouter(prefix="/api/incidents", tags=["incidents"])


@router.get("", response_model=List[PublicIncidentOut])
def public_incidents(db: Session = Depends(get_db)):
    """Verified incidents that are not resolved (FR 2)."""
    return [PublicIncidentOut.from_incident(i) for i in service.list_public_incidents(db)]


@router.post("/report", response_model=IncidentReportOut, status_code=status.HTTP_201_CREATED)
def report_incident(data: IncidentReportIn, db: Session = Depends(get_db)):
    """A road user reports an incident (FR 3). It stays hidden until an administrator verifies it."""
    try:
        incident = service.submit_report(db, data)
    except service.IncidentError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))
    db.commit()
    return IncidentReportOut(
        reference=service.reference_for(incident),
        status=IncidentStatus.SUBMITTED,
        message="Thank you. Your report was received and will be reviewed before it is shown to others.",
    )
