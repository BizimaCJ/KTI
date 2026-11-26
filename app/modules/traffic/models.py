import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, Float, ForeignKey, Index, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.modules.network.models import Road


class TrafficLevel(str, enum.Enum):
    FREE_FLOW = "FREE_FLOW"
    MODERATE = "MODERATE"
    HEAVY = "HEAVY"
    BLOCKED = "BLOCKED"


class TrafficCondition(Base):
    """One reading of the traffic on one road. Old rows are kept as history (FR 10)."""

    __tablename__ = "traffic_conditions"
    __table_args__ = (Index("ix_traffic_road_time", "road_id", "recorded_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    road_id: Mapped[int] = mapped_column(ForeignKey("roads.id"))
    level: Mapped[TrafficLevel] = mapped_column(SAEnum(TrafficLevel, native_enum=False, length=20))
    average_speed_kmh: Mapped[float] = mapped_column(Float)
    delay_minutes: Mapped[int] = mapped_column(Integer)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    is_simulated: Mapped[bool] = mapped_column(Boolean, default=True)

    road: Mapped[Road] = relationship()
