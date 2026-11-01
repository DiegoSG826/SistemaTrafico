"""Comprobar RNF-08 sobre ramas, además del porcentaje combinado de pytest-cov."""
import json
from pathlib import Path


def main():
    report = json.loads(Path("reports/coverage.json").read_text(encoding="utf-8"))
    checked = 0
    for path, value in report["files"].items():
        normalized = path.replace("\\", "/")
        if normalized.endswith(("backend/app/controller.py", "backend/app/schemas.py")):
            checked += 1
            summary = value["summary"]
            ratio = summary["covered_branches"]/max(1, summary["num_branches"])
            print(f"{normalized}: ramas {ratio:.0%}")
            if ratio < .8:
                raise SystemExit("No cumple RNF-08: ramas <80%")
    if checked != 2:
        raise SystemExit("Faltan módulos obligatorios en el reporte de cobertura")


if __name__ == "__main__":
    main()
