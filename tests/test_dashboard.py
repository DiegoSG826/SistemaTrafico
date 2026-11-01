from streamlit.testing.v1 import AppTest


def test_login_dashboard_renders_without_backend():
    app = AppTest.from_file("frontend/dashboard.py").run(timeout=20)
    assert not app.exception
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
