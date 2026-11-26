from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.modules.network import service
from app.modules.network.schemas import RoadOut

router = APIRouter(prefix="/api/network", tags=["network"])


@router.get("/roads", response_model=List[RoadOut])
def list_roads(db: Session = Depends(get_db)):
    return [RoadOut.from_road(r) for r in service.list_roads(db)]
