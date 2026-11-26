"""Imports every model so Base.metadata knows all tables (used by init-db and tests)."""
from app.modules.incidents.models import Incident, IncidentStatus, IncidentType  # noqa: F401
from app.modules.network.models import Intersection, NodeType, Road  # noqa: F401
from app.modules.traffic.models import TrafficCondition, TrafficLevel  # noqa: F401
