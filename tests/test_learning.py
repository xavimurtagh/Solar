"""Tests for the Wright's-law learning-curve model (Part XI)."""

import pytest

from solarlab.learning import (
    fit_learning_rate,
    milestone_years,
    project_lcoe,
    project_module_price,
)


def test_learning_rate_plausible():
    fit = fit_learning_rate()
    # Module learning rate is high over 2010-2024 (manufacturing glut); the
    # long-run figure is ~24%. Accept the fitted window.
    assert 0.18 <= fit["learning_rate"] <= 0.42
    assert fit["b"] < 0                         # price falls with cumulative volume
    assert fit["r2"] > 0.9                      # the law fits tightly


def test_module_price_falls_over_time():
    proj = project_module_price()
    p = proj.set_index("year")["module_price_usd_per_w"]
    assert p.loc[2050] < p.loc[2024] < p.loc[2010]
    assert p.loc[2050] < 0.05                   # module heads toward near-free


def test_lcoe_falls_then_floors():
    proj = project_lcoe().set_index("year")
    assert proj.loc[2050, "lcoe_usd_mwh"] < proj.loc[2024, "lcoe_usd_mwh"]
    # The decline decelerates: 2040->2050 drop is much smaller than 2024->2034.
    early = proj.loc[2024, "lcoe_usd_mwh"] - proj.loc[2034, "lcoe_usd_mwh"]
    late = proj.loc[2040, "lcoe_usd_mwh"] - proj.loc[2050, "lcoe_usd_mwh"]
    assert late < early                         # balance-of-system floors LCOE


def test_lcoe_reaches_cheap_but_not_zero():
    proj = project_lcoe().set_index("year")
    assert 15 <= proj.loc[2050, "lcoe_usd_mwh"] <= 35   # cheapest energy ever, not free


def test_milestones_are_ordered():
    proj = project_lcoe()
    ms = milestone_years(proj)
    years = [y for y in ms.values() if y]
    assert years == sorted(years)               # cheaper thresholds crossed later
