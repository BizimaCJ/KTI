from typing import List, Sequence

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session, joinedload

from app.modules.traffic.models import TrafficCondition


def add_many(db: Session, conditions: Sequence[TrafficCondition]) -> None:
    db.add_all(conditions)
    db.flush()


def latest_per_road(db: Session) -> List[TrafficCondition]:
    """The most recent reading for every road that has one."""
    newest = (
        select(
            TrafficCondition.road_id.label("road_id"),
            func.max(TrafficCondition.recorded_at).label("max_at"),
        )
        .group_by(TrafficCondition.road_id)
        .subquery()
    )
    stmt = (
        select(TrafficCondition)
        .join(
            newest,
            and_(
                TrafficCondition.road_id == newest.c.road_id,
                TrafficCondition.recorded_at == newest.c.max_at,
            ),
        )
        .options(joinedload(TrafficCondition.road))
        .order_by(TrafficCondition.road_id, TrafficCondition.id.desc())
    )
    rows = db.scalars(stmt).all()
    unique, seen = [], set()
    for row in rows:  # two rows with the same timestamp: keep the last inserted
        if row.road_id not in seen:
            seen.add(row.road_id)
            unique.append(row)
    return unique
