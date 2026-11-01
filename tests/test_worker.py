
from copy import deepcopy

import httpx
import pytest
from sqlalchemy import select

from backend.app.models import Intersection, Plan
from backend.app.services import timing_for
from backend.worker import acquire_lease, bootstrap, offline_tick, recover_local, tick


def test_apply_only_at_boundary_and_automatic_slew(system):
    client, factory, _ = system
    proposed = client.post("/predict_light", json={"intersection_id": 1, "previous_version": 0}).json()
    assert client.post(f"/plans/{proposed['id']}/apply", json={"previous_version": 0,
        "target_cycle": 1}).status_code == 202
    with factory.begin() as db:
        item = db.get(Intersection, 1)
        item.state = {**item.state, "second": 119}
        tick(db, item, 13, client.app.state.infer)
        assert db.get(Plan, proposed["id"]).status == "PENDING"
        tick(db, item, 13, client.app.state.infer)
        assert db.get(Plan, proposed["id"]).status == "ACTIVE"
        assert item.state["green_s"] == {"ns": 45, "eo": 35}
        assert item.state["colors"]["phase"] == "NS_GREEN"


def test_manual_expiry_and_fallback_precedence(system):
    client, factory, _ = system
    result = client.post("/manual_override", json={"intersection_id": 1, "previous_version": 0,
        "green_ns": 60, "green_eo": 20, "reason": "Demostración controlada", "duration_cycles": 1})
    assert result.status_code == 202
    with factory.begin() as db:
        item = db.get(Intersection, 1)
        item.state = {**item.state, "second": 0}
        tick(db, item, 13, client.app.state.infer)
        assert item.state["mode"] == "manual" and item.state["green_s"]["ns"] == 60
        item.state = {**item.state, "second": 0}
        tick(db, item, 13, client.app.state.infer)
        assert item.state["mode"] == "automatic" and item.state["green_s"]["ns"] == 60
        def failed(rows):
            raise httpx.ReadTimeout("test")
        item.state = {**item.state, "second": 0}
        tick(db, item, 13, failed)
        assert item.state["mode"] == "degraded" and item.state["green_s"]["ns"] == 40
        active = list(db.scalars(select(Plan).where(Plan.status == "ACTIVE")))
        assert len(active) == 1 and timing_for(db, active[0]).ns == 40


def test_single_worker_and_safe_restart(system):
    _, factory, now = system
    with factory.begin() as db:
        acquire_lease(db, "owner-one")
        with pytest.raises(RuntimeError):
            acquire_lease(db, "owner-two")
        item = db.get(Intersection, 1)
        bootstrap(db, item, 13)
        assert item.state["second"] == 110
        assert all(item.state["colors"][g] == "RED" for g in ("NS", "EO", "PEATON"))


def test_offline_fallback_conservation_and_recovery(system):
    _, factory, _ = system
    with factory() as db:
        state = deepcopy(db.get(Intersection, 1).state)
    state.update(second=0, green_s={"ns": 60, "eo": 20})
    cache = {1: {"state": state, "rates": [.5, .5], "group_ids": [1, 2], "buffer": []}}
    for _ in range(125):
        offline_tick(cache, 13)
    assert state["mode"] == "degraded" and state["green_s"] == {"ns": 40, "eo": 40}
    assert all(a-d == q for a, d, q in zip(state["arrivals"], state["departures"], state["queues"]))
    assert len(cache[1]["buffer"]) >= 2
    with factory.begin() as db:
        recover_local(db, cache)
        item = db.get(Intersection, 1)
        assert item.state["sim_time"] == state["sim_time"]
        assert item.state["recovery_fallback_cycle"] == state["cycle"]+1
        assert len(list(db.scalars(select(Plan).where(Plan.status == "ACTIVE")))) == 1
