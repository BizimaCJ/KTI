from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.modules.traffic import service
from app.modules.traffic.schemas import TrafficConditionOut

router = APIRouter(prefix="/api/traffic", tags=["traffic"])


@router.get("/conditions", response_model=List[TrafficConditionOut])
def latest_conditions(db: Session = Depends(get_db)):
    """Latest traffic level for each road (FR 1)."""
    return [TrafficConditionOut.from_condition(c) for c in service.get_latest_conditions(db)]
