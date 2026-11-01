"""Comparación pareada sin conocer llegadas futuras; las semillas no se usan al entrenar."""
import argparse
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import numpy as np

from backend.app.controller import Timing, phase, suggest
from backend.app.simulation import QueueSimulation
from .registry import Predictor
from .synthetic import features

SCENARIOS = {"valley": (5, 5), "peak": (14, 14), "imbalance": (18, 5),
             "rain_incident": (14, 6), "oversaturation": (35, 35)}


def arrivals_for(seed, scenario, seconds):
    rng = np.random.default_rng(seed)
    base = np.array(SCENARIOS[scenario])
    minute = np.arange((seconds+59)//60)
    # Modulación y ruido por bloques; todas las llegadas se fijan antes de elegir política.
    scale = (1+.2*np.sin(minute/12)+rng.normal(0, .05, len(minute))).clip(.3, 2)
    rate = scale[:, None]*base
    if scenario == "rain_incident":
        rate[(minute//15) % 2 == 1, 0] *= .6
    return rng.poisson(np.repeat(rate/60, 60, axis=0)[:seconds]), rate


def run_pair(predictor, seed, scenario, warmup_s=900, measure_s=7200):
    total = warmup_s+measure_s
    arrivals, rate = arrivals_for(seed, scenario, total)
    start = datetime(2026, 6, 1, 14, tzinfo=UTC)
    minute_totals = arrivals[:(total//60)*60].reshape(-1, 60, 2).sum(axis=1)
    decision_seconds = list(range(360, total, 120))
    rows = []
    for second in decision_seconds:
        minute = second//60
        for i, code in enumerate(("NS", "EO")):
            rows.append(features(start+timedelta(seconds=second),
                "rain" if scenario == "rain_incident" else "clear",
                minute_totals[minute-5:minute, i].tolist(),
                max(1, 55-rate[minute-1, i]*1.2), 1, code))
    forecasts = dict(zip(decision_seconds, np.array(predictor.predict(rows)).reshape(-1, 2)))
    output = {}
    for policy in ("fixed", "adaptive"):
        sim = QueueSimulation()
        timing, queue_sizes = Timing(), []
        ped_wait, elapsed_since_walk = [], 0
        measured_departures = [0, 0]
        start_wait_index = 0
        delay = 0
        conflicts = omissions = 0
        ped_seen = 0
        for second in range(total):
            if second % 120 == 0:
                if second and ped_seen != 20:
                    omissions += 1
                ped_seen = 0
                if policy == "adaptive" and second in forecasts:
                    timing = suggest(*forecasts[second], timing)
            colors = phase(timing, second % 120)
            conflicts += int(sum(colors[g] in ("GREEN", "YELLOW")
                                 for g in ("NS", "EO", "PEATON")) > 1)
            ped_seen += int(colors["PEATON"] == "GREEN")
            if second == warmup_s:
                measured_departures = sim.departures.copy()
                start_wait_index = len(sim.served_wait)
            queue = sim.tick(second, arrivals[second], timing, second % 120)
            if colors["PEATON"] == "GREEN":
                elapsed_since_walk = 0
            else:
                elapsed_since_walk += 1
            if second >= warmup_s:
                delay += queue
                queue_sizes.append(queue)
                ped_wait.append(elapsed_since_walk)
        wait = sim.served_wait[start_wait_index:]
        output[policy] = {"delay_vehicle_s": delay, "queue_mean_veh": float(np.mean(queue_sizes)),
            "queue_p95_veh": float(np.percentile(queue_sizes, 95)),
            "departures_veh": int(sum(np.array(sim.departures)-measured_departures)),
            "pending_veh": sum(map(len, sim.queues)),
            "served_wait_mean_s": float(np.mean(wait)) if wait else None,
            "pedestrian_max_red_s": max(ped_wait),
            "conflicts": conflicts, "pedestrian_omissions_complete_cycles": omissions}
    return {"seed": seed, "scenario": scenario, **output}


def evaluate(directory, version, repetitions=10, warmup_s=900, measure_s=7200):
    predictor = Predictor(directory, candidate_version=version)
    runs = [run_pair(predictor, seed, scenario, warmup_s, measure_s)
            for index, scenario in enumerate(SCENARIOS)
            for seed in range(10001+index*100, 10001+index*100+repetitions)]
    nonsaturated = [r for r in runs if r["scenario"] != "oversaturation"]
    reductions = np.array([(r["fixed"]["delay_vehicle_s"]-r["adaptive"]["delay_vehicle_s"])
        /max(1, r["fixed"]["delay_vehicle_s"]) for r in nonsaturated])
    if len(reductions) > 1:
        # Mantener la composición de escenarios fija; remuestrear corridas dentro de cada uno.
        blocks = reductions.reshape(4, repetitions)
        rng = np.random.default_rng(9801)
        resampled = np.stack([rng.choice(block, size=(5000, repetitions), replace=True).mean(axis=1)
                              for block in blocks]).mean(axis=0)
        low, high = np.percentile(resampled, [2.5, 97.5]).tolist()
    else:
        low = high = float(reductions[0])
    queue_ok = all(r["adaptive"]["queue_p95_veh"] <= 1.1*r["fixed"]["queue_p95_veh"] for r in nonsaturated)
    safe = all(r[p]["conflicts"] == r[p]["pedestrian_omissions_complete_cycles"] == 0
               for r in runs for p in ("fixed", "adaptive"))
    eligible = float(reductions.mean()) >= .1 and low > 0 and queue_ok and safe
    return {"model_version": version, "artifact_hash": predictor.metadata["artifact_hash"],
            "protocol": "paired-v1", "ci_method": "bootstrap-paired-runs-stratified-by-scenario",
            "repetitions": repetitions, "warmup_s": warmup_s,
            "measure_s": measure_s, "seed_start": 10001, "seed_scenario_stride": 100,
            "mean_delay_reduction": float(reductions.mean()), "ci95": [low, high],
            "queue_guard_passed": queue_ok, "invariants_passed": safe,
            "eligible_control": eligible, "runs": runs,
            "limitation": "Sintético, cruces independientes, espera peatonal como tiempo rojo máximo; sin llegadas peatonales individuales"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version")
    parser.add_argument("--directory", type=Path, default=Path("ml_model/artifacts"))
    parser.add_argument("--output", type=Path, default=Path("reports/experiment.json"))
    parser.add_argument("--repetitions", type=int, default=10)
    parser.add_argument("--warmup", type=int, default=900)
    parser.add_argument("--measure", type=int, default=7200)
    args = parser.parse_args()
    if args.repetitions < 1 or args.warmup < 360 or args.measure < 120:
        parser.error("Repeticiones >=1, calentamiento >=360 y medición >=120")
    report = evaluate(args.directory, args.version, args.repetitions, args.warmup, args.measure)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "runs"}, indent=2))
