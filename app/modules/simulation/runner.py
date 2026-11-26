"""Runs the generator on a schedule (FR 21: periodic generation)."""
import logging
import threading
from typing import Callable, Optional

from sqlalchemy.orm import Session

from app.database import session_scope
from app.modules.simulation.generator import SimulatedDataGenerator

log = logging.getLogger("kti.simulation")


class BackgroundSimulation:
    """Runs the generator in a background thread until stop() is called."""

    def __init__(self, generator: SimulatedDataGenerator, session_factory: Optional[Callable[[], Session]] = None):
        self._generator = generator
        self._factory = session_factory
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, name="kti-simulation", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5)

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                with session_scope(self._factory) as db:
                    result = self._generator.run_cycle(db)
                log.info("Simulation cycle: %s, %d conditions, %d incidents created, %d resolved",
                         result.scenario.value, result.conditions_created,
                         result.incidents_created, result.incidents_resolved)
            except Exception:  # keep running; the next cycle may succeed
                log.exception("Simulation cycle failed")
            self._stop.wait(self._generator.refresh_interval_seconds)
