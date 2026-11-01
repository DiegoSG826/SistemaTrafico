"""Recalcular red de Fase 1, sin confundir duración con horas-persona."""
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


def calculate():
    result = {}
    for name, deps, optimistic, likely, pessimistic in TASKS:
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
    return {"duration_workdays": duration, "calendar_reserve_workdays": 5,
            "critical_path": critical,
            "critical_variance_days2": sum(result[n]["variance"] for n in critical), "tasks": result}


if __name__ == "__main__":
    result = calculate()
    Path("reports").mkdir(exist_ok=True)
    Path("reports/pert.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Duración: {result['duration_workdays']} días hábiles; ruta: {' -> '.join(result['critical_path'])}")
