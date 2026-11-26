"""Database access for the road network. No business rules here."""
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.modules.network.models import Intersection, Road


def list_roads(db: Session) -> Sequence[Road]:
    stmt = (
        select(Road)
        .options(joinedload(Road.start_intersection), joinedload(Road.end_intersection))
        .order_by(Road.id)
    )
    return db.scalars(stmt).all()


def get_intersection_by_name(db: Session, name: str) -> Optional[Intersection]:
    return db.scalars(select(Intersection).where(Intersection.name == name)).first()


def get_road_by_name(db: Session, name: str) -> Optional[Road]:
    return db.scalars(select(Road).where(Road.name == name)).first()


def add(db: Session, obj):
    db.add(obj)
    db.flush()
    return obj
