from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.modules.traffic import service
from app.modules.traffic.schemas import TrafficConditionOut

router = APIRouter(prefix="/api/traffic", tags=["traffic"])


@router.get("/conditions", response_model=List[TrafficConditionOut])
def latest_conditions(db: Session = Depends(get_db)):
    """Latest traffic level for each road (FR 1)."""
    return [TrafficConditionOut.from_condition(c) for c in service.get_latest_conditions(db)]


@router.get("/history", response_model=List[TrafficConditionOut])
def traffic_history(
    road_id: int,
    hours: int = Query(6, ge=1, le=service.MAX_HISTORY_HOURS),
    db: Session = Depends(get_db),
):
    """Stored readings for one road over the last few hours, newest first (FR 10)."""
    try:
        rows = service.get_history(db, road_id, hours)
    except service.UnknownRoad as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return [TrafficConditionOut.from_condition(c) for c in rows]
