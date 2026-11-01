"""Promover/revertir exige evidencia y revisores distintos; nunca se promueve al entrenar."""
import argparse
import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path

from .registry import Predictor


def promote(directory, version, experiment_path, author, reviewer, reason):
    directory = Path(directory)
    if not author.strip() or not reviewer.strip() or author.strip() == reviewer.strip():
        raise ValueError("Autor y revisor distintos obligatorios")
    if len(reason.strip()) < 5:
        raise ValueError("Motivo obligatorio")
    candidate = Predictor(directory, candidate_version=version).metadata
    experiment = json.loads(Path(experiment_path).read_text(encoding="utf-8"))
    if (not candidate["eligible_predictive"] or not experiment["eligible_control"]
            or experiment["model_version"] != version
            or experiment["artifact_hash"] != candidate["artifact_hash"]
            or experiment["repetitions"] < 10 or experiment["warmup_s"] != 900
            or experiment["measure_s"] != 7200 or candidate["days"] != 90):
        raise ValueError("No cumple protocolo predictivo/control de Fase 1: conservar plan fijo")
    active = directory / "active.json"
    previous = json.loads(active.read_text(encoding="utf-8"))["version"] if active.exists() else None
    promoted = {**candidate, "status": "promoted", "approval": {
        "author": author, "reviewer": reviewer, "reason": reason,
        "previous_version": previous, "at": datetime.now(UTC).isoformat(),
        "experiment_hash": hashlib.sha256(Path(experiment_path).read_bytes()).hexdigest()}}
    temp = directory / "active.json.tmp"
    temp.write_text(json.dumps(promoted, indent=2), encoding="utf-8")
    os.replace(temp, active)
    with (directory / "promotions.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({"version": version, **promoted["approval"]})+"\n")
    return version


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version")
    parser.add_argument("--experiment", type=Path, required=True)
    parser.add_argument("--author", required=True)
    parser.add_argument("--reviewer", required=True)
    parser.add_argument("--reason", required=True)
    parser.add_argument("--directory", type=Path, default=Path("ml_model/artifacts"))
    args = parser.parse_args()
    print(promote(args.directory, args.version, args.experiment, args.author, args.reviewer, args.reason))
