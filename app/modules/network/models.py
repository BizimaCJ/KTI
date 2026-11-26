import enum
from typing import Optional

from sqlalchemy import Enum as SAEnum, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class NodeType(str, enum.Enum):
    TERMINAL = "TERMINAL"
    JUNCTION = "JUNCTION"


class Intersection(Base):
    __tablename__ = "intersections"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    node_type: Mapped[NodeType] = mapped_column(
        SAEnum(NodeType, native_enum=False, length=20), default=NodeType.JUNCTION
    )
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)


class Road(Base):
    __tablename__ = "roads"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160), unique=True)
    length_km: Mapped[float] = mapped_column(Float)
    start_intersection_id: Mapped[int] = mapped_column(ForeignKey("intersections.id"))
    end_intersection_id: Mapped[int] = mapped_column(ForeignKey("intersections.id"))

    start_intersection: Mapped[Intersection] = relationship(foreign_keys=[start_intersection_id])
    end_intersection: Mapped[Intersection] = relationship(foreign_keys=[end_intersection_id])
