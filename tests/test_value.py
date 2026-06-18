"""Tests for the value-of-time / value-deflation model (Part VII)."""

import numpy as np
import pytest

from solarlab.value import average_day_price, demand_profile, solar_shape, value_curve


@pytest.fixture(scope="module")
def curve(weather):
    return value_curve(weather=weather)


def test_solar_and_demand_normalised(weather):
    s = solar_shape(weather)
    d = demand_profile(s.index)
    assert s.mean() == pytest.approx(1.0, abs=1e-6)
    assert d.mean() == pytest.approx(1.0, abs=1e-6)
    assert len(s) == 8760


def test_solar_starts_above_average(curve):
    # At negligible penetration solar is worth MORE than the average kWh.
    assert curve.iloc[0]["value_factor"] > 1.0


def test_value_factor_collapses_with_penetration(curve):
    vf = curve.set_index((curve["penetration"] * 100).round().astype(int))["value_factor"]

    def at(pct):
        return vf.iloc[(vf.index - pct).to_series().abs().values.argmin()]

    assert at(10) > 0.85                       # still valuable when small
    assert 0.45 <= at(30) <= 0.70              # ~California today
    assert at(50) < 0.45                       # high-penetration collapse
    assert curve["value_factor"].is_monotonic_decreasing


def test_curtailment_rises_with_penetration(curve):
    assert curve.iloc[0]["curtailment"] == pytest.approx(0.0)
    assert curve.iloc[-1]["curtailment"] > 0.15    # lots spilled at high share
    assert curve["curtailment"].is_monotonic_increasing


def test_duck_curve_midday_crash(weather):
    day = average_day_price(0.45, weather=weather)
    midday = day[day["hour"].between(11, 14)]["price"].mean()
    evening = day[day["hour"].between(18, 20)]["price"].mean()
    assert evening > 3 * midday                 # evening peak dwarfs midday glut
    assert midday < 40                          # midday price has collapsed
