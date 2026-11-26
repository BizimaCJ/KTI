from datetime import datetime, timedelta, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from app.modules.network.models import Road
from app.modules.traffic import repository
from app.modules.traffic.models import TrafficCondition

MAX_HISTORY_HOURS = 72


class UnknownRoad(Exception):
    pass


def get_latest_conditions(db: Session) -> List[TrafficCondition]:
    return repository.latest_per_road(db)


def get_history(
    db: Session, road_id: int, hours: int = 6, now: Optional[datetime] = None
) -> List[TrafficCondition]:
    """Stored readings for one road over the last `hours` hours (FR 10)."""
    if db.get(Road, road_id) is None:
        raise UnknownRoad("Please choose one of the listed roads.")
    hours = max(1, min(hours, MAX_HISTORY_HOURS))
    since = (now or datetime.now(timezone.utc)) - timedelta(hours=hours)
    return repository.history_for_road(db, road_id, since)
