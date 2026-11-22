"""Consulta de tráfico actual para el visor, sin ingesta de observaciones."""

from datetime import datetime
from typing import Literal

import httpx
from pydantic import AliasPath, BaseModel, ConfigDict, Field

from .database import utcnow

FLOW_URL = "https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/17/json"


class Coordinate(BaseModel):
    model_config = ConfigDict(strict=True)

    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class TomTomFlow(BaseModel):
    model_config = ConfigDict(strict=True)

    source: Literal["tomtom"] = "tomtom"
    fetched_at: datetime = Field(default_factory=utcnow)
    current_speed_kmh: int = Field(ge=0, validation_alias="currentSpeed")
    free_flow_speed_kmh: int = Field(ge=0, validation_alias="freeFlowSpeed")
    current_travel_time_s: int = Field(ge=0, validation_alias="currentTravelTime")
    free_flow_travel_time_s: int = Field(ge=0, validation_alias="freeFlowTravelTime")
    confidence: float = Field(ge=0, le=1)
    road_closed: bool = Field(validation_alias="roadClosure")
    geometry: list[Coordinate] = Field(min_length=2, validation_alias=AliasPath("coordinates", "coordinate"))


def fetch_flow(key: str, latitude: float, longitude: float) -> TomTomFlow:
    response = httpx.get(FLOW_URL, params={"key": key, "point": f"{latitude},{longitude}",
                                          "unit": "kmph"}, timeout=httpx.Timeout(3, connect=2))
    response.raise_for_status()
    return TomTomFlow.model_validate(response.json()["flowSegmentData"])
