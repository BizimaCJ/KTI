"""SimulatedDataGenerator (class diagram CD-1, sequence diagram SD-8).

Each cycle it saves one TrafficCondition per road and, for incident scenarios,
simulated Verified incidents. Everything it writes is flagged is_simulated=True.
"""
import random
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, List, Optional, Union
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.modules.incidents import repository as incident_repo
from app.modules.incidents.models import Incident, IncidentStatus, IncidentType
from app.modules.network.models import Road
from app.modules.network.repository import list_roads
from app.modules.simulation.scenarios import PROFILES, Scenario, pick_auto_scenario
from app.modules.traffic import repository as traffic_repo
from app.modules.traffic.levels import classify_delay
from app.modules.traffic.models import TrafficCondition

_DESCRIPTIONS = {
    IncidentType.CRASH: "Simulated crash reported on {road}. Expect delays.",
    IncidentType.FLOODING: "Simulated flooding on {road}. Traffic is slow or stopped.",
    IncidentType.ROADWORKS: "Simulated roadworks on {road}. One lane may be closed.",
    IncidentType.BLOCKAGE: "Simulated blockage on {road}. Use another route if you can.",
    IncidentType.OTHER: "Simulated incident on {road}.",
}


class SimulationError(Exception):
    pass


@dataclass
class CycleResult:
    scenario: Scenario
    recorded_at: datetime
    conditions_created: int
    incidents_created: int
    incidents_resolved: int


def speed_for_delay(length_km: float, delay_minutes: int, free_flow_speed_kmh: float) -> float:
    """Average speed on a road when the free-flow travel time is stretched by the delay."""
    free_minutes = length_km / free_flow_speed_kmh * 60
    return round(length_km / ((free_minutes + delay_minutes) / 60), 1)


class SimulatedDataGenerator:
    def __init__(
        self,
        scenario: Union[Scenario, str, None] = "auto",
        refresh_interval_seconds: Optional[int] = None,
        settings: Optional[Settings] = None,
        rng: Optional[random.Random] = None,
        clock: Optional[Callable[[], datetime]] = None,
    ):
        self.settings = settings or get_settings()
        self.refresh_interval_seconds = refresh_interval_seconds or self.settings.simulation_interval_seconds
        self.rng = rng or random.Random()
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.scenario: Optional[Scenario] = None
        self.set_scenario(scenario)

    # --- configuration -------------------------------------------------
    def set_scenario(self, scenario: Union[Scenario, str, None]) -> None:
        """Set the scenario, or 'auto' / None to choose by time of day."""
        self.scenario = Scenario.parse(scenario) if isinstance(scenario, str) else scenario

    def _resolve_scenario(self, now: datetime) -> Scenario:
        if self.scenario is not None:
            return self.scenario
        return pick_auto_scenario(now.astimezone(ZoneInfo(self.settings.timezone)), self.rng)

    # --- one cycle -----------------------------------------------------
    def run_cycle(self, db: Session) -> CycleResult:
        """Generate one round of data. The caller commits (see session_scope)."""
        roads = list(list_roads(db))
        if not roads:
            raise SimulationError("The road network is empty. Run the seed command first.")
        now = self.clock()
        scenario = self._resolve_scenario(now)
        profile = PROFILES[scenario]

        count = self.rng.randint(*profile.affected_count)
        affected = self.rng.sample(roads, min(count, len(roads))) if count else []

        conditions = self.generate_traffic_conditions(db, roads, affected, scenario, now)
        created, resolved = self.generate_incidents(db, affected, scenario, now)
        # (Slice 5 will evaluate the alert rules here, as in sequence diagram SD-8.)
        return CycleResult(scenario, now, len(conditions), created, resolved)

    def generate_traffic_conditions(
        self, db: Session, roads: List[Road], affected: List[Road], scenario: Scenario, now: datetime
    ) -> List[TrafficCondition]:
        profile = PROFILES[scenario]
        affected_ids = {r.id for r in affected}
        conditions = []
        for road in roads:
            low, high = profile.affected_delay if road.id in affected_ids else profile.base_delay
            delay = self.rng.randint(low, high)
            conditions.append(
                TrafficCondition(
                    road_id=road.id,
                    level=classify_delay(delay, self.settings),
                    delay_minutes=delay,
                    average_speed_kmh=speed_for_delay(road.length_km, delay, self.settings.free_flow_speed_kmh),
                    recorded_at=now,
                    is_simulated=True,
                )
            )
        traffic_repo.add_many(db, conditions)
        return conditions

    def generate_incidents(self, db: Session, affected: List[Road], scenario: Scenario, now: datetime):
        """Create simulated incidents for incident scenarios; clear them otherwise.

        Returns (created, resolved). A road never has two active simulated incidents.
        """
        profile = PROFILES[scenario]
        created = resolved = 0
        if not profile.incident_types:
            for incident in incident_repo.find_active_simulated(db):
                incident.status = IncidentStatus.RESOLVED
                resolved += 1
            db.flush()
            return created, resolved
        for road in affected:
            if incident_repo.find_active_simulated(db, road.id):
                continue
            kind = self.rng.choice(profile.incident_types)
            incident_repo.add(
                db,
                Incident(
                    type=kind,
                    description=_DESCRIPTIONS[kind].format(road=road.name),
                    status=IncidentStatus.VERIFIED,
                    reported_at=now,
                    verified_at=now,
                    is_simulated=True,
                    road_id=road.id,
                ),
            )
            created += 1
        return created, resolved
