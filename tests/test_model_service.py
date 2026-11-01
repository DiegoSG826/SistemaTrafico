import hashlib
import json

import joblib
import pandas as pd
import pytest
import sklearn
from fastapi.testclient import TestClient
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sqlalchemy import func, select

from backend.app.models import PlanPrediction
from ml_model.registry import Predictor
from ml_model.synthetic import FEATURES
from ml_model.promote import promote


@pytest.fixture
def artifact(tmp_path):
    version = "rf-test-fixture"
    row = dict(zip(FEATURES, [0., 1., 0., 0., 10., 10., 30., 1., 0.]))
    frame = pd.DataFrame([row, {**row, "last_vpm": 20.}])
    pipeline = make_pipeline(SimpleImputer(), RandomForestRegressor(n_estimators=2, random_state=42))
    pipeline.fit(frame[FEATURES], [10., 20.])
    path = tmp_path/f"{version}.joblib"
    joblib.dump(pipeline, path)
    manifest = {"version": version, "artifact": path.name, "status": "promoted", "features": FEATURES,
        "artifact_hash": hashlib.sha256(path.read_bytes()).hexdigest(), "dataset_hash": "a"*64,
        "sklearn": sklearn.__version__, "horizon_min": 5, "eligible_predictive": False,
        "days": 5, "approval": {"reason": "Fixture aislado; no es promoción operativa"}}
    (tmp_path/"active.json").write_text(json.dumps(manifest), encoding="utf-8")
    (tmp_path/f"{version}.json").write_text(json.dumps(manifest), encoding="utf-8")
    return tmp_path, manifest, row


def test_real_pipeline_through_internal_service_and_api(artifact, monkeypatch, system):
    directory, manifest, row = artifact
    monkeypatch.setenv("MODEL_DIR", str(directory))
    from ml_model.service import app
    api, factory, _ = system
    with TestClient(app) as ml:
        assert ml.get("/health").json()["loaded"]
        assert ml.post("/predict", json={"rows": [row, row]}).status_code == 200
        def infer(rows):
            response = ml.post("/predict", json={"rows": rows})
            response.raise_for_status()
            return response.json()
        api.app.state.infer = infer
        response = api.post("/predict_light", json={"intersection_id": 1, "previous_version": 0})
        assert response.status_code == 201 and response.json()["mode"] == "automatic"
        assert response.json()["green_s"]["ns"]+response.json()["green_s"]["eo"] == 80
        with factory() as db:
            assert db.scalar(select(func.count()).select_from(PlanPrediction)) == 2


def test_hash_tamper_and_unpromoted_refused(artifact):
    directory, manifest, _ = artifact
    manifest["status"] = "candidate"
    (directory/"active.json").write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="no promovido"):
        Predictor(directory)
    (directory/manifest["artifact"]).write_bytes(b"tampered")
    with pytest.raises(ValueError, match="Hash"):
        Predictor(directory)


def test_promotion_requires_review_and_full_protocol(artifact):
    directory, manifest, _ = artifact
    report = directory/"experiment.json"
    report.write_text(json.dumps({"eligible_control": False}), encoding="utf-8")
    with pytest.raises(ValueError, match="distintos"):
        promote(directory, manifest["version"], report, "same", "same", "Prueba")
    with pytest.raises(ValueError, match="No cumple"):
        promote(directory, manifest["version"], report, "IA", "QA", "Prueba")
