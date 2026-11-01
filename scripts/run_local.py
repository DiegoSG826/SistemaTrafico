"""Lanzador local de cuatro procesos. Ctrl+C cierra los procesos que creó."""
import os
import socket
from pathlib import Path
import subprocess
import sys
import time

from database.manage import initialize
from backend.app.config import settings
from scripts.configure import configure


def main():
    configure()
    for port in (8000, 8001, 8501):
        with socket.socket() as probe:
            try:
                probe.bind(("127.0.0.1", port))
            except OSError:
                raise SystemExit(f"Puerto {port} ocupado. Cierra la ejecución anterior con Ctrl+C "
                                 "antes de iniciar otra. No se inició ningún servicio.")
    initialize(settings())
    Path("reports/local").mkdir(parents=True, exist_ok=True)
    commands = {
        "ml": ["-m", "uvicorn", "ml_model.service:app", "--host", "127.0.0.1", "--port", "8001"],
        "api": ["-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", "8000"],
        "worker": ["-m", "backend.worker"],
        "dashboard": ["-m", "streamlit", "run", "frontend/dashboard.py", "--server.address=127.0.0.1",
                      "--server.port=8501", "--server.headless=true", "--browser.gatherUsageStats=false"],
    }
    processes, logs = [], []
    try:
        for name, command in commands.items():
            stream = Path(f"reports/local/{name}.log").open("w", encoding="utf-8")
            logs.append(stream)
            processes.append(subprocess.Popen([sys.executable, *command], stdout=stream, stderr=stream,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0))
        print("Dashboard: http://127.0.0.1:8501 · API: http://127.0.0.1:8000/docs")
        print("Credenciales en .env; registros en reports/local. Ctrl+C para terminar.")
        while all(p.poll() is None for p in processes):
            time.sleep(1)
        failed = next(name for name, process in zip(commands, processes) if process.poll() is not None)
        raise RuntimeError(f"El servicio {failed} terminó. Revisa reports/local/{failed}.log")
    except KeyboardInterrupt:
        pass
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
        for stream in logs:
            stream.close()


if __name__ == "__main__":
    main()
