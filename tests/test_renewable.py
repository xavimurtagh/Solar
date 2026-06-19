"""Tests for the truly-renewable / closed-loop model (Part XIII)."""

import pytest

from solarlab.renewable import (
    closed_loop_fraction,
    renewability_verdict,
    runway_scenarios,
    steady_state,
)


def test_closed_loop_fraction():
    cl = closed_loop_fraction(0.9, 0.95, 0.99)
    assert 0.80 <= cl <= 0.90
    # A leaky collection rate drops the closed-loop fraction a lot.
    assert closed_loop_fraction(collection=0.5) < cl


def test_silver_without_recycling_runs_out():
    ss = steady_state("Silver", 13.0, fleet_tw=50.0, closed_loop=0.0)
    assert ss.runway_years < 60                        # a resource cliff
    assert ss.virgin_share_of_production > 0.5         # eats most of world supply


def test_recycling_transforms_silver():
    none = steady_state("Silver", 13.0, fleet_tw=50.0, closed_loop=0.0)
    tight = steady_state("Silver", 13.0, fleet_tw=50.0)  # default ~0.85 loop
    assert tight.runway_years > 3 * none.runway_years   # centuries vs decades
    assert tight.virgin_share_of_production < 0.25      # back within means


def test_copper_is_effectively_unlimited():
    ss = steady_state("Copper", 15.0, fleet_tw=50.0)
    assert ss.runway_years > 1000
    assert ss.virgin_share_of_production < 0.01         # trivial slice of copper


def test_verdict_orders_the_paths():
    v = renewability_verdict()
    assert v["silver_no_recycle_runway"] < v["silver_tight_runway"] < v["copper_runway"]


def test_runway_table_complete():
    df = runway_scenarios()
    assert len(df) == 4
    assert {"scenario", "runway_years", "virgin_share_of_production"} <= set(df.columns)
