import httpx
import pytest
from fastapi.testclient import TestClient

from backend.app.config import Settings
from backend.app.main import create_app
from backend.app.tomtom import FLOW_URL


@pytest.fixture
def open_tomtom_client(system):
    authenticated, factory, _ = system

    def open_client(key):
        config = Settings(jwt_secret="unit-test-secret-" * 4, tomtom_api_key=key)
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
