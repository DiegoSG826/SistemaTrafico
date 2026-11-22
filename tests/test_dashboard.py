import json
from datetime import UTC, datetime

import httpx
from streamlit.testing.v1 import AppTest


def test_login_dashboard_renders_without_backend():
    app = AppTest.from_file("frontend/dashboard.py").run(timeout=20)
    assert not app.exception
    assert len(app.text_input) == 2
    assert app.text_input[0].label == "Correo"


def test_login_does_not_send_empty_bearer(monkeypatch):
    requests = []

    def request(method, url, **kwargs):
        requests.append((url, kwargs))
        return httpx.Response(401, json={"detail": "Credenciales inválidas"},
                              request=httpx.Request(method, url))

    monkeypatch.setattr(httpx, "request", request)
    app = AppTest.from_file("frontend/dashboard.py").run(timeout=20)
    app.text_input[1].set_value("contraseña-de-prueba")
    app.button[0].click().run(timeout=20)
    assert not app.exception
    assert requests and requests[0][0].endswith("/auth/token")
    assert "Authorization" not in requests[0][1]["headers"]


def test_dashboard_switches_traffic_source_without_mixing_data(monkeypatch):
    calls = []
    center = {"latitude": 19.42568, "longitude": -99.15462}
    paths = {
        "/auth/token": {"access_token": "testing-only"},
        "/intersections": {"items": [{
            "id": 1, "name": "Cruce simulado", **center, "plan_version": 1,
            "telemetry_current": False, "state": {},
        }]},
        "/traffic_data": {"items": []},
        "/traffic/live": {"location": "Metro Cuauhtémoc", "configured": True, "center": center,
                          "segments": [{"label": "Acceso sur", "point": center, "status": "stale",
                                        "retrieved_at": "2026-11-20T11:00:00Z", "flow": {
                                            "speed_kmh": 20, "free_flow_speed_kmh": 40,
                                            "travel_time_s": 60, "free_flow_travel_time_s": 30,
                                            "closed": False, "confidence": 0.8,
                                            "geometry": [center, {**center, "latitude": 19.424}],
                                        }}]},
    }

    def request(method, url, **kwargs):
        path = httpx.URL(url).path
        calls.append(path)
        return httpx.Response(200, json=paths[path], request=httpx.Request(method, url))

    monkeypatch.setattr(httpx, "request", request)
    app = AppTest.from_file("frontend/dashboard.py")
    app.session_state["token"] = "testing-only"
    app.run(timeout=20)
    assert not app.exception
    assert app.radio(key="fuente_trafico").value == "Simulado"
    assert "/traffic/live" not in calls

    calls.clear()
    app.radio(key="fuente_trafico").set_value("Real (TomTom)").run(timeout=20)
    assert not app.exception
    assert calls == ["/traffic/live"]
    assert len(app.get("iframe")) == 2
    assert "Carga un aforo CSV" in app.get("iframe")[1].proto.srcdoc
    table = app.dataframe[0].value
    assert table.loc[0, "Estado"] == "Datos vencidos"
    assert table.loc[0, "Velocidad (km/h)"] == 20
    assert table.loc[0, "Demora (s)"] == 30

    app.session_state["aforo_filas"] = [(datetime(2026, 11, 21, 14, tzinfo=UTC), 0, 24)]
    app.run(timeout=20)
    app.slider[0].set_value(30)
    next(b for b in app.button if b.label == "Reproducir aforo").click().run(timeout=20)
    assert not app.exception
    replay = app.session_state["aforo_replay"]
    assert replay["verde_ns"] == 30
    assert replay["conteos"] == [[0, 24]]
    assert all(json.dumps(replay) in frame.proto.srcdoc for frame in app.get("iframe"))

    calls.clear()
    app.radio(key="fuente_trafico").set_value("Simulado").run(timeout=20)
    assert not app.exception
    assert "/traffic/live" not in calls
    assert len(app.get("iframe")) == 2
