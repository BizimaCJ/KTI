import random
from datetime import datetime, timedelta, timezone

import pytest

from app.config import Settings
from app.modules.incidents import service as incident_service
from app.modules.incidents.models import Incident, IncidentStatus
from app.modules.simulation.generator import SimulatedDataGenerator

REPORT = {"type": "CRASH", "road_id": 1, "description": "Two cars collided near the terminal gate."}


def run(db, scenario, seed=1):
    gen = SimulatedDataGenerator(scenario, rng=random.Random(seed), settings=Settings(),
                                 clock=lambda: datetime.now(timezone.utc))
    gen.run_cycle(db)
    db.commit()


# ---- incident reporting (FR 3) ----

def test_report_is_saved_as_submitted_with_reference(client, seeded_db):
    response = client.post("/api/incidents/report", json=REPORT)
    assert response.status_code == 201
    body = response.json()
    assert body["reference"].startswith("KTI-") and body["status"] == "SUBMITTED"
    saved = seeded_db.query(Incident).one()
    assert saved.status == IncidentStatus.SUBMITTED and saved.is_simulated is False


def test_submitted_report_is_not_public_until_verified(client, seeded_db):
    client.post("/api/incidents/report", json=REPORT)
    assert client.get("/api/incidents").json() == []


def test_report_with_optional_contact_details(client, seeded_db):
    payload = {**REPORT, "reporter_name": "  Aline ", "reporter_contact": "0780000000"}
    assert client.post("/api/incidents/report", json=payload).status_code == 201
    assert seeded_db.query(Incident).one().reporter_name == "Aline"


@pytest.mark.parametrize(
    "change",
    [{"description": "short"}, {"description": "   "}, {"type": "ALIEN"}, {"road_id": "x"},
     {"description": "x" * 501}],
)
def test_invalid_reports_are_rejected(client, seeded_db, change):
    assert client.post("/api/incidents/report", json={**REPORT, **change}).status_code == 422
    assert seeded_db.query(Incident).count() == 0


def test_unknown_road_is_rejected(client, seeded_db):
    response = client.post("/api/incidents/report", json={**REPORT, "road_id": 999})
    assert response.status_code == 422
    assert "listed roads" in response.json()["detail"]


def test_duplicate_report_is_refused(client, seeded_db):
    assert client.post("/api/incidents/report", json=REPORT).status_code == 201
    assert client.post("/api/incidents/report", json=REPORT).status_code == 409
    assert seeded_db.query(Incident).count() == 1


def test_same_type_on_another_road_is_not_a_duplicate(client, seeded_db):
    client.post("/api/incidents/report", json=REPORT)
    assert client.post("/api/incidents/report", json={**REPORT, "road_id": 2}).status_code == 201


def test_old_report_is_not_a_duplicate(seeded_db):
    from app.modules.incidents.schemas import IncidentReportIn
    data = IncidentReportIn(**REPORT)
    long_ago = datetime.now(timezone.utc) - timedelta(hours=2)
    incident_service.submit_report(seeded_db, data, now=long_ago)
    seeded_db.commit()
    incident_service.submit_report(seeded_db, data)  # no error


# ---- status changes used by the demo helper ----

def test_verified_report_becomes_public(client, seeded_db):
    client.post("/api/incidents/report", json=REPORT)
    incident_service.change_status(seeded_db, 1, IncidentStatus.UNDER_REVIEW)
    incident_service.change_status(seeded_db, 1, IncidentStatus.VERIFIED)
    seeded_db.commit()
    public = client.get("/api/incidents").json()
    assert len(public) == 1 and public[0]["is_simulated"] is False


def test_status_cannot_skip_review(client, seeded_db):
    client.post("/api/incidents/report", json=REPORT)
    with pytest.raises(incident_service.StatusChangeNotAllowed):
        incident_service.change_status(seeded_db, 1, IncidentStatus.VERIFIED)


def test_unknown_incident(seeded_db):
    with pytest.raises(incident_service.IncidentNotFound):
        incident_service.change_status(seeded_db, 42, IncidentStatus.UNDER_REVIEW)


# ---- historical traffic (FR 10) ----

def test_history_returns_stored_readings_newest_first(client, seeded_db):
    run(seeded_db, "normal", 1)
    run(seeded_db, "peak_hour", 2)
    rows = client.get("/api/traffic/history", params={"road_id": 1, "hours": 6}).json()
    assert len(rows) == 2
    assert rows[0]["recorded_at"] >= rows[1]["recorded_at"]
    assert all(r["road_id"] == 1 and r["is_simulated"] is True for r in rows)


def test_history_excludes_readings_outside_the_window(client, seeded_db):
    run(seeded_db, "normal")
    assert client.get("/api/traffic/history", params={"road_id": 1, "hours": 1}).json() != []
    from app.modules.traffic import service
    future = datetime.now(timezone.utc) + timedelta(hours=5)
    assert service.get_history(seeded_db, 1, hours=1, now=future) == []


def test_history_with_no_data_is_an_empty_list(client, seeded_db):
    assert client.get("/api/traffic/history", params={"road_id": 1}).json() == []


def test_history_unknown_road(client, seeded_db):
    assert client.get("/api/traffic/history", params={"road_id": 99}).status_code == 404


@pytest.mark.parametrize("hours", [0, 500, "abc"])
def test_history_rejects_bad_hours(client, seeded_db, hours):
    assert client.get("/api/traffic/history", params={"road_id": 1, "hours": hours}).status_code == 422


# ---- pages ----

@pytest.mark.parametrize("page,script", [("/report.html", "/js/report.js"), ("/history.html", "/js/history.js")])
def test_new_pages_are_served_with_simulated_label(client, page, script):
    response = client.get(page)
    assert response.status_code == 200 and "Simulated data" in response.text
    assert client.get(script).status_code == 200
