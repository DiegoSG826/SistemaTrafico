from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from backend.app.config import Settings
from backend.app.database import Base, connect, utcnow
from backend.app.main import create_app
from backend.app.models import Intersection, TrafficRecord, User
from backend.app.security import hasher
from database.manage import add_groups


@pytest.fixture
def system(tmp_path):
    engine, factory = connect(f"sqlite:///{(tmp_path / 'test.db').as_posix()}")
    Base.metadata.create_all(engine)
    now = utcnow().replace(second=0, microsecond=0)
    with factory.begin() as db:
        item = Intersection(name="Prueba", latitude=19.4, longitude=-99.1, state={
            "sim_time": now.isoformat(), "heartbeat": utcnow().isoformat(),
            "cycle": 0, "second": 1, "green_s": {"ns": 40, "eo": 40},
            "queues": [0, 0], "credit": [0., 0.], "arrivals": [0, 0], "departures": [0, 0]})
        db.add(item)
        db.flush()
        add_groups(db, item)
        db.add(User(email="admin@test", password_hash=hasher.hash("test-password-123"), role="admin"))
        db.add(User(email="viewer@test", password_hash=hasher.hash("test-password-123"), role="viewer"))
        for group in (1, 2):
            for n in range(5, 0, -1):
                db.add(TrafficRecord(group_id=group, window_start=now-timedelta(minutes=n),
                    window_end=now-timedelta(minutes=n-1), arrivals=10, speed_kmh=30,
                    weather="clear", source="test", quality="valid"))
    metadata = {"version": "fake-test-only", "artifact_hash": "a"*64, "dataset_hash": "b"*64,
                "status": "promoted", "horizon_min": 5}
    def infer(rows):
        return {"flow_vpm": [30., 10.], "metadata": metadata}
    app = create_app(Settings(jwt_secret="unit-test-secret-"*4), factory=factory, infer=infer)
    with TestClient(app) as client:
        token = client.post("/auth/token", json={"email": "admin@test", "password": "test-password-123"}).json()["access_token"]
        client.headers["Authorization"] = f"Bearer {token}"
        yield client, factory, now
    engine.dispose()
