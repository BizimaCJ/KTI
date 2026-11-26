from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.modules.overview import service
from app.modules.overview.schemas import OverviewOut

router = APIRouter(prefix="/api", tags=["overview"])


@router.get("/overview", response_model=OverviewOut)
def overview(db: Session = Depends(get_db)):
    """Everything the traffic overview page needs in one request."""
    return service.build_overview(db)
