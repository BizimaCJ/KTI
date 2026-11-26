"""Application settings.

Every value can be overridden with an environment variable that starts with
KTI_ (for example KTI_DATABASE_URL) or with a .env file in the project root.
Thresholds come from SRS section 4.3 and are defaults that may be tuned after
user testing, so they live here and not inside the business logic.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="KTI_", extra="ignore")

    database_url: str = "postgresql+psycopg://kti:kti_dev_password@localhost:5432/kti"
    timezone: str = "Africa/Kigali"

    # Traffic levels: upper bound (minutes of extra delay) of each level.
    # Anything above heavy_max_delay is BLOCKED.
    free_flow_max_delay: int = 2
    moderate_max_delay: int = 7
    heavy_max_delay: int = 15

    # Used by the alert rules in a later slice.
    alert_delay_threshold: int = 10
    session_timeout_minutes: int = 15

    # Simulation
    free_flow_speed_kmh: float = 30.0
    simulation_autorun: bool = False
    simulation_scenario: str = "auto"
    simulation_interval_seconds: int = 60


@lru_cache
def get_settings() -> Settings:
    return Settings()
