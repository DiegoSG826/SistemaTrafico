"""Capturas reales de una instancia temporal; credenciales efímeras fuera de las imágenes."""

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


def main():
    directory = Path("data") / f"academic-demo-{uuid4().hex}"
    directory.mkdir(parents=True)
    env = {
        **os.environ,
        "DATABASE_URL": f"sqlite:///{(directory / 'demo.db').resolve().as_posix()}",
        "ADMIN_EMAIL": "demo@example.test",
        "ADMIN_PASSWORD": secrets.token_hex(24),
        "JWT_SECRET": secrets.token_hex(32),
        "API_URL": "http://127.0.0.1:29000",
        "ML_SERVICE_URL": "http://127.0.0.1:29001",
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
        "ml": ["-m", "uvicorn", "ml_model.service:app", "--host", "127.0.0.1", "--port", "29001"],
        "api": ["-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", "29000"],
        "worker": ["-m", "backend.worker"],
        "dashboard": [
            "-m",
            "streamlit",
            "run",
            "frontend/dashboard.py",
            "--server.port=29501",
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
                    "http://127.0.0.1:29501/_stcore/health", trust_env=False, timeout=2
                ).is_success:
                    break
            except httpx.HTTPError:
                pass
            if time.monotonic() > until:
                raise RuntimeError("Demo no inició")
            time.sleep(0.5)
        env["DEMO_PASSWORD"] = env["ADMIN_PASSWORD"]
        runtime = Path(
            "C:/Users/diego/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe"
        )
        subprocess.run([str(runtime), "scripts/capture_academic_demo.mjs"], env=env, check=True)
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
