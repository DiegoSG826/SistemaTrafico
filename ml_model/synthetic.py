"""Datos didácticos, sin calibración con aforos de CDMX. Versión synth-v1."""
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
from scipy.signal import lfilter

WEATHER = ("clear", "rain", "heavy_rain")
FEATURES = ["hour_sin", "hour_cos", "weekday", "weather", "last_vpm", "mean5_vpm",
            "speed_kmh", "intersection", "direction"]


def features(at: datetime, weather: str, history: list[int], speed: float,
             intersection: int, direction: str) -> dict:
    if len(history) != 5 or weather not in WEATHER:
        raise ValueError("Se requieren cinco ventanas y clima conocido")
    local = at.astimezone(ZoneInfo("America/Mexico_City"))
    angle = 2 * np.pi * (local.hour + local.minute / 60) / 24
    return dict(zip(FEATURES, [float(np.sin(angle)), float(np.cos(angle)), local.weekday(),
                             WEATHER.index(weather), history[-1], float(np.mean(history)),
                             speed, intersection, int(direction == "EO")]))


def dataset(days=90, seed=42, intersections=5, start="2026-01-01T00:00:00Z"):
    if days < 5:
        raise ValueError("Se requieren al menos cinco días")
    timestamps = pd.date_range(start, periods=days*1440, freq="min")
    local = timestamps.tz_convert("America/Mexico_City")
    hour = local.hour.to_numpy() + local.minute.to_numpy()/60
    weather_rng = np.random.default_rng(seed)
    weather = np.repeat(weather_rng.choice(3, size=days*24, p=[.75, .2, .05]), 60)
    frames = []
    for intersection in range(1, intersections+1):
        for code in ("NS", "EO"):
            rng = np.random.default_rng([seed, intersection, int(code == "EO")])
            peak = (18*np.exp(-((hour-8)/1.8)**2) + 15*np.exp(-((hour-18)/2.2)**2))
            weekday = np.where(local.dayofweek < 5, 1., .65)
            noise = lfilter([1], [1, -.85], rng.normal(0, .5, len(hour)))
            incident = np.repeat(rng.choice([1., .55], size=days*24, p=[.97, .03]), 60)
            direction_factor = 1.15 if code == "NS" else .85
            rate = np.maximum(.5, (4+peak)*weekday*direction_factor*(.8+intersection*.06)
                              * (1-weather*.12)*incident + noise)
            arrivals = rng.poisson(rate).clip(0, 300)
            speed = np.clip(55-rate*1.2 + rng.normal(0, 3, len(rate)), 1, 100)
            frame = pd.DataFrame({
                "at": timestamps + pd.Timedelta(minutes=1),
                "intersection": intersection, "direction": int(code == "EO"),
                "hour_sin": np.sin(2*np.pi*((hour+1/60) % 24)/24),
                "hour_cos": np.cos(2*np.pi*((hour+1/60) % 24)/24),
                "weekday": (local+pd.Timedelta(minutes=1)).dayofweek,
                "weather": weather, "last_vpm": arrivals, "speed_kmh": speed,
            })
            frame["mean5_vpm"] = pd.Series(arrivals).rolling(5).mean()
            frame["target_vpm"] = sum(pd.Series(arrivals).shift(-i) for i in range(1, 6))/5
            frames.append(frame.dropna())
    return pd.concat(frames, ignore_index=True).sort_values(
        ["at", "intersection", "direction"]).reset_index(drop=True)


def live_minute(at: datetime, intersection: int, direction: str, seed: int):
    """Misma ventana/semilla = mismas llegadas, independiente del control."""
    minute = int(at.astimezone(UTC).timestamp())//60
    rng = np.random.default_rng([seed, minute, intersection, int(direction == "EO")])
    local = at.astimezone(ZoneInfo("America/Mexico_City"))
    hour = local.hour+local.minute/60
    weather = WEATHER[int(np.random.default_rng([seed, minute//60]).choice(3, p=[.75,.2,.05]))]
    rate = 4 + 18*np.exp(-((hour-8)/1.8)**2) + 15*np.exp(-((hour-18)/2.2)**2)
    rate *= (1.15 if direction == "NS" else .85)*(1-.12*WEATHER.index(weather))
    count = int(rng.poisson(rate))
    seconds = rng.multinomial(count, np.full(60, 1/60))
    return seconds, weather, float(max(1, 55-rate*1.2))
