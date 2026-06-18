"""Tests for land-use efficiency, LER, and the diurnal grid-value profile."""

import numpy as np
import pytest

from solarlab.landuse import ARCHETYPES, average_day_profile, land_metrics


@pytest.fixture(scope="module")
def metrics(weather):
    return land_metrics(weather=weather)


def test_all_archetypes_present(metrics):
    assert len(metrics) == len(ARCHETYPES) == 4
    assert (metrics["energy_per_land_m2"] > 0).all()


def test_agrivoltaics_beats_single_use(metrics):
    m = metrics.set_index("archetype")
    assert m.loc["Agrivoltaics", "ler"] > 1.0           # dual-use wins
    assert 1.2 <= m.loc["Agrivoltaics", "ler"] <= 1.8    # literature range


def test_reference_is_ler_one(metrics):
    m = metrics.set_index("archetype")
    assert m.loc["Ground-mount (reference)", "ler"] == pytest.approx(1.0)


def test_floating_cooling_lifts_yield(metrics):
    m = metrics.set_index("archetype")
    assert (m.loc["Floating PV", "specific_yield"]
            > m.loc["Ground-mount (reference)", "specific_yield"])
    assert not m.loc["Floating PV", "uses_land"]          # water, not land


def test_vertical_yield_is_slightly_below_optimal(metrics):
    m = metrics.set_index("archetype")
    ratio = (m.loc["Vertical bifacial E-W", "specific_yield"]
             / m.loc["Ground-mount (reference)", "specific_yield"])
    assert 0.85 <= ratio <= 1.0                           # a few % below optimal tilt
    assert m.loc["Vertical bifacial E-W", "ler"] > 1.5    # but high dual-use value


def test_vertical_diurnal_is_shoulder_peaked(weather):
    prof = average_day_profile(weather=weather)
    fixed = prof["fixed_optimal"].values
    vert = prof["vertical_ew"].values
    # Fixed peaks at midday; vertical dips at midday relative to its shoulders.
    assert 11 <= int(np.argmax(fixed)) <= 13
    assert vert[12] < max(vert[9], vert[16])             # midday below morning/evening
