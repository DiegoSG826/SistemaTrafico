import math

import numpy as np
import pytest

from backend.app.controller import Timing, phase, suggest
from backend.app.simulation import QueueSimulation


@pytest.mark.parametrize("timing", [Timing(19, 61), Timing(50, 50), Timing(40.0, 40)])
def test_invalid_timing(timing):
    with pytest.raises(ValueError):
        timing.validate()


def test_proportional_examples_and_invalid():
    assert suggest(30, 10) == Timing(45, 35)
    assert suggest(0, 0) == Timing()
    assert suggest(0, 100, Timing(20, 60)) == Timing(20, 60)
    for value in (-1, math.nan, math.inf):
        with pytest.raises(ValueError):
            suggest(value, 1)
    with pytest.raises(ValueError):
        phase(Timing(), 120)
    with pytest.raises(ValueError):
        phase(Timing(), -1)


def test_thousands_of_plans_and_every_phase():
    rng = np.random.default_rng(91)
    for _ in range(3000):
        prev_ns = int(rng.integers(20, 61))
        timing = suggest(*rng.uniform(0, 500, 2), Timing(prev_ns, 80-prev_ns))
        assert abs(timing.ns-prev_ns) <= 5
        assert timing.ns+timing.eo == 80 and 20 <= timing.ns <= 60
    for ns in range(20, 61):
        colors = [phase(Timing(ns, 80-ns), s) for s in range(120)]
        assert sum(c["PEATON"] == "GREEN" for c in colors) == 20
        assert sum(c["NS"] == "GREEN" for c in colors) == ns
        assert sum(c["EO"] == "GREEN" for c in colors) == 80-ns
        assert all(sum(c[g] in ("GREEN", "YELLOW") for g in ("NS", "EO", "PEATON")) <= 1 for c in colors)


def test_vehicle_conservation_and_saturation():
    sim = QueueSimulation()
    for second in range(1200):
        sim.tick(second, (2, 2), Timing(), second % 120)
    assert sim.arrivals == [2400, 2400]
    assert all(a-d == len(q) for a, d, q in zip(sim.arrivals, sim.departures, sim.queues))
    assert sum(map(len, sim.queues)) > 4000
