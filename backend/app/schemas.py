from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=160)]
Reason = Annotated[str, StringConstraints(strip_whitespace=True, min_length=5, max_length=300)]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class Login(Strict):
    email: str = Field(max_length=254)
    password: str = Field(max_length=256)


class IntersectionInput(Strict):
    name: Name
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    lanes: int = Field(default=1, ge=1, le=6)
    discharge_vps: float = Field(default=0.5, gt=0, le=2)


class IntersectionEdit(IntersectionInput):
    config_version: int = Field(ge=1)
    active: bool = True


class Observation(Strict):
    group_id: int = Field(gt=0)
    window_start: datetime
    window_end: datetime
    arrivals: int | None = Field(default=None, ge=0, le=300, strict=True)
    speed_kmh: float | None = Field(default=None, ge=0, le=150)
    weather: Literal["clear", "rain", "heavy_rain"] | None = None
    source: Literal["synthetic", "waze", "test"] = "synthetic"
    external_id: str | None = Field(default=None, max_length=160)

    @model_validator(mode="after")
    def window(self):
        if self.window_start.utcoffset() is None or self.window_end.utcoffset() is None:
            raise ValueError("Las fechas requieren zona horaria")
        if (self.window_end-self.window_start).total_seconds() != 60:
            raise ValueError("La ventana debe durar 60 segundos")
        if self.window_start.second or self.window_start.microsecond:
            raise ValueError("Ventanas alineadas al minuto")
        if self.source == "waze" and self.arrivals is not None:
            raise ValueError("El adaptador Waze no proporciona conteos por acceso")
        if self.source != "waze" and self.weather is None:
            raise ValueError("Clima requerido para el generador sintético")
        return self


class PredictionRequest(Strict):
    intersection_id: int = Field(gt=0)
    previous_version: int = Field(ge=0)


class ApplyRequest(Strict):
    previous_version: int = Field(ge=0)
    target_cycle: int = Field(ge=0)


class ManualRequest(PredictionRequest):
    green_ns: int = Field(ge=20, le=60, strict=True)
    green_eo: int = Field(ge=20, le=60, strict=True)
    reason: Reason
    duration_cycles: int = Field(ge=1, le=10)
