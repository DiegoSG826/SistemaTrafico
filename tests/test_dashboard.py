from streamlit.testing.v1 import AppTest


def test_login_dashboard_renders_without_backend():
    app = AppTest.from_file("frontend/dashboard.py").run(timeout=20)
    assert not app.exception
    assert app.title[0].value == "Sistema inteligente de tráfico · Cuauhtémoc"
    assert len(app.text_input) == 2
    assert app.text_input[0].label == "Correo"


def test_login_does_not_send_empty_bearer(monkeypatch):
    import httpx
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


def test_switching_to_tomtom_shows_traffic_for_the_selected_point(monkeypatch):
    import httpx

    requests = []
    catalog = {"items": [
        {"id": 1, "name": "Cruce simulado", "latitude": 19.432, "longitude": -99.145,
         "telemetry_current": False, "state": {}},
        {"id": 2, "name": "Otro cruce simulado", "latitude": 19.434, "longitude": -99.147,
         "telemetry_current": False, "state": {}},
    ]}
    traffic = {"source": "tomtom", "fetched_at": "2026-11-22T16:30:00Z", "confidence": 0.84,
               "current_speed_kmh": 22, "free_flow_speed_kmh": 45, "road_closed": True,
               "current_travel_time_s": 87, "free_flow_travel_time_s": 43,
               "geometry": [{"latitude": 19.432, "longitude": -99.145},
                            {"latitude": 19.433, "longitude": -99.146}]}

    def request(method, url, **kwargs):
        req = httpx.Request(method, url)
        requests.append(req.url.path)
        if req.url.path == "/intersections":
            return httpx.Response(200, json=catalog, request=req)
        if req.url.path == "/traffic_data":
            return httpx.Response(200, json={"items": []}, request=req)
        if req.url.path == "/tomtom/comparison":
            assert kwargs["params"] == {"point_id": [1, 2]}
            return httpx.Response(200, request=req, json=[
                {"intersection_id": 1, "status": "available", "delay_s": 44, "increase_pct": 102.3,
                 "confidence": 0.84, "fetched_at": traffic["fetched_at"], "detail": None},
                {"intersection_id": 2, "status": "closed", "delay_s": None, "increase_pct": None,
                 "confidence": 0.84, "fetched_at": traffic["fetched_at"], "detail": None},
            ])
        assert req.url.path in ("/intersections/1/tomtom-flow", "/intersections/2/tomtom-flow")
        return httpx.Response(200, json=traffic, request=req)

    monkeypatch.setattr(httpx, "request", request)
    app = AppTest.from_file("frontend/dashboard.py")
    app.session_state["token"] = "test-token"
    app.run(timeout=20)
    assert not app.exception
    assert not app.sidebar.selectbox
    assert app.selectbox(key="sel_id").label == "Intersección simulada"
    assert [tab.label for tab in app.tabs] == ["Monitor en vivo", "Intervención y Modelo", "Comparador y Auditoría"]
    assert app.tabs[1].slider[0].label == "Verde NS (s)"
    assert all(not path.endswith("/tomtom-flow") for path in requests)

    app.button(key="selbtn_2").click().run(timeout=20)
    assert app.selectbox(key="sel_id").value == 2
    requests.clear()
    app.selectbox(key="vista_trafico").set_value("Tráfico real (TomTom)").run(timeout=20)
    assert not app.exception
    assert requests == ["/intersections", "/intersections/2/tomtom-flow"]
    assert app.selectbox(key="sel_id").label == "Punto de consulta"
    assert {metric.value for metric in app.metric} == {"22 km/h", "45 km/h", "87 s", "43 s", "84%"}
    assert any("Cierre vial" in warning.value for warning in app.warning)
    assert not app.slider

    requests.clear()
    app.selectbox(key="sel_id").set_value(1).run(timeout=20)
    assert not app.exception
    assert requests == ["/intersections", "/intersections/1/tomtom-flow"]

    requests.clear()
    next(button for button in app.tabs[2].button if button.label == "Comparar puntos").click().run(timeout=20)
    assert not app.exception
    assert requests.count("/tomtom/comparison") == 1
    table = app.dataframe[0].value
    assert table.loc[0, "Demora adicional"] == 44
    assert table.loc[0, "Aumento del tiempo"] == 102.3
    assert table.loc[1, "Estado"] == "Cierre reportado"

    requests.clear()
    app.selectbox(key="sel_id").set_value(2).run(timeout=20)
    assert not app.exception
    assert requests == ["/intersections", "/intersections/2/tomtom-flow"]
    assert app.dataframe[0].value.loc[0, "Demora adicional"] == 44
