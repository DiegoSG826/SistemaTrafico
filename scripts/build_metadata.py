"""Generar contrato OpenAPI, migración inicial y bloqueo de dependencias instaladas."""
from importlib.metadata import distribution
from pathlib import Path
import json

from packaging.requirements import Requirement
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateIndex, CreateTable

from backend.app.database import Base
from backend.app import models  # noqa: F401
from backend.app.main import create_app


def main():
    dialect = postgresql.dialect()
    statements = ["-- Esquema v1 generado desde backend/app/models.py. No ejecutar en BD con datos previos.",
                  "-- Las sumas de fases se validan transaccionalmente en el controlador; CHECK por fila no basta."]
    for table in Base.metadata.sorted_tables:
        statements.append(str(CreateTable(table).compile(dialect=dialect)).strip()+";")
        statements.extend(str(CreateIndex(index).compile(dialect=dialect))+";"
                          for index in sorted(table.indexes, key=lambda i: i.name))
    Path("database/migrations").mkdir(exist_ok=True, parents=True)
    statements.append(Path("database/constraints.sql").read_text(encoding="utf-8"))
    Path("database/migrations/001_initial.sql").write_text("\n\n".join(statements)+"\n", encoding="utf-8")
    Path("docs").mkdir(exist_ok=True)
    Path("docs/openapi.json").write_text(json.dumps(create_app().openapi(), indent=2), encoding="utf-8")
    pending = [Requirement(line) for line in Path("requirements.txt").read_text().splitlines() if line]
    seen = set()
    versions = {}
    while pending:
        req = pending.pop()
        key = (req.name.lower(), tuple(sorted(req.extras)))
        if key in seen:
            continue
        seen.add(key)
        package = distribution(req.name)
        versions[package.metadata["Name"]] = package.version
        for raw in package.requires or []:
            dep = Requirement(raw)
            if dep.marker is None or any(dep.marker.evaluate({"extra": extra}) for extra in ["", *req.extras]):
                pending.append(dep)
    Path("requirements.lock").write_text(
        "# Python 3.13; versiones directas y transitivas verificadas.\n"+
        "\n".join(f"{name}=={version}" for name, version in sorted(versions.items(), key=lambda p: p[0].lower()))+"\n",
        encoding="utf-8")


if __name__ == "__main__":
    main()
