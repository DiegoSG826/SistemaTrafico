"""Lecturas de tramos viales del entorno de Metro Cuauhtémoc."""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from time import monotonic
from typing import Literal

import httpx
from pydantic import AliasPath, BaseModel, Field, SecretStr

from .database import utcnow

FLOW_URL = "https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/17/json"


class Coordinate(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


PILOT_NAME = "Entorno de Metro Cuauhtémoc"
PILOT_CENTER = Coordinate(latitude=19.42568, longitude=-99.15462)
QUERY_POINTS = (
    ("Av. Chapultepec · poniente", Coordinate(latitude=19.42541, longitude=-99.15555)),
    ("Acceso sur", Coordinate(latitude=19.42450, longitude=-99.15500)),
)


class SegmentFlow(BaseModel):
    speed_kmh: int = Field(validation_alias="currentSpeed", ge=0)
    free_flow_speed_kmh: int = Field(validation_alias="freeFlowSpeed", ge=0)
    travel_time_s: int = Field(validation_alias="currentTravelTime", ge=0)
    free_flow_travel_time_s: int = Field(validation_alias="freeFlowTravelTime", ge=0)
    confidence: float = Field(ge=0, le=1)
    closed: bool = Field(validation_alias="roadClosure")
    geometry: list[Coordinate] = Field(
        validation_alias=AliasPath("coordinates", "coordinate"), min_length=2,
    )


class LiveSegment(BaseModel):
    label: str
    point: Coordinate
    status: Literal["current", "stale", "unavailable"]
    retrieved_at: datetime | None = None
    flow: SegmentFlow | None = None


class LiveTrafficSnapshot(BaseModel):
    source: Literal["tomtom"] = "tomtom"
    location: str
    center: Coordinate
    configured: bool
    segments: list[LiveSegment]


@dataclass(frozen=True)
class CachedFlow:
    flow: SegmentFlow
    retrieved_at: datetime
    retrieved_monotonic: float


class TomTomTransport(httpx.AsyncHTTPTransport):
    def __init__(self, api_key: SecretStr):
        super().__init__()
        self.api_key = api_key

    async def handle_async_request(self, request):
        # HTTPX registra la URL original a nivel INFO. Añadir la clave solo para el envío.
        outbound = httpx.Request(
            request.method, request.url.copy_set_param("key", self.api_key.get_secret_value()),
            headers=request.headers, stream=request.stream, extensions=request.extensions,
        )
        return await super().handle_async_request(outbound)


async def fetch_flow(client: httpx.AsyncClient, point: Coordinate) -> CachedFlow | None:
    try:
        async with asyncio.timeout(3):
            response = await client.get(FLOW_URL, params={
                "point": f"{point.latitude},{point.longitude}", "unit": "kmph",
            })
        response.raise_for_status()
        flow = SegmentFlow.model_validate(response.json()["flowSegmentData"])
    except (TimeoutError, httpx.HTTPError, ValueError, KeyError, TypeError):
        return None
    return CachedFlow(flow, utcnow(), monotonic())


class TomTomTraffic:
    def __init__(self, api_key: SecretStr, refresh_seconds: int):
        key = api_key.get_secret_value().strip()
        self.api_key = SecretStr(key)
        self.refresh_seconds = refresh_seconds
        self.configured = bool(key)
        self.lock = asyncio.Lock()
        self.next_refresh = 0.0
        self.last_success: dict[str, CachedFlow] = {}
        self.current: set[str] = set()

    async def snapshot(self) -> LiveTrafficSnapshot:
        async with self.lock:
            if self.configured and monotonic() >= self.next_refresh:
                async with httpx.AsyncClient(transport=TomTomTransport(self.api_key),
                                             trust_env=False) as client:
                    results = await asyncio.gather(*(fetch_flow(client, point)
                                                     for _, point in QUERY_POINTS))
                self.current.clear()
                for (label, _), reading in zip(QUERY_POINTS, results, strict=True):
                    if reading is not None:
                        self.current.add(label)
                        self.last_success[label] = reading
                self.next_refresh = monotonic() + self.refresh_seconds

            segments = []
            for label, point in QUERY_POINTS:
                reading = self.last_success.get(label)
                if reading is None or monotonic() - reading.retrieved_monotonic > 3 * self.refresh_seconds:
                    self.last_success.pop(label, None)
                    segments.append(LiveSegment(label=label, point=point, status="unavailable"))
                else:
                    segments.append(LiveSegment(
                        label=label, point=point, status="current" if label in self.current else "stale",
                        retrieved_at=reading.retrieved_at, flow=reading.flow,
                    ))
        return LiveTrafficSnapshot(location=PILOT_NAME, center=PILOT_CENTER,
                                   configured=self.configured, segments=segments)
