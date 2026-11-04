"""Empaquetado local de documentos y código; excluye secretos y bases de usuario."""

from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import shutil
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path.cwd()
OUT = ROOT / "entrega_academica"
BUILD = ROOT / "data/academic-build"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    validated = OUT / "PRE_001_Presentacion_v4.pptx"
    if not validated.exists():
        validated = OUT / "PRE_001_Presentacion.pptx"
    receipt = json.loads((BUILD / "PRE_001_validation_v4.json").read_text(encoding="utf-8"))
    assert sha(validated) == receipt["finalSha256"]
    canonical = OUT / "PRE_001_Presentacion.pptx"
    if canonical.exists() and validated != canonical:
        shutil.copy2(canonical, BUILD / "PRE_001_version_previa.pptx")
    if validated != canonical:
        shutil.copy2(validated, canonical)
    # Conservar revisiones en build, no mezclarlas con el material final para el docente.
    for previous in OUT.glob("PRE_001_Presentacion_v*.pptx"):
        target = BUILD / previous.name
        assert target.resolve().is_relative_to(ROOT)
        shutil.move(str(previous), str(target))
    shutil.copy2(BUILD / "PRE_001_validation_v4.json", OUT / "PRE_001_Validacion.json")
    files = [
        p
        for p in OUT.rglob("*")
        if p.is_file() and p.suffix != ".zip" and p.name != "MANIFIESTO.json"
    ]
    for name in (
        "DOC_001_Memoria",
        "DOC_002_Casos_de_uso",
        "DOC_003_Manual",
        "DOC_004_Pruebas",
        "DOC_005_Resultados",
    ):
        assert all((OUT / (name + ext)).exists() for ext in (".md", ".docx", ".pdf"))
    manifest = {
        "id": "REG_001",
        "created_utc": datetime.now(UTC).isoformat(),
        "scope": "Cuauhtémoc; semáforos y llegadas sintéticas",
        "documents_complete": True,
        "formal_acceptance_complete": False,
        "open_conditions": [
            "Latencia de predicción bajo carga",
            "Alpha/Beta con personas reales",
            "Revisión de dependencias/TLS",
            "Reversión operativa",
            "Aceptación del docente",
            "Docker no ejecutado",
        ],
        "files": [
            {"path": p.relative_to(OUT).as_posix(), "bytes": p.stat().st_size, "sha256": sha(p)}
            for p in sorted(files)
        ],
    }
    (OUT / "MANIFIESTO.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    archive = OUT / "ENT_009_Entrega_Cuauhtemoc.zip"
    with ZipFile(archive, "w", ZIP_DEFLATED, compresslevel=6) as zipfile:
        for file in OUT.rglob("*"):
            if file.is_file() and file.suffix != ".zip":
                zipfile.write(file, "documentos/" + file.relative_to(OUT).as_posix())
        for directory in (
            "backend",
            "database",
            "frontend",
            "ml_model",
            "scripts",
            "tests",
            "docs",
            ".github",
        ):
            for file in (ROOT / directory).rglob("*"):
                if not file.is_file() or "__pycache__" in file.parts or "artifacts" in file.parts:
                    continue
                zipfile.write(file, "codigo/" + file.relative_to(ROOT).as_posix())
        for name in (
            "README.md",
            "LICENSE",
            ".gitignore",
            ".dockerignore",
            ".env.example",
            "compose.yaml",
            "Dockerfile",
            "pyproject.toml",
            "requirements.txt",
            "requirements.lock",
            "requirements-academic.txt",
        ):
            file = ROOT / name
            if file.exists():
                zipfile.write(file, "codigo/" + name)
        for file in (ROOT / "reports").rglob("*"):
            if file.is_file() and file.suffix in (".json", ".xml", ".md"):
                zipfile.write(file, "codigo/" + file.relative_to(ROOT).as_posix())
        # Incluir el modelo local seleccionado para una demostración reproducible.
        active = ROOT / "ml_model/artifacts/active.json"
        if active.exists():
            meta = json.loads(active.read_text(encoding="utf-8"))
            artifact = active.parent / meta["artifact"]
            assert (
                artifact.resolve().is_relative_to(active.parent.resolve())
                and sha(artifact) == meta["artifact_hash"]
            )
            for file in (active, artifact, active.parent / f"{meta['version']}.json"):
                if file.exists():
                    zipfile.write(file, "codigo/" + file.relative_to(ROOT).as_posix())
    with ZipFile(archive) as zipfile:
        assert zipfile.testzip() is None
        assert not any(Path(name).name == ".env" for name in zipfile.namelist())
    print(f"Paquete verificado: {archive.name}, {archive.stat().st_size / 1024**2:.1f} MB")


if __name__ == "__main__":
    main()
