from datetime import datetime, timedelta
from math import isfinite
from uuid import uuid4

import httpx
from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from ml_model.synthetic import features
from .controller import Timing, suggest
from .database import aware, utcnow
from .models import (Audit, Group, Intersection, ModelVersion, Plan, PlanDetail,
                     PlanPrediction, Prediction, TrafficRecord)


def audit(db, action, entity, reason, before=None, after=None, user=None, correlation=None):
    db.add(Audit(user_id=user.id if user else None, actor=user.email if user else "simulator",
                 action=action, entity=entity, reason=reason, before=before or {}, after=after or {},
                 correlation_id=correlation or str(uuid4())))


def get_intersection(db, identifier):
    item = db.get(Intersection, identifier)
    if item is None:
        raise HTTPException(404, "Intersección desconocida")
    return item


def groups_for(db, identifier):
    return list(db.scalars(select(Group).where(Group.intersection_id == identifier).order_by(Group.id)))


def decision_clock(item):
    return aware(datetime.fromisoformat(item.state["sim_time"])) \
        if item.state.get("sim_time") else utcnow()


def is_live(item):
    value = item.state.get("heartbeat")
    if not value:
        return False
    return (utcnow()-aware(datetime.fromisoformat(value))).total_seconds() <= 5


def latest_features(db, item):
    now = decision_clock(item)
    result, references = [], []
    for group in sorted(groups_for(db, item.id), key=lambda g: g.code, reverse=True):
        if group.code == "PEATON":
            continue
        rows = list(db.scalars(select(TrafficRecord).where(TrafficRecord.group_id == group.id,
            TrafficRecord.window_end <= now).order_by(TrafficRecord.window_end.desc(),
                                                     TrafficRecord.id.desc()).limit(30)))
        unique = {}
        for row in rows:
            unique.setdefault(aware(row.window_end), row)
        rows = list(unique.values())[:5]
        if len(rows) < 5:
            raise ValueError("Faltan cinco observaciones consecutivas por grupo")
        rows.reverse()
        age = (now-aware(rows[-1].window_end)).total_seconds()
        if age > 120 or age < 0:
            raise ValueError("Fuente vencida: antigüedad mayor de 120 s")
        if any(aware(b.window_end)-aware(a.window_end) != timedelta(minutes=1)
               for a, b in zip(rows, rows[1:])):
            raise ValueError("Hay ventanas ausentes")
        if any(r.arrivals is None for r in rows) or rows[-1].speed_kmh is None:
            raise ValueError("Fuente sin conteos o velocidad disponible")
        result.append(features(now, rows[-1].weather, [r.arrivals for r in rows],
                               rows[-1].speed_kmh, item.id, group.code))
        references.append((group, [r.id for r in rows]))
    if len(result) != 2:
        raise ValueError("Se requieren grupos NS y EO")
    # Orden explícito NS, EO para el servicio IA.
    paired = sorted(zip(result, references), key=lambda p: p[1][0].code == "EO")
    return [p[0] for p in paired], [p[1] for p in paired]


def infer_http(url, rows):
    with httpx.Client(timeout=2, trust_env=False) as client:
        response = client.post(f"{url.rstrip('/')}/predict", json={"rows": rows})
        response.raise_for_status()
        return response.json()


def timing_for(db, plan):
    details = list(db.execute(select(PlanDetail, Group).join(Group,
        PlanDetail.group_id == Group.id).where(PlanDetail.plan_id == plan.id)))
    values = {group.code: detail.green_s for detail, group in details}
    if set(values) != {"NS", "EO", "PEATON"} or values["PEATON"] != 20:
        raise ValueError("Plan incompleto")
    for detail, group in details:
        expected = (0, 10) if group.code == "PEATON" else (3, 2)
        if (detail.yellow_s, detail.clearance_s) != expected:
            raise ValueError("Transiciones inválidas")
        if group.intersection_id != plan.intersection_id:
            raise ValueError("Grupo ajeno al cruce")
    return Timing(values["NS"], values["EO"]).validate()


def create_plan(db, item, timing, mode, reason, *, user=None, target=None, expires=None,
                correlation=None):
    timing.validate()
    plan = Plan(intersection_id=item.id, previous_version=item.plan_version,
                target_cycle=target if target is not None else item.state.get("cycle", -1)+1,
                mode=mode, reason=reason, user_id=user.id if user else None, expires_cycle=expires)
    db.add(plan)
    db.flush()
    for group in groups_for(db, item.id):
        ped = group.code == "PEATON"
        db.add(PlanDetail(plan_id=plan.id, group_id=group.id,
                         order={"NS": 0, "EO": 1, "PEATON": 2}[group.code],
                         green_s=20 if ped else timing.ns if group.code == "NS" else timing.eo,
                         yellow_s=0 if ped else 3, clearance_s=10 if ped else 2))
    db.flush()
    timing_for(db, plan)
    audit(db, "propose", f"plan:{plan.id}", reason, after=timing.export(), user=user,
          correlation=correlation)
    return plan


def propose(db, item, infer, *, user=None, correlation=None, target=None):
    mode, reason, timing = "automatic", "Heurística proporcional limitada a ±5 s", Timing()
    forecasts, references, rows, metadata = [], [], [], None
    try:
        rows, references = latest_features(db, item)
        result = infer(rows)
        forecasts, metadata = result["flow_vpm"], result["metadata"]
        required_metadata = {"version", "status", "horizon_min", "artifact_hash", "dataset_hash"}
        if (not isinstance(metadata, dict) or not required_metadata <= metadata.keys()
                or not isinstance(metadata["version"], str) or not 1 <= len(metadata["version"]) <= 80
                or any(not isinstance(metadata[key], str) or len(metadata[key]) != 64
                       or any(char not in "0123456789abcdef" for char in metadata[key])
                       for key in ("artifact_hash", "dataset_hash"))):
            raise ValueError("Metadatos IA incompletos o inválidos")
        if (len(forecasts) != 2 or any(not isfinite(v) or v < 0 for v in forecasts)
                or metadata["status"] != "promoted" or metadata["horizon_min"] != 5):
            raise ValueError("Salida IA inválida")
        previous = Timing(**item.state.get("green_s", {"ns": 40, "eo": 40}))
        timing = suggest(*forecasts, previous)
    except (ValueError, KeyError, TypeError, httpx.HTTPError, OSError):
        mode, reason, forecasts = "degraded", "Datos ausentes/vencidos o IA indisponible/inválida", []
    plan = create_plan(db, item, timing, mode, reason, user=user, target=target,
                       correlation=correlation)
    if forecasts:
        model = db.scalar(select(ModelVersion).where(ModelVersion.version == metadata["version"]))
        if model is None:
            try:
                with db.begin_nested():
                    model = ModelVersion(version=metadata["version"],
                        artifact_hash=metadata["artifact_hash"], dataset_hash=metadata["dataset_hash"],
                        metadata_json=metadata, status="promoted")
                    db.add(model)
                    db.flush()
            except IntegrityError:
                model = db.scalar(select(ModelVersion).where(ModelVersion.version == metadata["version"]))
        for flow, (group, ids), row in zip(forecasts, references, rows):
            prediction = Prediction(group_id=group.id, model_id=model.id,
                decision_at=decision_clock(item), flow_vpm=flow,
                inputs={"record_ids": ids, "features": row, "correlation_id": correlation})
            db.add(prediction)
            db.flush()
            db.add(PlanPrediction(plan_id=plan.id, prediction_id=prediction.id))
    return plan, forecasts


def export_plan(db, plan, forecasts=None):
    return {"id": plan.id, "intersection_id": plan.intersection_id,
            "previous_version": plan.previous_version, "target_cycle": plan.target_cycle,
            "mode": plan.mode, "reason": plan.reason, "status": plan.status,
            "applied_at": plan.applied_at, "expires_cycle": plan.expires_cycle,
            "horizon_min": 5, "flow_vpm": forecasts,
            "heuristic": True, **timing_for(db, plan).export()}


def queue_plan(db, item, plan, expected_version, target_cycle, user=None, correlation=None):
    if not item.active:
        raise HTTPException(409, "Intersección inactiva")
    if not is_live(item):
        raise HTTPException(503, "Trabajador sin telemetría vigente")
    if plan.status != "PROPOSED" or plan.previous_version != expected_version:
        raise HTTPException(409, "Propuesta ya solicitada o versión obsoleta")
    if target_cycle != item.state.get("cycle", -1)+1 or target_cycle != plan.target_cycle:
        raise HTTPException(409, "Solo se permite el siguiente límite de ciclo")
    timing_for(db, plan)
    reserved = db.execute(update(Intersection).where(Intersection.id == item.id,
        Intersection.plan_version == expected_version).values(plan_version=expected_version+1))
    if reserved.rowcount != 1:
        raise HTTPException(409, "Conflicto de versión")
    plan.status = "PENDING"
    audit(db, "queue", f"plan:{plan.id}", plan.reason, before={"version": expected_version},
          after={"version": expected_version+1, "status": "PENDING"}, user=user,
          correlation=correlation)
