"""python -m ml_model.train_model --days 90 --output ml_model/artifacts"""
import argparse
import hashlib
import json
import platform
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, root_mean_squared_error
from sklearn.pipeline import make_pipeline

from .synthetic import FEATURES, dataset


def temporal_split(frame, days):
    start = pd.Timestamp("2026-01-01T00:00:00Z")
    train_end = start+pd.Timedelta(days=int(days*.6))
    valid_end = start+pd.Timedelta(days=int(days*.8))
    horizon = pd.Timedelta(minutes=5)
    # La etiqueta termina cinco minutos después de la decisión: purga explícita.
    train = frame[frame["at"] + horizon < train_end]
    valid = frame[(frame["at"] >= train_end) & (frame["at"] + horizon < valid_end)]
    test = frame[frame["at"] >= valid_end]
    return train, valid, test


def metrics(frame, predicted):
    return {"mae": float(mean_absolute_error(frame.target_vpm, predicted)),
            "rmse": float(root_mean_squared_error(frame.target_vpm, predicted))}


def train(days=90, seed=42, output=Path("ml_model/artifacts"), max_rows=300_000):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    frame = dataset(days, seed)
    data_path = output / f"dataset-{seed}-{days}d.csv.gz"
    # mtime=0 y orden fijo permiten verificar el mismo dataset en otra ejecución.
    frame.to_csv(data_path, index=False, compression={"method": "gzip", "mtime": 0})
    data_hash = hashlib.sha256(data_path.read_bytes()).hexdigest()
    training, valid, test = temporal_split(frame, days)
    # Muestreo por bloques horarios; conserva todos los cruces y ambos grupos.
    hours = training["at"].dt.floor("h").unique()
    rng = np.random.default_rng(seed)
    block_count = min(len(hours), max(1, max_rows//600))
    selected_hours = rng.choice(hours, size=block_count, replace=False)
    sampled = training[training["at"].dt.floor("h").isin(selected_hours)]
    if max_rows < 600:
        sampled = sampled.head(max_rows)
    validation_runs = []
    # Dos candidatos, dos pliegues temporales expansivos dentro de entrenamiento.
    for depth in (10, 16):
        scores = []
        for fraction in (.65, .8):
            cut = training["at"].min()+(training["at"].max()-training["at"].min())*fraction
            fold_train = sampled[sampled["at"]+pd.Timedelta(minutes=5) < cut]
            fold_valid = training[(training["at"] >= cut) &
                                  (training["at"] < cut+pd.Timedelta(hours=12))]
            candidate = make_pipeline(SimpleImputer(strategy="median"),
                RandomForestRegressor(n_estimators=40, max_depth=depth, min_samples_leaf=8,
                                      n_jobs=-1, random_state=seed))
            candidate.fit(fold_train[FEATURES], fold_train.target_vpm)
            scores.append(metrics(fold_valid, candidate.predict(fold_valid[FEATURES]))["mae"])
        validation_runs.append({"depth": depth, "expanding_mae": float(np.mean(scores))})
    depth = min(validation_runs, key=lambda x: x["expanding_mae"])["depth"]
    model = make_pipeline(SimpleImputer(strategy="median"), RandomForestRegressor(
        n_estimators=80, max_depth=depth, min_samples_leaf=8, n_jobs=-1, random_state=seed))
    model.fit(sampled[FEATURES], sampled.target_vpm)
    report = {"validation": {}, "test": {}}
    for name, part in (("validation", valid), ("test", test)):
        pred = model.predict(part[FEATURES])
        report[name] = {"model": metrics(part, pred),
                        "persistence": metrics(part, part.mean5_vpm), "rows": len(part)}
        report[name]["by_group"] = {
            f"{i}-{d}": metrics(part[mask], pred[mask.to_numpy()])
            for (i, d), _ in part.groupby(["intersection", "direction"])
            for mask in [(part.intersection == i) & (part.direction == d)]
        }
    version = f"rf-v1-{days}d-s{seed}-{data_hash[:10]}"
    artifact = output / f"{version}.joblib"
    joblib.dump(model, artifact, compress=3)
    test_m = report["test"]
    eligible = test_m["model"]["mae"] <= .9*test_m["persistence"]["mae"]
    metadata = {
        "version": version, "artifact": artifact.name,
        "artifact_hash": hashlib.sha256(artifact.read_bytes()).hexdigest(),
        "dataset_hash": data_hash, "dataset": data_path.name, "features": FEATURES,
        "seed": seed, "days": days, "generator": "synth-v1", "horizon_min": 5,
        "train_rows": len(training), "sampled_rows": len(sampled),
        "train_end": training["at"].max().isoformat(), "cv": validation_runs,
        "metrics": report, "eligible_predictive": eligible,
        "python": platform.python_version(), "sklearn": sklearn.__version__,
        "status": "candidate", "limitation": "Solo datos sintéticos; requiere revisión y evaluación de control",
    }
    (output / f"{version}.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days", type=int, default=90)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-rows", type=int, default=300_000)
    parser.add_argument("--output", type=Path, default=Path("ml_model/artifacts"))
    args = parser.parse_args()
    result = train(args.days, args.seed, args.output, args.max_rows)
    print(json.dumps({k: result[k] for k in ("version", "eligible_predictive", "metrics")}, indent=2))
