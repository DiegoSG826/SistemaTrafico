"""Consulta de tráfico actual para el visor, sin ingesta de observaciones."""

from collections import deque
from dataclasses import dataclass
from datetime import datetime
from email.utils import parsedate_to_datetime
from math import ceil
from threading import Lock
from time import monotonic
from typing import Literal

import httpx
from pydantic import AliasPath, BaseModel, ConfigDict, Field

from .database import utcnow

FLOW_URL = "https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/17/json"
SAMPLE_TTL_S = 120
RETRY_FALLBACK_S = 300
DAY_S = 86_400


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


@dataclass(frozen=True)
class FlowFailure:
    status_code: int
    detail: str
    retry_after: int | None = None


class PointDelay(BaseModel):
    intersection_id: int
    status: Literal["available", "closed", "no_reference", "unavailable"]
    delay_s: int | None = None
    increase_pct: float | None = None
    confidence: float | None = None
    fetched_at: datetime | None = None
    detail: str | None = None

    @classmethod
    def from_reading(cls, identifier: int, reading: TomTomFlow | FlowFailure) -> "PointDelay":
        if isinstance(reading, FlowFailure):
            return cls(intersection_id=identifier, status="unavailable", detail=reading.detail)
        metadata = {"intersection_id": identifier, "confidence": reading.confidence,
                    "fetched_at": reading.fetched_at}
        if reading.road_closed:
            return cls(status="closed", **metadata)
        baseline = reading.free_flow_travel_time_s
        if baseline == 0:
            return cls(status="no_reference", **metadata)
        delay = max(0, reading.current_travel_time_s - baseline)
        return cls(status="available", delay_s=delay, increase_pct=round(100 * delay / baseline, 1),
                   **metadata)


def retry_after_seconds(value: str | None) -> int:
    if value:
        try:
            return max(1, int(value))
        except ValueError:
            try:
                date = parsedate_to_datetime(value)
                return max(1, ceil((date - utcnow()).total_seconds()))
            except (ValueError, TypeError, OverflowError):
                pass
    return RETRY_FALLBACK_S


class TomTomReader:
    """Comparte lecturas recientes y el presupuesto entre peticiones del backend."""

    def __init__(self, key: str, daily_budget: int):
        self.key = key
        self.daily_budget = daily_budget
        self._lock = Lock()
        self._readings: dict[tuple[float, float], tuple[float, TomTomFlow | FlowFailure]] = {}
        self._requests: deque[float] = deque()
        self._paused_until = 0.0
        self._pause_reason = ""

    def get(self, latitude: float, longitude: float) -> TomTomFlow | FlowFailure:
        # Una llamada en curso permite reutilizar su resultado y detener el lote ante un 429.
        with self._lock:
            now = monotonic()
            self._readings = {point: entry for point, entry in self._readings.items() if entry[0] > now}
            point = (latitude, longitude)
            if point in self._readings:
                return self._readings[point][1]
            if now < self._paused_until:
                return FlowFailure(503, self._pause_reason, ceil(self._paused_until - now))
            while self._requests and self._requests[0] <= now - DAY_S:
                self._requests.popleft()
            if len(self._requests) >= self.daily_budget:
                return FlowFailure(503, "Se alcanzó el presupuesto diario de consultas TomTom.",
                                   ceil(self._requests[0] + DAY_S - now))

            self._requests.append(now)
            try:
                reading = fetch_flow(self.key, *point)
            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                if status in (401, 403, 429):
                    seconds = retry_after_seconds(exc.response.headers.get("Retry-After"))
                    self._paused_until = monotonic() + seconds
                    self._pause_reason = ("TomTom alcanzó el límite de consultas. Intenta más tarde."
                                          if status == 429 else
                                          "TomTom rechazó la clave. Verifica el acceso a Traffic API.")
                    return FlowFailure(503, self._pause_reason, seconds)
                detail = ("TomTom no encontró un tramo con datos cerca de este punto." if status == 404
                          else "TomTom no pudo entregar datos para este punto.")
                reading = FlowFailure(502, detail)
            except httpx.RequestError:
                reading = FlowFailure(502, "Sin comunicación con TomTom. Intenta más tarde.")
            except (ValueError, KeyError, TypeError):
                reading = FlowFailure(502, "TomTom devolvió datos incompletos o inválidos para este punto.")

            ttl = 30 if isinstance(reading, FlowFailure) else SAMPLE_TTL_S
            self._readings[point] = (monotonic() + ttl, reading)
            return reading
