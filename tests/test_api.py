from datetime import timedelta

import httpx
import pytest
from sqlalchemy import func, select

from backend.app.models import Intersection, Plan, TrafficRecord


def test_prediction_is_persisted_proposal_not_application(system):
    client, factory, _ = system
    response = client.post("/predict_light", json={"intersection_id": 1, "previous_version": 0})
    assert response.status_code == 201
    result = response.json()
    assert result["flow_vpm"] == [30., 10.]
    assert result["green_s"] == {"ns": 45, "eo": 35}
    assert result["red_s"] == {"ns": 72, "eo": 82}
    assert result["cycle_s"] == 120 and result["status"] == "PROPOSED"
    assert result["applied_at"] is None and result["horizon_min"] == 5
    assert response.headers["X-Correlation-ID"]
    with factory() as db:
        assert db.get(Plan, result["id"]).status == "PROPOSED"
        assert db.get(Intersection, 1).plan_version == 0


def test_queue_is_deferred_and_rejects_stale_version(system):
    client, _, _ = system
    proposals = [client.post("/predict_light", json={"intersection_id": 1, "previous_version": 0}).json()
                 for _ in range(2)]
    body = {"previous_version": 0, "target_cycle": 1}
    assert client.post(f"/plans/{proposals[0]['id']}/apply", json=body).status_code == 202
    assert client.post(f"/plans/{proposals[1]['id']}/apply", json=body).status_code == 409
    plan = client.get(f"/plans/{proposals[0]['id']}").json()
    assert plan["status"] == "PENDING" and plan["applied_at"] is None


@pytest.mark.parametrize("failure", ["old", "missing", "timeout", "nan", "metadata"])
def test_fallback(system, failure):
    client, factory, now = system
    if failure in ("old", "missing"):
        with factory.begin() as db:
            if failure == "old":
                item = db.get(Intersection, 1)
                item.state = {**item.state, "sim_time": (now+timedelta(seconds=121)).isoformat()}
            else:
                db.delete(db.get(TrafficRecord, 1))
    elif failure == "timeout":
        def fail(rows):
            raise httpx.ReadTimeout("test")
        client.app.state.infer = fail
    elif failure == "nan":
        metadata = client.app.state.infer([])["metadata"]
        client.app.state.infer = lambda rows: {"flow_vpm": [float("nan"), 2], "metadata": metadata}
    else:
        client.app.state.infer = lambda rows: {"flow_vpm": [30., 10.],
            "metadata": {"status": "promoted", "horizon_min": 5}}
    result = client.post("/predict_light", json={"intersection_id": 1, "previous_version": 0})
    assert result.status_code == 201
    assert result.json()["mode"] == "degraded"
    assert result.json()["green_s"] == {"ns": 40, "eo": 40}


@pytest.mark.parametrize("body", [
    {"intersection_id": -1, "previous_version": 0},
    {"intersection_id": 1, "previous_version": 0, "arrivals": -10},
])
def test_invalid_prediction_request(system, body):
    client, _, _ = system
    assert client.post("/predict_light", json=body).status_code == 422


def test_permissions(system):
    client, _, _ = system
    client.headers.pop("Authorization")
    assert client.get("/intersections").status_code == 401
    token = client.post("/auth/token", json={"email": "viewer@test", "password": "test-password-123"}).json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    assert client.get("/intersections").status_code == 200
    assert client.post("/predict_light", json={"intersection_id": 1, "previous_version": 0}).status_code == 403


def test_ingest_idempotent_mixed_batch(system):
    client, factory, now = system
    record = {"group_id": 1, "window_start": (now-timedelta(minutes=1)).isoformat(),
              "window_end": now.isoformat(), "arrivals": 12, "speed_kmh": 30,
              "weather": "rain", "source": "synthetic"}
    result = client.post("/traffic_records", json=[record, record, {**record, "arrivals": -1}])
    assert [r["status"] for r in result.json()["results"]] == ["accepted", "duplicate", "rejected"]
    with factory() as db:
        assert db.scalar(select(func.count()).select_from(TrafficRecord)) == 11


def test_manual_invariants_and_expiry(system):
    client, _, _ = system
    body = {"intersection_id": 1, "previous_version": 0, "green_ns": 50, "green_eo": 50,
            "reason": "Prueba manual", "duration_cycles": 1}
    assert client.post("/manual_override", json=body).status_code == 422
    assert client.post("/manual_override", json={**body, "green_eo": 30, "duration_cycles": 11}).status_code == 422
    result = client.post("/manual_override", json={**body, "green_eo": 30})
    assert result.status_code == 202
    assert result.json()["expires_cycle"] == 2


def test_unknown_and_config_conflict(system):
    client, _, _ = system
    assert client.post("/predict_light", json={"intersection_id": 999, "previous_version": 0}).status_code == 404
    body = {"name": "Cruce cambiado", "latitude": 19.4, "longitude": -99.1, "config_version": 1}
    assert client.put("/intersections/1", json=body).status_code == 200
    assert client.put("/intersections/1", json=body).status_code == 409


def test_traffic_filters_and_dates(system):
    client, _, now = system
    result = client.get("/traffic_data", params={"intersection_id": 1, "limit": 2}).json()
    assert len(result["items"]) == 2 and result["items"][0]["current"]
    assert client.get("/traffic_data", params={"start": "invalid"}).status_code == 422
    assert client.get("/traffic_data", params={"start": now.isoformat()}).status_code == 200


def test_timezone_normalization_and_duplicate(system):
    from datetime import timezone
    client, _, now = system
    local = now.astimezone(timezone(timedelta(hours=-6)))
    record = {"group_id": 1, "window_start": (local-timedelta(minutes=1)).isoformat(),
              "window_end": local.isoformat(), "arrivals": 5, "speed_kmh": 30,
              "weather": "clear", "source": "synthetic"}
    assert client.post("/traffic_records", json=[record]).json()["results"][0]["status"] == "accepted"
    utc_record = {**record, "window_start": (now-timedelta(minutes=1)).isoformat(), "window_end": now.isoformat()}
    assert client.post("/traffic_records", json=[utc_record]).json()["results"][0]["status"] == "duplicate"
