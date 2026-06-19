"""Tests for the space-solar deep-dive (Part XV)."""

import pytest

from solarlab import spacedeep as SD


def test_beaming_chain_realistic():
    bc = SD.beaming_chain()
    end = bc["cumulative_eff"].iloc[-1]
    assert 0.45 <= end <= 0.70                  # ~60% orbit-to-grid
    assert bc["cumulative_eff"].is_monotonic_decreasing


def test_launch_carbon_pays_back_fast():
    c = SD.launch_carbon()
    assert c["carbon_payback_years"] < 1.0       # months, not years
    assert c["co2_intensity_g_per_kwh"] < 50     # cleaner per kWh than fossil grid


def test_scalability_caps_sbsp_at_a_slice():
    s1 = SD.scalability(1.0)
    sworld = SD.scalability(SD.WORLD_POWER_TW)
    # 1 TW is heroic; the whole world is absurd.
    assert 5 <= s1["launches_per_day"] <= 30
    assert sworld["launches_per_day"] > 100
    assert sworld["mass_to_orbit_mt"] > 100


def test_rectenna_area_scales():
    a1 = SD.rectenna_area_km2(1000.0)            # 1 TW
    a10 = SD.rectenna_area_km2(10000.0)          # 10 TW
    assert a10 == pytest.approx(10 * a1)
    assert a1 > 1000                             # thousands of km^2


def test_scalability_curve_monotonic():
    df = SD.scalability_curve()
    assert df["launches_per_day"].is_monotonic_increasing
