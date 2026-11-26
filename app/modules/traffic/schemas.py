from datetime import datetime

from pydantic import BaseModel

from app.modules.traffic.models import TrafficCondition, TrafficLevel


class TrafficConditionOut(BaseModel):
    road_id: int
    road_name: str
    length_km: float
    level: TrafficLevel
    delay_minutes: int
    average_speed_kmh: float
    recorded_at: datetime
    is_simulated: bool

    @classmethod
    def from_condition(cls, c: TrafficCondition) -> "TrafficConditionOut":
        return cls(
            road_id=c.road_id,
            road_name=c.road.name,
            length_km=c.road.length_km,
            level=c.level,
            delay_minutes=c.delay_minutes,
            average_speed_kmh=c.average_speed_kmh,
            recorded_at=c.recorded_at,
            is_simulated=c.is_simulated,
        )
