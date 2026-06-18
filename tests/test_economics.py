"""Tests for the LCOE engine, validated against published benchmarks."""

import numpy as np
import pytest

from solarlab.economics import (
    LCOEInputs,
    cost_stack,
    energy_per_dollar,
    lcoe,
    lcoe_monte_carlo,
    lcoe_sensitivity,
    opex_for,
    system_cost_per_w,
)


def test_cost_stacks_sum_to_benchmarks():
    assert 0.8 <= system_cost_per_w("utility") <= 1.3       # NREL ~$0.9-1.1/W
    assert 1.3 <= system_cost_per_w("commercial") <= 2.0
    assert 2.4 <= system_cost_per_w("residential") <= 3.3


def test_utility_lcoe_matches_lazard():
    # Lazard 2025 unsubsidised utility-scale solar: US$38-78/MWh.
    L = lcoe(system_cost_per_w("utility"), 1537,
             LCOEInputs(opex_per_kw_yr=opex_for("utility")))
    assert 0.030 <= L <= 0.075                                # $/kWh


def test_residential_lcoe_higher_than_utility():
    util = lcoe(system_cost_per_w("utility"), 1537,
                LCOEInputs(opex_per_kw_yr=opex_for("utility")))
    res = lcoe(system_cost_per_w("residential"), 1386,
              LCOEInputs(opex_per_kw_yr=opex_for("residential")))
    assert res > util
    assert 0.10 <= res <= 0.22


def test_lcoe_monotonic_drivers():
    base = lcoe(1.0, 1400)
    assert lcoe(0.7, 1400) < base                # cheaper system -> lower LCOE
    assert lcoe(1.0, 1800) < base                # more energy -> lower LCOE
    assert lcoe(1.0, 1400, LCOEInputs(discount_rate=0.09)) > base   # pricier capital
    assert lcoe(1.0, 1400, LCOEInputs(lifetime_years=40)) < base    # longer life


def test_energy_per_dollar_positive_and_intuitive():
    epd_util = energy_per_dollar(system_cost_per_w("utility"), 1537)
    epd_res = energy_per_dollar(system_cost_per_w("residential"), 1386)
    assert epd_util > epd_res > 0                # cheaper systems buy more kWh/$


def test_sensitivity_orders_by_swing():
    df = lcoe_sensitivity(1.0, 1400)
    assert list(df["swing"]) == sorted(df["swing"])     # ascending
    assert {"Installed cost", "Capacity factor / yield"} <= set(df["driver"])


def test_monte_carlo_distribution_reasonable():
    samples = lcoe_monte_carlo(1.0, 1400, n=3000, seed=0)
    assert len(samples) == 3000
    assert np.all(samples > 0)
    # Deterministic given the seed.
    again = lcoe_monte_carlo(1.0, 1400, n=3000, seed=0)
    assert np.allclose(samples, again)
