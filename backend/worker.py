"""Único trabajador de simulación; no iniciar dentro de Uvicorn."""
import logging
import time
from copy import deepcopy
from datetime import datetime, timedelta
from uuid import uuid4

import httpx
from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError

from ml_model.synthetic import live_minute
from .app import services
from .app.config import settings
from .app.controller import Timing, phase
from .app.database import aware, connect, utcnow
from .app.models import Intersection, Plan, TrafficRecord, WorkerLease

log = logging.getLogger("sgt.worker")


def acquire_lease(db, owner):
    lease = db.scalar(select(WorkerLease).where(WorkerLease.id == 1).with_for_update())
    now = utcnow()
    if lease is None:
        db.add(WorkerLease(id=1, owner=owner, heartbeat=now))
        db.flush()
    elif lease.owner != owner and (now-aware(lease.heartbeat)).total_seconds() <= 15:
        raise RuntimeError("Ya existe un trabajador de simulación activo")
    else:
        lease.owner, lease.heartbeat = owner, now


def bootstrap(db, item, seed):
    now = services.decision_clock(item).replace(second=0, microsecond=0)
    groups = services.groups_for(db, item.id)
    for group in groups:
        if group.code == "PEATON":
            continue
        for age in range(5, 0, -1):
            start = now-timedelta(minutes=age)
            if db.scalar(select(TrafficRecord.id).where(TrafficRecord.group_id == group.id,
                TrafficRecord.source == "synthetic", TrafficRecord.window_start == start)):
                continue
            seconds, weather, speed = live_minute(start, item.id, group.code, seed)
            db.add(TrafficRecord(group_id=group.id, window_start=start,
                window_end=start+timedelta(minutes=1), arrivals=int(seconds.sum()), speed_kmh=speed,
                weather=weather, source="synthetic", quality="valid"))
    # Reinicio explícito desde despeje; no afirmar un color previo no confirmado.
    prior = item.state
    item.state = {"sim_time": now.isoformat(), "cycle": prior.get("cycle", -1), "second": 110,
                  "green_s": {"ns": 40, "eo": 40}, "mode": "degraded",
                  "queues": prior.get("queues", [0, 0]), "credit": [0., 0.],
                  "arrivals": prior.get("arrivals", [0, 0]),
                  "departures": prior.get("departures", [0, 0]),
                  "colors": phase(Timing(), 110), "heartbeat": utcnow().isoformat()}
    db.execute(update(Plan).where(Plan.intersection_id == item.id,
        Plan.status.in_(["ACTIVE", "PENDING"])).values(status="CANCELLED"))
    services.audit(db, "restart", f"intersection:{item.id}", "Reinicio con 10 s de despeje validado")


def cycle_boundary(db, item, cycle, infer):
    # Fallback > manual vigente > propuesta pendiente > automático.
    try:
        services.latest_features(db, item)
        source_ok = True
    except ValueError:
        source_ok = False
    pending = db.scalar(select(Plan).where(Plan.intersection_id == item.id, Plan.status == "PENDING"))
    if pending and pending.target_cycle != cycle:
        pending.status = "CANCELLED"
        pending = None
    manual = db.scalar(select(Plan).where(Plan.intersection_id == item.id, Plan.mode == "manual",
        Plan.target_cycle <= cycle, Plan.expires_cycle > cycle,
        Plan.status.in_(["PENDING", "ACTIVE", "SUPERSEDED"])).order_by(Plan.id.desc()))
    if cycle == item.state.get("recovery_fallback_cycle"):
        def unavailable(rows):
            raise ValueError("Recuperación de persistencia; se requiere un ciclo fijo")
        infer = unavailable
    # Comprobar IA incluso durante una intervención, según RB-11.
    candidate, _ = services.propose(db, item, infer, target=cycle)
    if not source_ok or candidate.mode == "degraded":
        if pending and pending.mode == "degraded" and services.timing_for(db, pending) == Timing():
            chosen = pending
            candidate.status = "CANCELLED"
        else:
            chosen = candidate
    elif manual:
        if manual.status == "PENDING" and manual.target_cycle == cycle:
            chosen = manual
        else:
            chosen = services.create_plan(db, item, services.timing_for(db, manual), "manual",
                manual.reason, target=cycle, expires=manual.expires_cycle)
            chosen.user_id = manual.user_id
        candidate.status = "CANCELLED"
    elif pending and pending.mode == "automatic":
        # Aplicar la propuesta almacenada solo si respeta el cambio desde el plan activo.
        proposed = services.timing_for(db, pending)
        previous = Timing(**item.state["green_s"])
        if abs(proposed.ns-previous.ns) <= 5:
            chosen = pending
            candidate.status = "CANCELLED"
        else:
            chosen = candidate
    else:
        chosen = candidate
    if pending and pending.id != chosen.id:
        pending.status = "SUPERSEDED" if pending.mode == "manual" else "CANCELLED"
    # Primero desactivar y vaciar el flush: respeta índice parcial de plan único.
    db.execute(update(Plan).where(Plan.intersection_id == item.id, Plan.status == "ACTIVE").values(
        status="SUPERSEDED"))
    db.flush()
    if chosen.status != "PENDING":
        item.plan_version += 1
    chosen.status, chosen.applied_at = "ACTIVE", services.decision_clock(item)
    timing = services.timing_for(db, chosen)
    services.audit(db, "apply", f"plan:{chosen.id}", chosen.reason,
        before={"green_s": item.state["green_s"]},
        after={"cycle": cycle, "version": item.plan_version, **timing.export()})
    return timing, chosen


def tick(db, item, seed, infer):
    state = dict(item.state)
    now = aware(datetime.fromisoformat(state["sim_time"]))
    second, cycle = state["second"], state["cycle"]
    timing = Timing(**state["green_s"])
    if second == 0:
        cycle += 1
        timing, chosen = cycle_boundary(db, item, cycle, infer)
        state.update(green_s={"ns": timing.ns, "eo": timing.eo}, mode=chosen.mode,
                     plan_id=chosen.id, reason=chosen.reason)
    colors = phase(timing, second)
    queues, credit = list(state["queues"]), list(state["credit"])
    arrived, departed = list(state["arrivals"]), list(state["departures"])
    minute = now.replace(second=0, microsecond=0)
    groups = {g.code: g for g in services.groups_for(db, item.id)}
    for i, code in enumerate(("NS", "EO")):
        seconds, weather, speed = live_minute(minute, item.id, code, seed)
        count = int(seconds[now.second])
        queues[i] += count
        arrived[i] += count
        group = groups[code]
        if colors[code] == "GREEN":
            credit[i] += group.lanes*group.discharge_vps
            capacity = int(credit[i])
            credit[i] -= capacity
            served = min(queues[i], capacity)
            queues[i] -= served
            departed[i] += served
        else:
            credit[i] = 0
        assert arrived[i]-departed[i] == queues[i]
        if now.second == 59:
            db.add(TrafficRecord(group_id=group.id, window_start=minute,
                window_end=minute+timedelta(minutes=1), arrivals=int(seconds.sum()),
                speed_kmh=speed, weather=weather, source="synthetic", quality="valid"))
    state.update(sim_time=(now+timedelta(seconds=1)).isoformat(), heartbeat=utcnow().isoformat(),
                 cycle=cycle, second=(second+1) % 120, queues=queues, credit=credit,
                 arrivals=arrived, departures=departed, colors=colors)
    item.state = state


def offline_tick(cache, seed):
    """Continuidad local no confirmada; solo fallback y observaciones en memoria."""
    for identifier, entry in cache.items():
        if len(entry["buffer"]) >= 10000:
            log.error("Buffer completo: reloj local detenido para no perder observaciones")
            continue
        state = entry["state"]
        now = aware(datetime.fromisoformat(state["sim_time"]))
        second = state["second"]
        if second == 0:
            state.update(cycle=state["cycle"]+1, green_s={"ns": 40, "eo": 40},
                         mode="degraded", reason="BD indisponible: fallback local sin confirmar",
                         plan_id=None)
            entry["fallback_at"] = now.isoformat()
        timing = Timing(**state["green_s"])
        colors = phase(timing, second)
        for i, code in enumerate(("NS", "EO")):
            minute = now.replace(second=0, microsecond=0)
            counts, weather, speed = live_minute(minute, identifier, code, seed)
            count = int(counts[now.second])
            state["queues"][i] += count
            state["arrivals"][i] += count
            if colors[code] == "GREEN":
                state["credit"][i] += entry["rates"][i]
                capacity = int(state["credit"][i])
                state["credit"][i] -= capacity
                served = min(capacity, state["queues"][i])
                state["queues"][i] -= served
                state["departures"][i] += served
            else:
                state["credit"][i] = 0
            if now.second == 59:
                entry["buffer"].append(dict(group_id=entry["group_ids"][i], window_start=minute,
                    window_end=minute+timedelta(minutes=1), arrivals=int(counts.sum()),
                    speed_kmh=speed, weather=weather, source="synthetic", quality="valid"))
        state.update(sim_time=(now+timedelta(seconds=1)).isoformat(), second=(second+1) % 120,
                     colors=colors)


def recover_local(db, cache):
    for identifier, entry in cache.items():
        item = db.scalar(select(Intersection).where(Intersection.id == identifier).with_for_update())
        before = deepcopy(item.state)
        item.state = deepcopy(entry["state"])
        for record in entry["buffer"]:
            exists = db.scalar(select(TrafficRecord.id).where(
                TrafficRecord.group_id == record["group_id"], TrafficRecord.source == "synthetic",
                TrafficRecord.window_start == record["window_start"]))
            if not exists:
                db.add(TrafficRecord(**record))
        db.execute(update(Plan).where(Plan.intersection_id == identifier,
            Plan.status == "PENDING").values(status="CANCELLED"))
        if entry.get("fallback_at"):
            db.execute(update(Plan).where(Plan.intersection_id == identifier,
                Plan.status == "ACTIVE").values(status="SUPERSEDED"))
            plan = services.create_plan(db, item, Timing(), "degraded",
                "Confirmación diferida del fallback local durante caída de BD", target=item.state["cycle"])
            plan.status = "ACTIVE"
            plan.applied_at = aware(datetime.fromisoformat(entry["fallback_at"]))
            item.plan_version += 1
            item.state = {**item.state, "plan_id": plan.id}
        item.state = {**item.state, "recovery_fallback_cycle": item.state["cycle"]+1}
        services.audit(db, "recover", f"intersection:{identifier}",
            "Persistencia restaurada; sincronización de reloj y buffer local",
            before=before, after={**item.state, "replayed_records": len(entry["buffer"])})


def run():
    config = settings()
    engine, factory = connect(config.database_url)
    owner = str(uuid4())
    with factory.begin() as db:
        acquire_lease(db, owner)
        for item in db.scalars(select(Intersection).where(Intersection.active.is_(True))):
            bootstrap(db, item, config.sim_seed)
    ml_failed_until = 0
    def infer(rows):
        nonlocal ml_failed_until
        if time.monotonic() < ml_failed_until:
            raise ValueError("Circuito IA abierto tras una falla reciente")
        try:
            return services.infer_http(config.ml_service_url, rows)
        except httpx.HTTPError:
            ml_failed_until = time.monotonic()+5
            raise
    cache, offline = {}, False
    try:
        while True:
            start = time.monotonic()
            try:
                with factory.begin() as db:
                    acquire_lease(db, owner)
                    if offline:
                        recover_local(db, cache)
                    items = db.scalars(select(Intersection).where(Intersection.active.is_(True))
                                      .order_by(Intersection.id).with_for_update())
                    next_cache = {}
                    for item in items:
                        if not item.state.get("sim_time"):
                            bootstrap(db, item, config.sim_seed)
                        tick(db, item, config.sim_seed, infer)
                        groups = {g.code: g for g in services.groups_for(db, item.id)}
                        next_cache[item.id] = {"state": deepcopy(item.state), "buffer": [],
                            "rates": [groups[c].lanes*groups[c].discharge_vps for c in ("NS", "EO")],
                            "group_ids": [groups[c].id for c in ("NS", "EO")]}
                cache, offline = next_cache, False
            except SQLAlchemyError:
                if not offline:
                    log.exception("BD indisponible; continúa simulación local y telemetría vencerá")
                offline_tick(cache, config.sim_seed)
                offline = True
            time.sleep(max(0, 1/config.sim_speed-(time.monotonic()-start)))
    finally:
        with factory.begin() as db:
            lease = db.get(WorkerLease, 1)
            if lease and lease.owner == owner:
                db.delete(lease)
        engine.dispose()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        run()
    except KeyboardInterrupt:
        pass
