import random
from datetime import datetime, timezone

import pytest

from app.config import Settings
from app.modules.incidents.models import Incident, IncidentStatus, IncidentType
from app.modules.incidents.service import list_public_incidents
from app.modules.simulation.generator import SimulatedDataGenerator, SimulationError, speed_for_delay
from app.modules.simulation.scenarios import Scenario, pick_auto_scenario
from app.modules.traffic.levels import classify_delay
from app.modules.traffic.models import TrafficLevel
from app.modules.traffic.service import get_latest_conditions
from sqlalchemy import select

NOW = datetime(2026, 10, 26, 5, 30, tzinfo=timezone.utc)  # 07:30 in Kigali (UTC+2)


def make_generator(scenario, seed=1):
    return SimulatedDataGenerator(scenario, rng=random.Random(seed), clock=lambda: NOW, settings=Settings())


def test_normal_scenario_is_mostly_free_flow(seeded_db):
    result = make_generator("normal").run_cycle(seeded_db)
    conditions = get_latest_conditions(seeded_db)
    assert result.conditions_created == 3 and len(conditions) == 3
    assert all(c.delay_minutes <= 3 and c.is_simulated for c in conditions)
    assert result.incidents_created == 0


def test_level_always_matches_delay(seeded_db):
    for seed in range(20):
        make_generator("peak_hour", seed).run_cycle(seeded_db)
    for c in get_latest_conditions(seeded_db):
        assert c.level == classify_delay(c.delay_minutes)


def test_peak_hour_has_a_heavy_road(seeded_db):
    make_generator("peak_hour").run_cycle(seeded_db)
    assert any(c.level == TrafficLevel.HEAVY for c in get_latest_conditions(seeded_db))


def test_flooding_blocks_a_road_and_creates_flood_incident(seeded_db):
    result = make_generator("flooding").run_cycle(seeded_db)
    assert any(c.level == TrafficLevel.BLOCKED for c in get_latest_conditions(seeded_db))
    incidents = list_public_incidents(seeded_db)
    assert result.incidents_created == len(incidents) >= 1
    assert all(i.type == IncidentType.FLOODING and i.is_simulated for i in incidents)


def test_incidents_are_cleared_when_scenario_returns_to_normal(seeded_db):
    make_generator("incident").run_cycle(seeded_db)
    assert len(list_public_incidents(seeded_db)) == 1
    result = make_generator("normal").run_cycle(seeded_db)
    assert result.incidents_resolved == 1
    assert list_public_incidents(seeded_db) == []
    assert seeded_db.scalars(select(Incident)).first().status == IncidentStatus.RESOLVED


def test_one_active_simulated_incident_per_road(seeded_db):
    for seed in range(30):
        make_generator("flooding", seed).run_cycle(seeded_db)
    road_ids = [i.road_id for i in list_public_incidents(seeded_db)]
    assert len(road_ids) == len(set(road_ids))


def test_empty_network_gives_clear_error(db):
    with pytest.raises(SimulationError):
        make_generator("normal").run_cycle(db)


def test_unknown_scenario_is_rejected():
    with pytest.raises(ValueError):
        SimulatedDataGenerator("bogus")


def test_set_scenario_accepts_auto_and_names():
    gen = SimulatedDataGenerator("flooding")
    assert gen.scenario == Scenario.FLOODING
    gen.set_scenario("auto")
    assert gen.scenario is None
    gen.set_scenario("Peak-Hour")
    assert gen.scenario == Scenario.PEAK_HOUR


class FixedRoll:
    def __init__(self, value):
        self.value = value

    def random(self):
        return self.value


def test_auto_scenario_follows_local_time():
    kigali = lambda h, m: datetime(2026, 10, 26, h, m, tzinfo=timezone.utc)  # naive hour is used as given
    assert pick_auto_scenario(kigali(7, 30), FixedRoll(0.5)) == Scenario.PEAK_HOUR
    assert pick_auto_scenario(kigali(17, 0), FixedRoll(0.5)) == Scenario.PEAK_HOUR
    assert pick_auto_scenario(kigali(13, 0), FixedRoll(0.5)) == Scenario.NORMAL
    assert pick_auto_scenario(kigali(13, 0), FixedRoll(0.03)) == Scenario.INCIDENT
    assert pick_auto_scenario(kigali(13, 0), FixedRoll(0.005)) == Scenario.FLOODING


def test_auto_uses_kigali_time_not_utc(seeded_db):
    # 05:30 UTC is 07:30 in Kigali, so a quiet roll must give PEAK_HOUR
    class QuietRandom(random.Random):
        def random(self):  # never triggers a random incident or flood
            return 0.5

    gen = SimulatedDataGenerator("auto", rng=QuietRandom(1), clock=lambda: NOW, settings=Settings())
    assert gen.run_cycle(seeded_db).scenario == Scenario.PEAK_HOUR


def test_speed_drops_as_delay_grows():
    free = speed_for_delay(0.8, 0, 30.0)
    slow = speed_for_delay(0.8, 9, 30.0)
    assert free == 30.0 and 0 < slow < free
