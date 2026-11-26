import random
from datetime import datetime, timezone

from sqlalchemy.exc import OperationalError

from app.config import Settings
from app.database import get_db
from app.modules.simulation.generator import SimulatedDataGenerator


def run(db, scenario, seed=3):
    gen = SimulatedDataGenerator(scenario, rng=random.Random(seed), settings=Settings(),
                                 clock=lambda: datetime.now(timezone.utc))
    gen.run_cycle(db)
    db.commit()


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_overview_when_empty(client):
    body = client.get("/api/overview").json()
    assert body["has_data"] is False
    assert body["roads"] == [] and body["incidents"] == []
    assert body["worst_level"] is None


def test_overview_with_data(client, seeded_db):
    run(seeded_db, "flooding")
    body = client.get("/api/overview").json()
    assert body["has_data"] is True and body["simulated"] is True
    assert len(body["roads"]) == 3
    assert body["worst_level"] == "BLOCKED"
    assert {"road_name", "level", "delay_minutes", "average_speed_kmh", "recorded_at", "is_simulated"} <= set(body["roads"][0])
    assert len(body["incidents"]) >= 1


def test_overview_returns_only_latest_reading_per_road(client, seeded_db):
    run(seeded_db, "normal", 1)
    run(seeded_db, "peak_hour", 2)
    assert len(client.get("/api/overview").json()["roads"]) == 3
    assert len(client.get("/api/traffic/conditions").json()) == 3


def test_public_incident_payload_hides_private_fields(client, seeded_db):
    run(seeded_db, "incident")
    incident = client.get("/api/incidents").json()[0]
    assert "reporter_name" not in incident and "reporter_contact" not in incident
    assert "rejection_reason" not in incident


def test_roads_endpoint(client, seeded_db):
    roads = client.get("/api/network/roads").json()
    assert len(roads) == 3
    assert roads[0]["start_intersection"] == "Nyabugogo Terminal"


def test_database_down_gives_friendly_503(engine):
    from fastapi.testclient import TestClient
    from app.main import create_app

    class BrokenSession:
        def __getattr__(self, name):
            raise OperationalError("SELECT", {}, Exception("database is down"))

    def broken_db():
        yield BrokenSession()

    app = create_app()
    app.dependency_overrides[get_db] = broken_db
    response = TestClient(app).get("/api/overview")
    assert response.status_code == 503
    assert "temporarily unavailable" in response.json()["detail"]


def test_home_page_is_served_with_simulated_label(client):
    page = client.get("/")
    assert page.status_code == 200
    assert "Simulated data" in page.text
    assert client.get("/js/main.js").status_code == 200
