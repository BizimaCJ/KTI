from app.modules.network import service
from app.modules.network.models import NodeType


def test_seed_creates_network(db):
    result = service.seed_network(db)
    assert (result.intersections_created, result.roads_created) == (3, 3)
    roads = service.list_roads(db)
    assert len(roads) == 3
    terminal = [r for r in roads if r.start_intersection.node_type == NodeType.TERMINAL]
    assert len(terminal) == 2  # two roads start at the terminal


def test_seed_is_idempotent(db):
    service.seed_network(db)
    again = service.seed_network(db)
    assert (again.intersections_created, again.roads_created) == (0, 0)
    assert len(service.list_roads(db)) == 3
