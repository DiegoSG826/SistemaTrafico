"""Preparar escenario Cuauhtémoc en BD SQLite propia, conservando el histórico anterior."""
from pathlib import Path
import re

from backend.app.config import settings
from backend.app.database import connect
from backend.app.models import Intersection
from backend.app.study_area import CATALOG
from database.manage import initialize
from scripts.configure import configure
from sqlalchemy import select


def select_study_area():
    configure()
    config = settings()
    target = "sqlite:///./data/cuauhtemoc.db"
    if config.database_url not in ("sqlite:///./data/traffic.db", target):
        raise ValueError("Configuración personalizada: use una BD nueva para Cuauhtémoc e inicialícela; "
                         "no se cambiará automáticamente su conexión existente")
    initialize(config.model_copy(update={"database_url": target}))
    engine, factory = connect(target)
    try:
        with factory() as db:
            names = list(db.scalars(select(Intersection.name).order_by(Intersection.id)))
            if names[:5] != [row[0] for row in CATALOG]:
                raise ValueError("La BD de destino contiene otro catálogo; no se sobrescribirá")
    finally:
        engine.dispose()
    env_path = Path(".env")
    current = env_path.read_text(encoding="utf-8")
    updated, count = re.subn(r"(?m)^DATABASE_URL=.*$", "DATABASE_URL="+target, current)
    if count != 1:
        raise ValueError("Se requiere una única línea DATABASE_URL en .env")
    env_path.write_text(updated, encoding="utf-8")
    print("Escenario Cuauhtémoc preparado. Histórico anterior conservado. Reinicie los servicios.")


if __name__ == "__main__":
    select_study_area()
