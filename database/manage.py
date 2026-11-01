"""Inicialización explícita y no destructiva; nunca se ejecuta al importar la API."""
import argparse
from pathlib import Path

from sqlalchemy import select

from backend.app.config import settings
from backend.app.database import Base, connect
from backend.app.models import Group, Intersection, Light, User
from backend.app.security import hasher

CATALOG = [("Cruce sintético Reforma 01", 19.427, -99.167),
           ("Cruce sintético Insurgentes 02", 19.419, -99.163),
           ("Cruce sintético Eje Central 03", 19.432, -99.141),
           ("Cruce sintético Universidad 04", 19.361, -99.169),
           ("Cruce sintético Tlalpan 05", 19.342, -99.143)]


def add_groups(db, item, lanes=1, discharge=.5):
    for code in ("NS", "EO", "PEATON"):
        group = Group(intersection_id=item.id, code=code, lanes=lanes if code != "PEATON" else 1,
                      discharge_vps=discharge)
        db.add(group)
        db.flush()
        db.add(Light(group_id=group.id, head=f"SIM-{item.id}-{code}"))


def initialize(config):
    if len(config.admin_password) < 12 or config.admin_password.startswith("CAMBIAR"):
        raise ValueError("Configure ADMIN_PASSWORD propia de al menos 12 caracteres")
    if len(config.jwt_secret) < 32 or config.jwt_secret.startswith("CAMBIAR"):
        raise ValueError("Configure JWT_SECRET propio de al menos 32 caracteres")
    Path("data").mkdir(exist_ok=True)
    engine, factory = connect(config.database_url)
    if engine.dialect.name == "postgresql":
        import psycopg
        from psycopg import sql
        with psycopg.connect(config.database_url.replace("postgresql+psycopg://", "postgresql://")) as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS schema_versions (version integer PRIMARY KEY)")
            if not conn.execute("SELECT 1 FROM schema_versions WHERE version=1").fetchone():
                conn.execute(Path("database/migrations/001_initial.sql").read_text(encoding="utf-8"))
                conn.execute("INSERT INTO schema_versions VALUES (1)")
            if config.app_db_password:
                if len(config.app_db_password) < 16 or config.app_db_password.startswith("CAMBIAR"):
                    raise ValueError("APP_DB_PASSWORD propia de al menos 16 caracteres obligatoria")
                exists = conn.execute("SELECT 1 FROM pg_roles WHERE rolname='traffic_app'").fetchone()
                command = "ALTER ROLE traffic_app WITH LOGIN PASSWORD {}" if exists else \
                          "CREATE ROLE traffic_app WITH LOGIN PASSWORD {}"
                conn.execute(sql.SQL(command).format(sql.Literal(config.app_db_password)))
                conn.execute(Path("database/runtime_permissions.sql").read_text(encoding="utf-8"))
    else:
        Base.metadata.create_all(engine)
    with factory.begin() as db:
        if db.scalar(select(Intersection.id).limit(1)) is None:
            for name, lat, lon in CATALOG:
                item = Intersection(name=name, latitude=lat, longitude=lon, state={})
                db.add(item)
                db.flush()
                add_groups(db, item)
        if not db.scalar(select(User).where(User.email == config.admin_email)):
            db.add(User(email=config.admin_email, password_hash=hasher.hash(config.admin_password)))
    engine.dispose()


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    initialize(settings())
    print("Esquema v1, cinco cruces sintéticos y administrador inicializados")
