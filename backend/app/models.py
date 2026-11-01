from datetime import datetime

from sqlalchemy import (
    JSON, Boolean, CheckConstraint, DateTime, Float, ForeignKey, Index, Integer,
    String, UniqueConstraint, text,
)
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base, utcnow


class Intersection(Base):
    __tablename__ = "intersecciones"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    timezone: Mapped[str] = mapped_column(String(50), default="America/Mexico_City")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    config_version: Mapped[int] = mapped_column(default=1)
    plan_version: Mapped[int] = mapped_column(default=0)
    state: Mapped[dict] = mapped_column(JSON, default=dict)
    __table_args__ = (CheckConstraint("latitude BETWEEN -90 AND 90"),
                      CheckConstraint("longitude BETWEEN -180 AND 180"))


class Group(Base):
    __tablename__ = "grupos_movimiento"
    id: Mapped[int] = mapped_column(primary_key=True)
    intersection_id: Mapped[int] = mapped_column(ForeignKey("intersecciones.id"))
    code: Mapped[str] = mapped_column(String(10))
    lanes: Mapped[int] = mapped_column(default=1)
    discharge_vps: Mapped[float] = mapped_column(Float, default=0.5)
    __table_args__ = (UniqueConstraint("intersection_id", "code"),
                      CheckConstraint("code IN ('NS','EO','PEATON')"),
                      CheckConstraint("lanes > 0 AND discharge_vps > 0"))


class Light(Base):
    __tablename__ = "semaforos"
    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("grupos_movimiento.id"))
    head: Mapped[str] = mapped_column(String(80), unique=True)
    operational: Mapped[bool] = mapped_column(default=True)


class TrafficRecord(Base):
    __tablename__ = "registros_trafico"
    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("grupos_movimiento.id"))
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    arrivals: Mapped[int | None] = mapped_column(Integer, nullable=True)
    speed_kmh: Mapped[float | None] = mapped_column(Float, nullable=True)
    weather: Mapped[str | None] = mapped_column(String(12), nullable=True)
    source: Mapped[str] = mapped_column(String(40))
    external_id: Mapped[str | None] = mapped_column(String(160), nullable=True)
    quality: Mapped[str] = mapped_column(String(16), default="valid")
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (
        UniqueConstraint("source", "group_id", "window_start", "window_end"),
        CheckConstraint("arrivals IS NULL OR arrivals BETWEEN 0 AND 300"),
        CheckConstraint("speed_kmh IS NULL OR speed_kmh BETWEEN 0 AND 150"),
        CheckConstraint("window_end > window_start"),
        Index("ix_traffic_group_time", "group_id", "window_end"),
    )


class User(Base):
    __tablename__ = "usuarios"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    password_hash: Mapped[str] = mapped_column(String(512))
    role: Mapped[str] = mapped_column(String(16), default="admin")
    active: Mapped[bool] = mapped_column(default=True)


class ModelVersion(Base):
    __tablename__ = "modelos"
    id: Mapped[int] = mapped_column(primary_key=True)
    version: Mapped[str] = mapped_column(String(80), unique=True)
    artifact_hash: Mapped[str] = mapped_column(String(64))
    dataset_hash: Mapped[str] = mapped_column(String(64))
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON)
    status: Mapped[str] = mapped_column(String(20), default="candidate")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Prediction(Base):
    __tablename__ = "predicciones"
    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("grupos_movimiento.id"))
    model_id: Mapped[int] = mapped_column(ForeignKey("modelos.id"))
    decision_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    horizon_min: Mapped[int] = mapped_column(default=5)
    flow_vpm: Mapped[float] = mapped_column(Float)
    inputs: Mapped[dict] = mapped_column(JSON)
    __table_args__ = (CheckConstraint("flow_vpm >= 0 AND horizon_min = 5"),)


class Plan(Base):
    __tablename__ = "planes_semaforicos"
    id: Mapped[int] = mapped_column(primary_key=True)
    intersection_id: Mapped[int] = mapped_column(ForeignKey("intersecciones.id"))
    user_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"), nullable=True)
    previous_version: Mapped[int] = mapped_column(Integer)
    target_cycle: Mapped[int] = mapped_column(Integer)
    mode: Mapped[str] = mapped_column(String(16))
    reason: Mapped[str] = mapped_column(String(300))
    status: Mapped[str] = mapped_column(String(16), default="PROPOSED")
    expires_cycle: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    __table_args__ = (
        CheckConstraint("mode IN ('automatic','manual','degraded','fixed')"),
        CheckConstraint("status IN ('PROPOSED','PENDING','ACTIVE','SUPERSEDED','CANCELLED')"),
        Index("uq_active_plan", "intersection_id", unique=True,
              postgresql_where=text("status = 'ACTIVE'"), sqlite_where=text("status = 'ACTIVE'")),
        Index("uq_pending_plan", "intersection_id", unique=True,
              postgresql_where=text("status = 'PENDING'"), sqlite_where=text("status = 'PENDING'")),
    )


class PlanDetail(Base):
    __tablename__ = "detalles_plan"
    plan_id: Mapped[int] = mapped_column(ForeignKey("planes_semaforicos.id"), primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("grupos_movimiento.id"), primary_key=True)
    order: Mapped[int] = mapped_column(Integer)
    green_s: Mapped[int] = mapped_column(Integer)
    yellow_s: Mapped[int] = mapped_column(Integer)
    clearance_s: Mapped[int] = mapped_column(Integer)
    __table_args__ = (CheckConstraint("green_s >= 0 AND yellow_s >= 0 AND clearance_s >= 0"),)


class PlanPrediction(Base):
    __tablename__ = "plan_prediccion"
    plan_id: Mapped[int] = mapped_column(ForeignKey("planes_semaforicos.id"), primary_key=True)
    prediction_id: Mapped[int] = mapped_column(ForeignKey("predicciones.id"), primary_key=True)


class Audit(Base):
    __tablename__ = "auditoria"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"), nullable=True)
    actor: Mapped[str] = mapped_column(String(80))
    action: Mapped[str] = mapped_column(String(50))
    entity: Mapped[str] = mapped_column(String(80))
    before: Mapped[dict] = mapped_column(JSON, default=dict)
    after: Mapped[dict] = mapped_column(JSON, default=dict)
    reason: Mapped[str] = mapped_column(String(300))
    correlation_id: Mapped[str] = mapped_column(String(80), index=True)
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Experiment(Base):
    __tablename__ = "experimentos"
    id: Mapped[int] = mapped_column(primary_key=True)
    model_id: Mapped[int | None] = mapped_column(ForeignKey("modelos.id"), nullable=True)
    configuration: Mapped[dict] = mapped_column(JSON)
    metrics: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class WorkerLease(Base):
    __tablename__ = "control_worker"
    id: Mapped[int] = mapped_column(primary_key=True)
    owner: Mapped[str] = mapped_column(String(80))
    heartbeat: Mapped[datetime] = mapped_column(DateTime(timezone=True))
