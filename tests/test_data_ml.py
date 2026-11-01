from datetime import UTC, datetime

import numpy as np
import pandas as pd
import pytest

from ml_model.synthetic import FEATURES, dataset, features, live_minute
from ml_model.train_model import temporal_split
from backend.app.schemas import Observation
from backend.app.waze_adapter import normalize_jam


def test_generator_reproducible_temporal_purge_and_feature_parity():
    frame = dataset(5, 123, intersections=1)
    pd.testing.assert_frame_equal(frame, dataset(5, 123, intersections=1))
    train, valid, test = temporal_split(frame, 5)
    assert train["at"].max()+pd.Timedelta(minutes=5) < valid["at"].min()
    assert valid["at"].max()+pd.Timedelta(minutes=5) < test["at"].min()
    row = frame.iloc[200]
    history = [int(x) for x in frame[(frame.direction == row.direction) &
              (frame["at"] <= row["at"])].tail(5).last_vpm]
    actual = features(row["at"].to_pydatetime(), ("clear", "rain", "heavy_rain")[int(row.weather)],
                      history, row.speed_kmh, 1, "EO" if row.direction else "NS")
    np.testing.assert_allclose([actual[k] for k in FEATURES], row[FEATURES].astype(float), atol=1e-12)
    at = datetime(2026, 1, 1, tzinfo=UTC)
    np.testing.assert_array_equal(live_minute(at, 1, "NS", 4)[0], live_minute(at, 1, "NS", 4)[0])


def test_waze_retains_missing_counts_and_weather():
    raw = normalize_jam({"speed": 5, "uuid": "test"}, 1, datetime(2026, 1, 1, tzinfo=UTC))
    obs = Observation.model_validate(raw)
    assert obs.arrivals is None and obs.weather is None and obs.speed_kmh == 18
    with pytest.raises(ValueError):
        Observation.model_validate({**raw, "arrivals": 10})


@pytest.mark.parametrize("variant", ["naive", "duration", "unaligned", "weather"])
def test_observation_window_contract(variant):
    from datetime import timedelta
    start = datetime(2026, 1, 1, tzinfo=UTC)
    raw = {"group_id": 1, "window_start": start, "window_end": start+timedelta(minutes=1),
           "arrivals": 10, "speed_kmh": 30, "weather": "clear", "source": "synthetic"}
    if variant == "naive":
        raw.update(window_start=start.replace(tzinfo=None),
                   window_end=(start+timedelta(minutes=1)).replace(tzinfo=None))
    elif variant == "duration":
        raw["window_end"] = start+timedelta(minutes=2)
    elif variant == "unaligned":
        raw.update(window_start=start+timedelta(seconds=1), window_end=start+timedelta(seconds=61))
    else:
        raw["weather"] = None
    with pytest.raises(ValueError):
        Observation.model_validate(raw)
