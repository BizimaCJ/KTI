from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.modules.incidents.schemas import PublicIncidentOut
from app.modules.traffic.models import TrafficLevel
from app.modules.traffic.schemas import TrafficConditionOut


class OverviewOut(BaseModel):
    generated_at: datetime
    has_data: bool
    simulated: bool
    worst_level: Optional[TrafficLevel]
    roads: List[TrafficConditionOut]
    incidents: List[PublicIncidentOut]
