"""Colas discretas; capacidad fraccionaria, sin crear ni perder vehículos."""
from collections import deque

from .controller import Timing, phase


class QueueSimulation:
    def __init__(self, rates=(.5, .5)):
        self.queues = [deque(), deque()]
        self.credit = [0., 0.]
        self.rates = rates
        self.arrivals = [0, 0]
        self.departures = [0, 0]
        self.delay = 0
        self.served_wait = []

    def tick(self, second, arrivals, timing: Timing, cycle_second):
        colors = phase(timing, cycle_second)
        for i, code in enumerate(("NS", "EO")):
            self.queues[i].extend([second]*int(arrivals[i]))
            self.arrivals[i] += int(arrivals[i])
            if colors[code] == "GREEN":
                self.credit[i] += self.rates[i]
                capacity = int(self.credit[i])
                self.credit[i] -= capacity  # no acumular capacidad ociosa
                count = min(capacity, len(self.queues[i]))
                for _ in range(count):
                    self.served_wait.append(second-self.queues[i].popleft())
                self.departures[i] += count
            else:
                self.credit[i] = 0
            assert self.arrivals[i]-self.departures[i] == len(self.queues[i])
        queue = sum(map(len, self.queues))
        self.delay += queue
        return queue
