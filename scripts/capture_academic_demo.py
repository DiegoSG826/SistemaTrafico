"""Capturas reales de una instancia temporal; credenciales efímeras fuera de las imágenes."""

from datetime import datetime
import json
import os
from pathlib import Path
import secrets
import shutil
import socket
import subprocess
import sys
import time
from uuid import uuid4
from zoneinfo import ZoneInfo

import httpx
from backend.app.config import Settings
from database.manage import initialize


def available_ports(count):
    listeners = [socket.socket() for _ in range(count)]
    try:
        for listener in listeners:
            listener.bind(("127.0.0.1", 0))
        return [listener.getsockname()[1] for listener in listeners]
    finally:
        for listener in listeners:
            listener.close()


def main():
    if not Settings().tomtom_api_key.get_secret_value().strip():
        raise RuntimeError("Configura TOMTOM_API_KEY para documentar el visor con datos en vivo.")
    directory = Path("data") / f"academic-demo-{uuid4().hex}"
    directory.mkdir(parents=True)
    figures = directory / "figuras"
    api_port, ml_port, dashboard_port = available_ports(3)
    dashboard_url = f"http://127.0.0.1:{dashboard_port}"
    env = {
        **os.environ,
        "DATABASE_URL": f"sqlite:///{(directory / 'demo.db').resolve().as_posix()}",
        "ADMIN_EMAIL": "demo@example.test",
        "ADMIN_PASSWORD": secrets.token_hex(24),
        "JWT_SECRET": secrets.token_hex(32),
        "API_URL": f"http://127.0.0.1:{api_port}",
        "ML_SERVICE_URL": f"http://127.0.0.1:{ml_port}",
        "SGT_DEMO_URL": dashboard_url,
        "SGT_DEMO_FIGURES": str(figures),
        "SIM_SPEED": "10",
    }
    initialize(
        Settings(
            database_url=env["DATABASE_URL"],
            admin_email=env["ADMIN_EMAIL"],
            admin_password=env["ADMIN_PASSWORD"],
            jwt_secret=env["JWT_SECRET"],
        )
    )
    commands = {
        "ml": ["-m", "uvicorn", "ml_model.service:app", "--host", "127.0.0.1", "--port", str(ml_port)],
        "api": ["-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", str(api_port)],
        "worker": ["-m", "backend.worker"],
        "dashboard": [
            "-m",
            "streamlit",
            "run",
            "frontend/dashboard.py",
            f"--server.port={dashboard_port}",
            "--server.headless=true",
            "--browser.gatherUsageStats=false",
            "--server.address=127.0.0.1",
        ],
    }
    processes = []
    logs = []
    try:
        for name, cmd in commands.items():
            stream = (directory / f"{name}.log").open("w", encoding="utf-8")
            logs.append(stream)
            processes.append(
                subprocess.Popen(
                    [sys.executable, *cmd],
                    env=env,
                    stdout=stream,
                    stderr=stream,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
                )
            )
        until = time.monotonic() + 60
        while True:
            try:
                if httpx.get(
                    f"{dashboard_url}/_stcore/health", trust_env=False, timeout=2
                ).is_success and httpx.get(
                    f"{env['API_URL']}/health", trust_env=False, timeout=2
                ).is_success:
                    break
            except httpx.HTTPError:
                pass
            if time.monotonic() > until:
                raise RuntimeError("Demo no inició")
            time.sleep(0.5)
        subprocess.run(
            [env["SGT_ACADEMIC_NODE"], "scripts/capture_academic_demo.mjs"], env=env, check=True,
        )
        destination = Path("entrega_academica/figuras")
        items = [
            "FIG_007_acceso.png", "FIG_008_monitor.png", "FIG_009_intervencion.png",
            "FIG_010_auditoria.png", "FIG_011_tomtom.png",
        ]
        if not all((figures / name).is_file() for name in items):
            raise RuntimeError("Faltan capturas de la instancia de demostración.")
        for name in items:
            shutil.copyfile(figures / name, destination / name)
        metadata = {
            "version_app": subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip(),
            "fecha_cdmx": datetime.now(ZoneInfo("America/Mexico_City")).isoformat(timespec="seconds"),
            "ambiente": "Instancia temporal con SQLite y cuenta de demostración",
            "fuente_tomtom": "Consulta en vivo al tramo cercano al primer punto del catálogo",
            "archivos": items,
        }
        (destination / "CAPTURAS.json").write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
        )
    finally:
        for p in processes:
            if p.poll() is None:
                p.terminate()
        for p in processes:
            try:
                p.wait(timeout=10)
            except subprocess.TimeoutExpired:
                p.kill()
        for s in logs:
            s.close()


if __name__ == "__main__":
    main()
