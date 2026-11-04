"""Ensayos aislados de 5/50 cruces y restauración PostgreSQL; no toca la BD de usuario."""

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import time

import httpx
import psycopg
from psycopg import sql
from sqlalchemy import select, func

from backend.app.config import Settings
from backend.app.database import connect
from backend.app.models import Intersection, TrafficRecord
from database.manage import initialize, add_groups

BIN = Path("C:/Program Files/PostgreSQL/17/bin")
ADMIN = "postgresql://sgt_test@127.0.0.1:55432/postgres"
REPORTS = Path("reports/academico")


def create_database(name):
    assert name.startswith("sgt_academic_") and name.replace("_", "").isalnum()
    with psycopg.connect(ADMIN, autocommit=True) as conn:
        if conn.execute("SELECT 1 FROM pg_database WHERE datname=%s", (name,)).fetchone():
            raise ValueError("La BD de laboratorio ya existe; usar otro sufijo")
        conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
    return f"postgresql+psycopg://sgt_test@127.0.0.1:55432/{name}"


def profile(count, suffix):
    database = f"sgt_academic_{suffix}_{count}"
    url = create_database(database)
    password, secret = secrets.token_hex(24), secrets.token_hex(32)
    config = Settings(
        database_url=url,
        admin_email="qa@example.test",
        admin_password=password,
        jwt_secret=secret,
        app_db_password="",
    )
    initialize(config)
    engine, factory = connect(url)
    with factory.begin() as db:
        for number in range(6, count + 1):
            item = Intersection(
                name=f"Cuauhtémoc · Escala sintética {number}",
                latitude=19.432,
                longitude=-99.145,
                state={},
            )
            db.add(item)
            db.flush()
            add_groups(db, item)
    engine.dispose()
    port = 28000 if count == 5 else 28100
    env = {
        **os.environ,
        "DATABASE_URL": url,
        "ADMIN_EMAIL": config.admin_email,
        "ADMIN_PASSWORD": password,
        "JWT_SECRET": secret,
        "SIM_SPEED": "1",
        "ML_SERVICE_URL": f"http://127.0.0.1:{port + 1}",
        "API_URL": f"http://127.0.0.1:{port}",
    }
    processes, streams = [], []
    commands = {
        "ml": [
            "-m",
            "uvicorn",
            "ml_model.service:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port + 1),
        ],
        "api": [
            "-m",
            "uvicorn",
            "backend.app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        "worker": ["-m", "backend.worker"],
    }
    try:
        for name, command in commands.items():
            stream = (REPORTS / f"load-{count}-{name}.log").open("w", encoding="utf-8")
            streams.append(stream)
            processes.append(
                subprocess.Popen(
                    [sys.executable, *command],
                    env=env,
                    stdout=stream,
                    stderr=stream,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
                )
            )
        with httpx.Client(base_url=env["API_URL"], timeout=10, trust_env=False) as client:
            deadline = time.monotonic() + 90
            while True:
                try:
                    if client.get("/health").is_success:
                        break
                except httpx.HTTPError:
                    pass
                if time.monotonic() > deadline:
                    raise RuntimeError("API de laboratorio no inició")
                time.sleep(0.5)
            login = client.post(
                "/auth/token", json={"email": config.admin_email, "password": password}
            )
            login.raise_for_status()
            client.headers["Authorization"] = "Bearer " + login.json()["access_token"]
            while True:
                items = client.get("/intersections").json()["items"]
                if len(items) == count and all(i["state"].get("cycle", -1) >= 0 for i in items):
                    break
                if time.monotonic() > deadline:
                    raise RuntimeError("El trabajador no publicó los cruces")
                time.sleep(0.5)
            # Ingesta contractual con unidad veh/min y referencia al mismo reloj simulado.
            records = []
            for item in items:
                end = datetime.fromisoformat(item["state"]["sim_time"]).replace(
                    second=0, microsecond=0
                )
                for group in item["groups"]:
                    if group["code"] != "PEATON":
                        records.append(
                            {
                                "group_id": group["id"],
                                "window_start": (end - timedelta(minutes=1)).isoformat(),
                                "window_end": end.isoformat(),
                                "arrivals": 10,
                                "speed_kmh": 30,
                                "weather": "clear",
                                "source": "test",
                            }
                        )
            accepted = client.post("/traffic_records", json=records)
            accepted.raise_for_status()
            accepted_count = sum(r["status"] == "accepted" for r in accepted.json()["results"])
        output = REPORTS / f"load-{count}.json"
        subprocess.run(
            [
                sys.executable,
                "-m",
                "scripts.load_test",
                "--url",
                env["API_URL"],
                "--seconds",
                "600",
                "--users",
                "10",
                "--output",
                str(output),
            ],
            env=env,
            check=True,
        )
        engine, factory = connect(url)
        with factory() as db:
            persisted = db.scalar(
                select(func.count())
                .select_from(TrafficRecord)
                .where(TrafficRecord.source == "test")
            )
            synthetic = db.scalar(
                select(func.count())
                .select_from(TrafficRecord)
                .where(TrafficRecord.source == "synthetic")
            )
        engine.dispose()
        report = json.loads(output.read_text())
        report.update(
            intersections=count,
            database="PostgreSQL 17.4",
            simulation_speed=1,
            accepted_test_records=accepted_count,
            persisted_test_records=persisted,
            accepted_records_preserved=accepted_count == persisted == count * 2,
            synthetic_records=synthetic,
            database_name=database,
            limitations="Concurrencia real local; modelos sin calibración geográfica; carga de catálogo y predicción",
        )
        report["latency_targets_passed"] = (
            report["query"]["p95_ms"] is not None
            and report["prediction"]["p95_ms"] is not None
            and report["query"]["p95_ms"] <= 500
            and report["prediction"]["p95_ms"] <= 1000
            and report["errors"] == 0
        )
        output.write_text(json.dumps(report, indent=2), encoding="utf-8")
        return report
    finally:
        for process in processes:
            if process.poll() is None:
                process.terminate()
        for process in processes:
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
        for stream in streams:
            stream.close()


def recovery(source, suffix):
    source_name = source["database_name"]
    target_name = f"sgt_academic_restore_{suffix}"
    create_database(target_name)
    dump = REPORTS / "recovery.dump"
    started = time.perf_counter()
    subprocess.run(
        [
            str(BIN / "pg_dump.exe"),
            "-h",
            "127.0.0.1",
            "-p",
            "55432",
            "-U",
            "sgt_test",
            "-d",
            source_name,
            "-Fc",
            "-f",
            str(dump),
        ],
        check=True,
    )
    backup_s = time.perf_counter() - started
    start = time.perf_counter()
    subprocess.run(
        [
            str(BIN / "pg_restore.exe"),
            "-h",
            "127.0.0.1",
            "-p",
            "55432",
            "-U",
            "sgt_test",
            "--no-owner",
            "--no-acl",
            "-d",
            target_name,
            str(dump),
        ],
        check=True,
    )
    restore_s = time.perf_counter() - start
    tables = [
        "intersecciones",
        "registros_trafico",
        "planes_semaforicos",
        "auditoria",
        "predicciones",
    ]
    counts = {}
    for database in (source_name, target_name):
        with psycopg.connect(ADMIN.replace("/postgres", "/" + database)) as conn:
            counts[database] = {
                t: conn.execute(
                    sql.SQL("SELECT count(*) FROM {}").format(sql.Identifier(t))
                ).fetchone()[0]
                for t in tables
            }
    report = {
        "database": "PostgreSQL 17.4",
        "source": source_name,
        "restored": target_name,
        "backup_s": backup_s,
        "restore_s": restore_s,
        "counts": counts,
        "counts_match": counts[source_name] == counts[target_name],
        "restore_target_30min_passed": restore_s <= 1800,
        "rpo_measured_s": 0,
        "rpo_scope": "Fuente detenida durante respaldo; no demuestra una política diaria de respaldos",
        "limitation": "Restauración de laboratorio con comparación de conteos; RTO operativo completo requiere reinicio y aceptación humana",
    }
    (REPORTS / "recovery.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    REPORTS.mkdir(exist_ok=True, parents=True)
    suffix = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda n: profile(n, suffix), (5, 50)))
    recovery(results[0], suffix)
    print("Ensayos y restauración completados; resultados en reports/academico")
