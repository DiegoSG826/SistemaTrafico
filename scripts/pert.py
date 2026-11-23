"""Recalcular el plan base y la estimación de la ampliación TomTom."""
import json
from pathlib import Path

TASKS = [
    ("A", [], 3, 4, 5), ("B", ["A"], 3, 5, 7), ("C", ["B"], 3, 4, 5),
    ("D", ["B"], 3, 5, 7), ("E", ["C"], 3, 4, 5), ("F", ["B"], 2, 4, 6),
    ("G", ["D"], 5, 7, 9), ("H", ["E"], 4, 6, 8), ("I", ["C", "F"], 6, 8, 10),
    ("J", ["H", "G"], 3, 5, 7), ("K", ["J", "I"], 3, 4, 5),
    ("L", ["K"], 4, 6, 8), ("M", ["K"], 3, 5, 7),
    ("N", ["L", "M"], 2, 4, 6), ("O", ["N"], 2, 3, 4),
]

TOMTOM_TASKS = [
    ("P", [], 1, 2, 3), ("Q", ["P"], 2, 3, 4), ("R", ["P"], 1, 2, 3),
    ("S", ["Q", "R"], 1, 1, 1), ("T", ["S"], 1, 2, 3),
    ("U", ["T"], 1, 1, 1), ("V", ["U"], 1, 2, 3), ("W", ["U"], 1, 1, 1),
    ("X", ["V", "W"], 1, 2, 3),
]
TOMTOM_LABELS = {
    "P": "Diseño y contrato",
    "Q": "Backend y consulta TomTom",
    "R": "Integración del dashboard",
    "S": "Pruebas con el proveedor",
    "T": "Documentación y capturas",
    "U": "Diseño del comparador",
    "V": "Lecturas y cuota del backend",
    "W": "Tabla y selección del tramo",
    "X": "Pruebas y documentación",
}
MILESTONES = [
    {"date_cdmx": "2026-11-01", "commit": "ecf0b0a", "description": "Entrega académica inicial"},
    {"date_cdmx": "2026-11-16", "commit": "e4da62b", "description": "Mapa y simulación en el dashboard"},
    {"date_cdmx": "2026-11-22", "commit": "1e48f7e", "description": "Vista TomTom integrada"},
    {"date_cdmx": "2026-11-23", "commit": "4f377b2", "description": "Comparador integrado"},
]


def calculate(tasks=TASKS, reserve=5):
    result = {}
    for name, deps, optimistic, likely, pessimistic in tasks:
        expected = (optimistic+4*likely+pessimistic)/6
        early = max((result[d]["EF"] for d in deps), default=0)
        result[name] = {"predecessors": deps, "TE": expected, "ES": early, "EF": early+expected,
                        "variance": ((pessimistic-optimistic)/6)**2}
    duration = max(r["EF"] for r in result.values())
    for name in reversed(result):
        successors = [r for r in result.values() if name in r["predecessors"]]
        row = result[name]
        row["LF"] = min((r["LS"] for r in successors), default=duration)
        row["LS"] = row["LF"]-row["TE"]
        row["slack"] = row["LS"]-row["ES"]
    critical = [name for name, row in result.items() if row["slack"] == 0]
    return {"duration_workdays": duration, "calendar_reserve_workdays": reserve,
            "critical_path": critical,
            "critical_variance_days2": sum(result[n]["variance"] for n in critical), "tasks": result}


if __name__ == "__main__":
    result = calculate()
    result["tomtom_extension"] = {
        **calculate(TOMTOM_TASKS, reserve=0),
        "basis": "Estimación académica para reproducir la ampliación. Duraciones ejecutadas sin registrar.",
        "duration_inputs": {code: [optimistic, likely, pessimistic]
                            for code, _, optimistic, likely, pessimistic in TOMTOM_TASKS},
        "labels": TOMTOM_LABELS,
    }
    result["git_milestones"] = MILESTONES
    Path("reports").mkdir(exist_ok=True)
    Path("reports/pert.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Duración: {result['duration_workdays']} días hábiles; ruta: {' -> '.join(result['critical_path'])}")
