"""Application entry point: `uvicorn app.main:app --reload`."""
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from fastapi import Depends

from app.config import get_settings
from app.database import get_db
from app.modules.incidents.router import router as incidents_router
from app.modules.network.router import router as network_router
from app.modules.overview.router import router as overview_router
from app.modules.simulation.generator import SimulatedDataGenerator
from app.modules.simulation.runner import BackgroundSimulation
from app.modules.traffic.router import router as traffic_router

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger("kti")
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    simulation = None
    if settings.simulation_autorun:
        simulation = BackgroundSimulation(SimulatedDataGenerator(settings.simulation_scenario))
        simulation.start()
        log.info("Background simulation started (%s)", settings.simulation_scenario)
    yield
    if simulation:
        simulation.stop()


def create_app() -> FastAPI:
    app = FastAPI(title="Kigali Traffic Insight", version="0.1.0", lifespan=lifespan)

    @app.exception_handler(OperationalError)
    async def database_unavailable(request: Request, exc: OperationalError):
        log.error("Database unavailable: %s", exc)
        return JSONResponse(
            status_code=503,
            content={"detail": "Traffic data is temporarily unavailable. Please try again shortly."},
        )

    @app.get("/api/health", tags=["health"])
    def health(db: Session = Depends(get_db)):
        db.execute(text("SELECT 1"))
        return {"status": "ok"}

    app.include_router(network_router)
    app.include_router(traffic_router)
    app.include_router(incidents_router)
    app.include_router(overview_router)

    if FRONTEND_DIR.exists():  # mounted last so it never hides /api routes
        app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
    return app


app = create_app()
