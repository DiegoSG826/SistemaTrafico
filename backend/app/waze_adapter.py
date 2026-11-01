"""Puerto de normalización offline de un feed autorizado, sin inventar conteos.

El mapeo segmento→grupo debe validarse externamente. No hay credenciales ni consulta HTTP.
Un feed Waze solo nunca habilita el modo adaptativo basado en conteos.
"""
from datetime import timedelta


def normalize_jam(jam: dict, group_id: int, window_start):
    # El campo speed de jams utiliza m/s; speedKMH utiliza km/h.
    speed = jam.get("speedKMH")
    if speed is None and jam.get("speed") is not None:
        speed = jam["speed"]*3.6
    return {"group_id": group_id, "window_start": window_start.isoformat(),
            "window_end": (window_start+timedelta(minutes=1)).isoformat(), "arrivals": None,
            "speed_kmh": speed, "weather": None, "source": "waze",
            "external_id": str(jam.get("uuid", ""))}
