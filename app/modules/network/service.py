"""Road network rules and seed data for the Nyabugogo prototype area."""
from dataclasses import dataclass
from typing import Sequence

from sqlalchemy.orm import Session

from app.modules.network import repository
from app.modules.network.models import Intersection, NodeType, Road

# PLACEHOLDERS: rename "Junction A" and "Junction B" to the two real intersections
# and fill in latitude/longitude when you have them (edit the rows in the database
# or change this list before running `seed` on a fresh database).
SEED_INTERSECTIONS = [
    ("Nyabugogo Terminal", NodeType.TERMINAL),
    ("Junction A", NodeType.JUNCTION),
    ("Junction B", NodeType.JUNCTION),
]
# (road name, length in km, start intersection, end intersection)
SEED_ROADS = [
    ("Terminal to Junction A", 0.8, "Nyabugogo Terminal", "Junction A"),
    ("Junction A to Junction B", 0.7, "Junction A", "Junction B"),
    ("Terminal to Junction B", 0.9, "Nyabugogo Terminal", "Junction B"),
]


@dataclass
class SeedResult:
    intersections_created: int = 0
    roads_created: int = 0


def list_roads(db: Session) -> Sequence[Road]:
    return repository.list_roads(db)


def seed_network(db: Session) -> SeedResult:
    """Create the prototype network. Safe to run more than once."""
    result = SeedResult()
    for name, node_type in SEED_INTERSECTIONS:
        if repository.get_intersection_by_name(db, name) is None:
            repository.add(db, Intersection(name=name, node_type=node_type))
            result.intersections_created += 1
    for name, length_km, start_name, end_name in SEED_ROADS:
        if repository.get_road_by_name(db, name) is None:
            start = repository.get_intersection_by_name(db, start_name)
            end = repository.get_intersection_by_name(db, end_name)
            repository.add(
                db,
                Road(
                    name=name,
                    length_km=length_km,
                    start_intersection_id=start.id,
                    end_intersection_id=end.id,
                ),
            )
            result.roads_created += 1
    return result
