"""Verificación real local: servicios HTTP, worker, persistencia y dashboard; cierre garantizado."""
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import time
from uuid import uuid4

import httpx

from backend.app.config import Settings
from database.manage import initialize


def run():
    directory = Path("data")/f"smoke-{uuid4().hex}"
    directory.mkdir(parents=True)
    password, secret = secrets.token_hex(24), secrets.token_hex(32)
    db_url = f"sqlite:///{(directory/'traffic.db').resolve().as_posix()}"
    env = {**os.environ, "DATABASE_URL": db_url, "ADMIN_EMAIL": "smoke@example.test",
           "ADMIN_PASSWORD": password, "JWT_SECRET": secret, "SIM_SPEED": "30",
           "MODEL_DIR": str(directory.resolve()/"no-promoted-model"),
           "ML_SERVICE_URL": "http://127.0.0.1:18001", "API_URL": "http://127.0.0.1:18000"}
    initialize(Settings(database_url=db_url, admin_email=env["ADMIN_EMAIL"], admin_password=password,
                        jwt_secret=secret))
    commands = {
        "ml": ["-m", "uvicorn", "ml_model.service:app", "--host", "127.0.0.1", "--port", "18001"],
        "api": ["-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", "18000"],
        "worker": ["-m", "backend.worker"],
        "dashboard": ["-m", "streamlit", "run", "frontend/dashboard.py", "--server.port=18501",
            "--server.address=127.0.0.1", "--server.headless=true", "--browser.gatherUsageStats=false"],
    }
    processes, logs = [], []
    try:
        for name, command in commands.items():
            log = (directory/f"{name}.log").open("w", encoding="utf-8")
            logs.append(log)
            processes.append(subprocess.Popen([sys.executable, *command], env=env, stdout=log, stderr=log,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0))
        def wait_url(url):
            until = time.monotonic()+45
            while time.monotonic() < until:
                try:
                    response = httpx.get(url, timeout=2, trust_env=False)
                    if response.is_success:
                        return response
                except httpx.HTTPError:
                    pass
                time.sleep(.2)
            raise AssertionError(f"Servicio no disponible: {url}; logs en {directory}")
        wait_url("http://127.0.0.1:18000/health")
        wait_url("http://127.0.0.1:18001/health")
        wait_url("http://127.0.0.1:18501/_stcore/health")
        with httpx.Client(base_url=env["API_URL"], timeout=5, trust_env=False) as client:
            response = client.post("/auth/token", json={"email": env["ADMIN_EMAIL"], "password": password})
            response.raise_for_status()
            client.headers["Authorization"] = f"Bearer {response.json()['access_token']}"
            until = time.monotonic()+30
            while time.monotonic() < until:
                items = client.get("/intersections").json()["items"]
                if all(i["telemetry_current"] and i["state"].get("cycle", -1) >= 0 for i in items):
                    break
                time.sleep(.2)
            assert len(items) == 5 and all(i["telemetry_current"] for i in items)
            for item in items:
                state = item["state"]
                assert state["mode"] == "degraded"
                assert all(a-d == q for a, d, q in zip(state["arrivals"], state["departures"], state["queues"]))
            response = client.get("/traffic_data", params={"intersection_id": 1})
            assert response.status_code == 200 and response.json()["items"]
            for _ in range(10):
                item = client.get("/intersections").json()["items"][0]
                response = client.post("/predict_light", json={"intersection_id": 1,
                                                               "previous_version": item["plan_version"]})
                if response.status_code == 409:
                    continue
                response.raise_for_status()
                plan = response.json()
                assert plan["status"] == "PROPOSED" and plan["mode"] == "degraded"
                response = client.post(f"/plans/{plan['id']}/apply", json={
                    "previous_version": plan["previous_version"], "target_cycle": plan["target_cycle"]})
                if response.status_code == 202:
                    break
            assert response.status_code == 202
            until = time.monotonic()+15
            while time.monotonic() < until:
                confirmed = client.get(f"/plans/{plan['id']}").json()
                if confirmed["status"] == "ACTIVE":
                    break
                time.sleep(.1)
            assert confirmed["status"] == "ACTIVE" and confirmed["applied_at"]
            assert client.get("/audit").json()["items"]
        report = {"status": "passed", "services": list(commands), "intersections": 5,
                  "database": "sqlite-isolated", "model_mode": "degraded-unpromoted",
                  "authenticated_http": True, "deferred_application_confirmed": True,
                  "vehicle_conservation": True, "dashboard_http_healthy": True}
        Path("reports/smoke.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps(report, indent=2))
    finally:
        for process in reversed(processes):
            if process.poll() is None:
                process.terminate()
        for process in processes:
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        for log in logs:
            log.close()


if __name__ == "__main__":
    run()
