import enum
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.modules.network.models import Intersection, Road


class IncidentType(str, enum.Enum):
    CRASH = "CRASH"
    FLOODING = "FLOODING"
    ROADWORKS = "ROADWORKS"
    BLOCKAGE = "BLOCKAGE"
    OTHER = "OTHER"


class IncidentStatus(str, enum.Enum):
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    VERIFIED = "VERIFIED"
    RESOLVED = "RESOLVED"
    REJECTED = "REJECTED"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[IncidentType] = mapped_column(SAEnum(IncidentType, native_enum=False, length=20))
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[IncidentStatus] = mapped_column(
        SAEnum(IncidentStatus, native_enum=False, length=20), default=IncidentStatus.SUBMITTED, index=True
    )
    reported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    reporter_name: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    reporter_contact: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_simulated: Mapped[bool] = mapped_column(Boolean, default=False)

    road_id: Mapped[int] = mapped_column(ForeignKey("roads.id"))
    intersection_id: Mapped[Optional[int]] = mapped_column(ForeignKey("intersections.id"), nullable=True)

    road: Mapped[Road] = relationship()
    intersection: Mapped[Optional[Intersection]] = relationship()
