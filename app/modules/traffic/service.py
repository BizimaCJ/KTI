from typing import List

from sqlalchemy.orm import Session

from app.modules.traffic import repository
from app.modules.traffic.models import TrafficCondition


def get_latest_conditions(db: Session) -> List[TrafficCondition]:
    return repository.latest_per_road(db)
