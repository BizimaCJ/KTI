# Kigali Traffic Insight

FastAPI + PostgreSQL + frontend. Prototype with simulated data for Nyabugogo terminal
and two nearby intersections.

## What works now
- Road network (intersections and roads) with seed data
- Traffic conditions with the four traffic levels from the SRS (Free flow, Moderate, Heavy, Blocked)
- Simulated data generator with scenarios: normal, peak_hour, incident, flooding, auto
- Public traffic overview page: traffic levels, delay, speed, active (Verified) incidents,
  simulated-data label, auto refresh every 30 s, friendly errors, works from 360 px wide
- API: `GET /api/overview`, `/api/traffic/conditions`, `/api/incidents`, `/api/network/roads`, `/api/health`
  (interactive docs at `/docs`)

SRS coverage: FR 1, FR 2 (read side), FR 20, FR 21, NFR 4, NFR 12.

## Setup on Ubuntu
```bash
sudo apt update
sudo apt install -y postgresql python3-venv

sudo -u postgres psql -c "CREATE USER kti WITH PASSWORD 'kti_dev_password';"
sudo -u postgres psql -c "CREATE DATABASE kti OWNER kti;"

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # edit the password if you changed it above

python -m app.cli init-db       # create tables
python -m app.cli seed          # add roads and intersections
python -m app.cli simulate --scenario peak_hour   # generate one round of data

uvicorn app.main:app --reload   # open http://localhost:8000
```

Keep data changing while you demo (pick one):
```bash
python -m app.cli simulate --scenario auto --loop --interval 30      # separate terminal
KTI_SIMULATION_AUTORUN=true uvicorn app.main:app --reload            # inside the web app
```
Scenarios: `normal`, `peak_hour`, `incident`, `flooding`, `auto` (picks by Kigali time of day,
small chance of an incident or flooding).

## Tests
```bash
pytest                                  # uses in-memory SQLite, no setup needed
sudo -u postgres psql -c "CREATE DATABASE kti_test OWNER kti;"
KTI_TEST_DATABASE_URL=postgresql+psycopg://kti:kti_dev_password@localhost:5432/kti_test pytest
```

## Structure
```
app/
  main.py, config.py, database.py, models.py, cli.py
  modules/
    network/      models, repository, service, schemas, router   (roads, intersections, seed)
    traffic/      models, levels, repository, service, schemas, router
    incidents/    models, status, repository, service, schemas, router  (read side only so far)
    simulation/   scenarios, generator, runner
    overview/     service, schemas, router                        (combines traffic + incidents)
frontend/         index.html, css/, js/ (api, dom, format, render, main)
tests/
```
Rule of thumb: `router` handles HTTP only, `service` holds business rules, `repository` is the only
code that talks to the database.

## Notes
- "Junction A" and "Junction B" are placeholders. Rename them (and add latitude/longitude) once you
  have the two real intersections.
- Thresholds (delay ranges, alert threshold) are in `.env` / `app/config.py`.
- Tables are created with `init-db`. Alembic migrations will be added before the schema changes
  (slice 4: administrators, audit log).
- Change the database password before using this anywhere other than your own computer.
