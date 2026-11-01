"""Verificación antes de deserializar. Solo artefactos propios en directorio confiable."""
import hashlib
import json
from pathlib import Path

import joblib
import pandas as pd
import sklearn

from .synthetic import FEATURES


class Predictor:
    def __init__(self, directory: Path, candidate_version: str | None = None):
        directory = Path(directory)
        if candidate_version and (Path(candidate_version).name != candidate_version
                                  or any(c in candidate_version for c in ("/", "\\", ":"))):
            raise ValueError("Versión inválida")
        manifest = json.loads((directory / (f"{candidate_version}.json" if candidate_version else
                                           "active.json")).read_text(encoding="utf-8"))
        self.metadata = manifest
        version = manifest["version"]
        if manifest["artifact"] != f"{version}.joblib" or Path(version).name != version:
            raise ValueError("Ruta de artefacto inválida")
        artifact = directory / manifest["artifact"]
        if hashlib.sha256(artifact.read_bytes()).hexdigest() != manifest["artifact_hash"]:
            raise ValueError("Hash de modelo incorrecto")
        if manifest["sklearn"] != sklearn.__version__ or manifest["features"] != FEATURES:
            raise ValueError("Entorno o atributos incompatibles")
        if not candidate_version and manifest["status"] != "promoted":
            raise ValueError("Modelo no promovido")
        self.model = joblib.load(artifact)

    def predict(self, rows):
        return self.model.predict(pd.DataFrame(rows)[FEATURES]).clip(min=0).tolist()
