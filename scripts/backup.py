"""Respaldos PostgreSQL en formato custom. Contraseña por entorno, nunca en argumentos."""
import argparse
from datetime import UTC, datetime
import os
from pathlib import Path
import subprocess

from sqlalchemy.engine import make_url

from backend.app.config import settings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pg-dump", default="pg_dump")
    parser.add_argument("--output", type=Path, default=Path("data/backups"))
    args = parser.parse_args()
    url = make_url(settings().database_url)
    if url.get_backend_name() != "postgresql":
        parser.error("Usar PostgreSQL para este procedimiento; detener procesos antes de copiar SQLite")
    args.output.mkdir(parents=True, exist_ok=True)
    target = args.output / (datetime.now(UTC).strftime("traffic-%Y%m%dT%H%M%SZ")+".dump")
    env = {**os.environ, "PGPASSWORD": url.password or ""}
    subprocess.run([args.pg_dump, "-h", url.host or "localhost", "-p", str(url.port or 5432),
                    "-U", url.username or "traffic", "-d", url.database, "-Fc", "-f", str(target)],
                   check=True, env=env)
    print(f"Respaldo creado: {target}")


if __name__ == "__main__":
    main()
