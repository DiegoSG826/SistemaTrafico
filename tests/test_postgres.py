"""Ejecutar contra BD de laboratorio; crea y elimina solo un esquema UUID propio."""
import os
from pathlib import Path
from uuid import uuid4

import pytest
import psycopg
from psycopg import sql
from sqlalchemy import create_engine, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from backend.app.models import Intersection, Plan
from backend.app.services import create_plan
from backend.app.controller import Timing
from database.manage import add_groups

pytestmark = pytest.mark.postgres


@pytest.fixture
def postgres():
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Configurar TEST_DATABASE_URL de laboratorio")
    schema = "sgt_test_"+uuid4().hex
    raw_url = url.replace("postgresql+psycopg://", "postgresql://")
    with psycopg.connect(raw_url, autocommit=True) as conn:
        conn.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
    engine = create_engine(url, connect_args={"options": f"-csearch_path={schema}"})
    try:
        with psycopg.connect(raw_url) as conn:
            conn.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(schema)))
            conn.execute(Path("database/migrations/001_initial.sql").read_text(encoding="utf-8"))
        yield sessionmaker(engine, expire_on_commit=False)
    finally:
        engine.dispose()
        with psycopg.connect(raw_url, autocommit=True) as conn:
            conn.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


def test_migration_partial_index_and_rollback(postgres):
    with postgres.begin() as db:
        item = Intersection(name="PostgreSQL test", latitude=19.4, longitude=-99.1, state={})
        db.add(item)
        db.flush()
        add_groups(db, item)
        first = create_plan(db, item, Timing(), "fixed", "Prueba PostgreSQL", target=0)
        first.status = "ACTIVE"
    with pytest.raises(IntegrityError):
        with postgres.begin() as db:
            item = db.get(Intersection, 1)
            second = create_plan(db, item, Timing(), "fixed", "Segundo plan incompatible", target=0)
            second.status = "ACTIVE"
    with postgres() as db:
        assert len(list(db.scalars(select(Plan).where(Plan.status == "ACTIVE")))) == 1


def test_database_rejects_incomplete_active_plan(postgres):
    with pytest.raises(IntegrityError):
        with postgres.begin() as db:
            item = Intersection(name="Incomplete", latitude=19.4, longitude=-99.1, state={})
            db.add(item)
            db.flush()
            db.add(Plan(intersection_id=item.id, previous_version=0, target_cycle=0,
                        mode="fixed", reason="Plan sin fases", status="ACTIVE"))


def test_concurrent_version_reservation(postgres):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    with postgres.begin() as db:
        item = Intersection(name="Concurrency", latitude=19.4, longitude=-99.1, state={})
        db.add(item)
        db.flush()
        identifier = item.id
    barrier = Barrier(2)
    def reserve(_):
        with postgres.begin() as db:
            barrier.wait(timeout=10)
            return db.execute(update(Intersection).where(Intersection.id == identifier,
                Intersection.plan_version == 0).values(plan_version=1)).rowcount
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(reserve, range(2))) == [0, 1]
