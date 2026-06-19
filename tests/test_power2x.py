"""Tests for the power-to-X / solar-as-feedstock model (Part IX)."""

import numpy as np
import pytest

from solarlab import power2x as PX


def test_lcoh_in_2026_range():
    # Dedicated solar electrolysis should land in the $2.50-5/kg range.
    assert 2.5 <= PX.lcoh(25.0, 0.25) <= 5.0
    assert 2.5 <= PX.lcoh(20.0, 0.30, electrolyzer_capex_per_kw=500) <= 5.0


def test_lcoh_rises_with_electricity_price():
    lo = PX.lcoh(10.0, 0.30)
    hi = PX.lcoh(60.0, 0.30)
    assert hi > lo
    # ~$10/MWh shifts LCOH by ~$0.5/kg (51 kWh/kg).
    assert PX.lcoh(30, 0.30) - PX.lcoh(20, 0.30) == pytest.approx(0.51, abs=0.02)


def test_low_utilisation_hurts():
    # An electrolyser idle most of the time can't amortise its capital, even on
    # cheap power.
    curtailed_only = PX.lcoh(5.0, 0.15)
    well_run = PX.lcoh(30.0, 0.45)
    assert curtailed_only > well_run


def test_glut_grows_with_penetration(weather):
    g30 = PX.glut_to_hydrogen(0.30, weather=weather)
    g60 = PX.glut_to_hydrogen(0.60, weather=weather)
    assert g60["curtailment_frac"] > g30["curtailment_frac"]
    assert g60["hydrogen_mt"] > g30["hydrogen_mt"] > 0


def test_flexible_demand_cuts_curtailment(weather):
    f = PX.flexible_demand_effect(0.50, flex_capacity=0.6, weather=weather)
    assert f["curtailment_flex"] < f["curtailment_base"]
    # Value factor should not fall when flexible demand absorbs the glut.
    assert f["value_factor_flex"] >= f["value_factor_base"] - 1e-6


def test_cheap_solar_unlocks_enduses():
    df = PX.enduse_unlock(20.0, 90.0)
    assert (df["elec_cost_cheap"] < df["elec_cost_grid"]).all()
    # Cheap solar electricity is below the market price of the product (viable);
    # grid power is not, for the energy-intensive ones.
    ammonia = df[df["product"] == "Green ammonia"].iloc[0]
    assert ammonia["elec_cost_cheap"] < ammonia["market_reference"]
    assert ammonia["elec_cost_grid"] > ammonia["market_reference"]
