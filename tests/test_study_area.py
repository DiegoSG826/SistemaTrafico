from backend.app.config import Settings
from backend.app.database import connect
from backend.app.models import Intersection
from backend.app.study_area import CATALOG, STUDY_AREA
from database.manage import initialize
from sqlalchemy import select


def test_cuauhtemoc_catalog_is_idempotent_and_separate(tmp_path):
    config = Settings(database_url=f"sqlite:///{(tmp_path/'cuauhtemoc.db').as_posix()}",
                      admin_password="test-password-only-123", jwt_secret="test-only-secret-"*4)
    initialize(config)
    initialize(config)
    engine, factory = connect(config.database_url)
    try:
        with factory() as db:
            names = list(db.scalars(select(Intersection.name).order_by(Intersection.id)))
            assert names == [entry[0] for entry in CATALOG]
            assert len(names) == 5 and all("Cuauhtémoc" in name for name in names)
    finally:
        engine.dispose()


def test_api_exposes_academic_study_area(system):
    client, _, _ = system
    assert client.get("/intersections").json()["study_area"] == STUDY_AREA
    assert client.get("/health").json()["study_area"]["simulation_only"]
