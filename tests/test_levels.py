import pytest

from app.config import Settings
from app.modules.traffic.levels import classify_delay, worst_level
from app.modules.traffic.models import TrafficLevel as L


@pytest.mark.parametrize(
    "delay,expected",
    [(0, L.FREE_FLOW), (2, L.FREE_FLOW), (3, L.MODERATE), (7, L.MODERATE),
     (8, L.HEAVY), (15, L.HEAVY), (16, L.BLOCKED), (60, L.BLOCKED)],
)
def test_srs_boundaries(delay, expected):
    assert classify_delay(delay, Settings()) == expected


def test_negative_delay_is_rejected():
    with pytest.raises(ValueError):
        classify_delay(-1, Settings())


def test_thresholds_are_configurable():
    strict = Settings(free_flow_max_delay=0, moderate_max_delay=2, heavy_max_delay=5)
    assert classify_delay(1, strict) == L.MODERATE
    assert classify_delay(6, strict) == L.BLOCKED


def test_worst_level():
    assert worst_level([L.FREE_FLOW, L.HEAVY, L.MODERATE]) == L.HEAVY
    assert worst_level([L.BLOCKED, L.HEAVY]) == L.BLOCKED
    assert worst_level([]) is None
