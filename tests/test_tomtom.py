import httpx
import pytest
from fastapi.testclient import TestClient

from backend.app import tomtom
from backend.app.config import Settings
from backend.app.main import create_app
from backend.app.models import Intersection
from backend.app.tomtom import FLOW_URL


@pytest.fixture
def open_tomtom_client(system):
    authenticated, factory, _ = system

    def open_client(key, **overrides):
        config = Settings(jwt_secret="unit-test-secret-" * 4, tomtom_api_key=key, **overrides)
        return TestClient(create_app(config, factory=factory), headers=authenticated.headers)

    return open_client


def test_tomtom_flow_uses_catalog_point_and_returns_only_traffic(monkeypatch, open_tomtom_client):
    def get(url, *, params, timeout):
        assert url == FLOW_URL
        assert params == {"key": "test-key", "point": "19.4,-99.1", "unit": "kmph"}
        assert timeout.connect == 2
        return httpx.Response(200, request=httpx.Request("GET", url), json={"flowSegmentData": {
            "currentSpeed": 22, "freeFlowSpeed": 45, "currentTravelTime": 87,
            "freeFlowTravelTime": 43, "confidence": 0.84, "roadClosure": False,
            "coordinates": {"coordinate": [{"latitude": 19.4, "longitude": -99.1},
                                           {"latitude": 19.41, "longitude": -99.12}]},
        }})

    monkeypatch.setattr(httpx, "get", get)
    with open_tomtom_client("test-key") as client:
        before = client.get("/traffic_data").json()["items"]
        response = client.get("/intersections/1/tomtom-flow")
        assert response.status_code == 200
        assert response.json() == {
            "source": "tomtom", "fetched_at": response.json()["fetched_at"],
            "current_speed_kmh": 22, "free_flow_speed_kmh": 45, "current_travel_time_s": 87,
            "free_flow_travel_time_s": 43, "confidence": 0.84, "road_closed": False,
            "geometry": [{"latitude": 19.4, "longitude": -99.1}, {"latitude": 19.41, "longitude": -99.12}],
        }
        assert response.json()["fetched_at"].endswith("Z")
        assert client.get("/traffic_data").json()["items"] == before


def test_tomtom_rejects_unauthenticated_and_unconfigured_requests(monkeypatch, open_tomtom_client):
    def unexpected_request(*args, **kwargs):
        pytest.fail("TomTom no debe recibir la consulta")

    monkeypatch.setattr(httpx, "get", unexpected_request)
    with open_tomtom_client("") as client:
        assert client.get("/intersections/999/tomtom-flow").status_code == 404
        response = client.get("/intersections/1/tomtom-flow")
        assert response.status_code == 503
        assert "TOMTOM_API_KEY" in response.json()["detail"]
        del client.headers["Authorization"]
        assert client.get("/intersections/1/tomtom-flow").status_code == 401


@pytest.mark.parametrize(("upstream_status", "expected_status", "message"), [
    (403, 503, "rechazó la clave"),
    (429, 503, "límite de consultas"),
    (200, 502, "datos incompletos"),
])
def test_tomtom_reports_provider_errors_without_upstream_details(
    monkeypatch, open_tomtom_client, upstream_status, expected_status, message,
):
    def get(url, **kwargs):
        return httpx.Response(upstream_status, request=httpx.Request("GET", url),
                              json={"error": "upstream-secret", "flowSegmentData": {}})

    monkeypatch.setattr(httpx, "get", get)
    with open_tomtom_client("test-key") as client:
        response = client.get("/intersections/1/tomtom-flow")
    assert response.status_code == expected_status
    assert message in response.json()["detail"]
    assert "upstream-secret" not in response.text
    assert "test-key" not in response.text


def add_points(system, *latitudes):
    _, factory, _ = system
    with factory.begin() as db:
        db.add_all(Intersection(name="Punto de prueba", latitude=lat, longitude=-99.1)
                   for lat in latitudes)


def flow_response(url, current=87, baseline=43, *, closed=False):
    return httpx.Response(200, request=httpx.Request("GET", url), json={"flowSegmentData": {
        "currentSpeed": 22, "freeFlowSpeed": 45, "currentTravelTime": current,
        "freeFlowTravelTime": baseline, "confidence": 0.84, "roadClosure": closed,
        "coordinates": {"coordinate": [{"latitude": 19.4, "longitude": -99.1},
                                       {"latitude": 19.41, "longitude": -99.12}]},
    }})


def test_comparison_reuses_map_readings_and_orders_the_delays(monkeypatch, system, open_tomtom_client):
    add_points(system, 19.41, 19.42, 19.43, 19.4)
    timestamp = [0.0]
    calls = []
    monkeypatch.setattr(tomtom, "monotonic", lambda: timestamp[0])

    def get(url, *, params, **kwargs):
        point = params["point"]
        calls.append(point)
        if point == "19.41,-99.1":
            return flow_response(url, 51, 60)
        if point == "19.42,-99.1":
            return flow_response(url, closed=True)
        if point == "19.43,-99.1":
            return flow_response(url, baseline=0)
        return flow_response(url, 210, 120)

    monkeypatch.setattr(httpx, "get", get)
    with open_tomtom_client("test-key") as client:
        compare = "/tomtom/comparison"
        assert client.get(compare, params={"point_id": [1, 999]}).status_code == 404
        assert client.get(compare, params={"point_id": [1, 1]}).status_code == 422
        assert client.get(compare, params={"point_id": [1, 2, 3, 4, 5, 6]}).status_code == 422
        assert not calls
        detail = client.get("/intersections/1/tomtom-flow").json()
        params = {"point_id": [2, 1, 3, 4, 5]}
        result = client.get(compare, params=params).json()
        assert [row["intersection_id"] for row in result] == [1, 5, 2, 3, 4]
        assert [row["delay_s"] for row in result] == [90, 90, 0, None, None]
        assert [row["increase_pct"] for row in result] == [75.0, 75.0, 0.0, None, None]
        assert [row["status"] for row in result] == [
            "available", "available", "available", "closed", "no_reference",
        ]
        assert result[0]["fetched_at"] == detail["fetched_at"]
        assert result[0]["confidence"] == 0.84
        assert client.get(compare, params=params).json() == result
        assert client.get("/intersections/2/tomtom-flow").status_code == 200
        assert calls == ["19.4,-99.1", "19.41,-99.1", "19.42,-99.1", "19.43,-99.1"]

        timestamp[0] += tomtom.SAMPLE_TTL_S
        assert client.get("/intersections/1/tomtom-flow").status_code == 200
        assert calls.count("19.4,-99.1") == 2


def test_comparison_stops_at_provider_limit_and_keeps_cached_results(
    monkeypatch, system, open_tomtom_client,
):
    add_points(system, 19.41, 19.42)
    timestamp = [0.0]
    calls = []
    monkeypatch.setattr(tomtom, "monotonic", lambda: timestamp[0])

    def get(url, *, params, **kwargs):
        calls.append(params["point"])
        if len(calls) == 2:
            return httpx.Response(429, request=httpx.Request("GET", url), headers={"Retry-After": "45"})
        return flow_response(url)

    monkeypatch.setattr(httpx, "get", get)
    with open_tomtom_client("test-key") as client:
        assert client.get("/intersections/1/tomtom-flow").status_code == 200
        result = client.get("/tomtom/comparison", params={"point_id": [1, 2, 3]}).json()
        assert [row["status"] for row in result] == ["available", "unavailable", "unavailable"]
        assert "límite de consultas" in result[2]["detail"]
        assert calls == ["19.4,-99.1", "19.41,-99.1"]
        assert client.get("/intersections/1/tomtom-flow").status_code == 200
        timestamp[0] += 44
        blocked = client.get("/intersections/3/tomtom-flow")
        assert blocked.status_code == 503 and blocked.headers["Retry-After"] == "1"
        assert len(calls) == 2
        timestamp[0] += 1
        assert client.get("/intersections/3/tomtom-flow").status_code == 200
        assert len(calls) == 3


def test_daily_budget_limits_real_calls_over_a_rolling_day(monkeypatch, system, open_tomtom_client):
    add_points(system, 19.41)
    timestamp = [0.0]
    calls = []
    monkeypatch.setattr(tomtom, "monotonic", lambda: timestamp[0])

    def get(url, *, params, **kwargs):
        calls.append(params["point"])
        return flow_response(url)

    monkeypatch.setattr(httpx, "get", get)
    with open_tomtom_client("test-key", tomtom_daily_request_budget=1) as client:
        result = client.get("/tomtom/comparison", params={"point_id": [1, 2]}).json()
        assert [row["status"] for row in result] == ["available", "unavailable"]
        assert "presupuesto diario" in result[1]["detail"]
        assert calls == ["19.4,-99.1"]
        assert client.get("/intersections/1/tomtom-flow").status_code == 200
        timestamp[0] += tomtom.DAY_S
        assert client.get("/intersections/2/tomtom-flow").status_code == 200
        assert calls == ["19.4,-99.1", "19.41,-99.1"]
