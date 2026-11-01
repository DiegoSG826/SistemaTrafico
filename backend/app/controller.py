"""Reglas didácticas de Fase 1; el modelo nunca autoriza movimientos."""
from dataclasses import asdict, dataclass
from math import isfinite


@dataclass(frozen=True)
class Timing:
    ns: int = 40
    eo: int = 40

    def validate(self):
        if (type(self.ns) is not int or type(self.eo) is not int
                or not 20 <= self.ns <= 60 or not 20 <= self.eo <= 60
                or self.ns + self.eo != 80):
            raise ValueError("Verdes enteros 20..60 y suma 80 obligatorios")
        return self

    def export(self):
        return {"green_s": asdict(self), "red_s": {"ns": 117-self.ns, "eo": 117-self.eo},
                "yellow_s": 3, "vehicle_clearance_s": 2,
                "pedestrian_green_s": 20, "pedestrian_clearance_s": 10, "cycle_s": 120}


def suggest(ns: float, eo: float, previous: Timing = Timing()) -> Timing:
    previous.validate()
    if any(not isfinite(v) or v < 0 for v in (ns, eo)):
        raise ValueError("Demanda inválida")
    target = 40 if ns + eo == 0 else max(20, min(60, 80 * ns / (ns + eo)))
    green = round(max(previous.ns - 5, min(previous.ns + 5, target)))
    return Timing(green, 80 - green).validate()


def phase(timing: Timing, second: int) -> dict:
    timing.validate()
    if type(second) is not int or not 0 <= second < 120:
        raise ValueError("Segundo fuera del ciclo")
    timeline = [("NS_GREEN", timing.ns, "GREEN", "RED", "RED"),
                ("NS_YELLOW", 3, "YELLOW", "RED", "RED"),
                ("NS_CLEAR", 2, "RED", "RED", "RED"),
                ("EO_GREEN", timing.eo, "RED", "GREEN", "RED"),
                ("EO_YELLOW", 3, "RED", "YELLOW", "RED"),
                ("EO_CLEAR", 2, "RED", "RED", "RED"),
                ("PEDESTRIAN", 20, "RED", "RED", "GREEN"),
                ("PEDESTRIAN_CLEAR", 10, "RED", "RED", "RED")]
    for name, duration, ns, eo, ped in timeline:
        if second < duration:
            return {"phase": name, "NS": ns, "EO": eo, "PEATON": ped}
        second -= duration
    raise AssertionError("Ciclo inconsistente")
