"""Traffic level rules (SRS section 4.3.2). Pure functions, easy to test."""
from typing import Iterable, Optional

from app.config import Settings, get_settings
from app.modules.traffic.models import TrafficLevel

SEVERITY = {
    TrafficLevel.FREE_FLOW: 0,
    TrafficLevel.MODERATE: 1,
    TrafficLevel.HEAVY: 2,
    TrafficLevel.BLOCKED: 3,
}


def classify_delay(delay_minutes: int, settings: Optional[Settings] = None) -> TrafficLevel:
    """Map the extra delay on a road (minutes) to a traffic level."""
    if delay_minutes < 0:
        raise ValueError("delay_minutes cannot be negative")
    s = settings or get_settings()
    if delay_minutes <= s.free_flow_max_delay:
        return TrafficLevel.FREE_FLOW
    if delay_minutes <= s.moderate_max_delay:
        return TrafficLevel.MODERATE
    if delay_minutes <= s.heavy_max_delay:
        return TrafficLevel.HEAVY
    return TrafficLevel.BLOCKED


def worst_level(levels: Iterable[TrafficLevel]) -> Optional[TrafficLevel]:
    levels = list(levels)
    return max(levels, key=lambda lv: SEVERITY[lv]) if levels else None
