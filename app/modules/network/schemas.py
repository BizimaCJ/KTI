from pydantic import BaseModel

from app.modules.network.models import Road


class RoadOut(BaseModel):
    id: int
    name: str
    length_km: float
    start_intersection: str
    end_intersection: str

    @classmethod
    def from_road(cls, road: Road) -> "RoadOut":
        return cls(
            id=road.id,
            name=road.name,
            length_km=road.length_km,
            start_intersection=road.start_intersection.name,
            end_intersection=road.end_intersection.name,
        )
