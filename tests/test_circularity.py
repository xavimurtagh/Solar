"""Tests for the circularity / urban-mine material-flow model."""

import numpy as np
import pytest

from solarlab import circularity as Z
from solarlab import constants as C


def test_weibull_survival_shape():
    shape, scale = C.PV_LIFETIME_WEIBULL["regular"]
    assert Z.weibull_survival(0, shape, scale) == pytest.approx(1.0)
    # At age == scale, S = exp(-1) ~= 0.368 for any shape.
    assert Z.weibull_survival(scale, shape, scale) == pytest.approx(np.exp(-1), abs=1e-6)
    ages = np.arange(0, 45)
    s = Z.weibull_survival(ages, shape, scale)
    assert np.all(np.diff(s) <= 1e-12)             # monotone non-increasing
    assert s[-1] < 0.05                            # nearly all retired by 44 yr


def test_retirement_fractions_sum_to_one():
    shape, scale = C.PV_LIFETIME_WEIBULL["regular"]
    ages = np.arange(0, 120)
    total = Z.retirement_fraction(ages, shape, scale).sum()
    assert total == pytest.approx(1.0, abs=1e-3)   # every panel eventually retires


def test_deployment_trajectory_reasonable():
    dep = Z.project_deployment(to_year=2050)
    cum2024 = dep.loc[dep["year"] == 2024, "cumulative_gw"].iloc[0] / 1000
    cum2050 = dep.loc[dep["year"] == 2050, "cumulative_gw"].iloc[0] / 1000
    assert 1.5 <= cum2024 <= 2.5                    # ~2 TW installed end-2024
    assert 50 <= cum2050 <= 90                      # net-zero-scale by 2050
    assert dep["annual_gw"].is_monotonic_increasing  # smooth projection


def test_urban_mine_mass_consistent():
    # Cumulative retired mass = retired GW * module mass; internally consistent
    # and far larger than IRENA's 2016 78 Mt because deployment outran 2016
    # forecasts.
    mass = Z.cumulative_recovered_mass_mt(2050)
    fleet = Z.fleet_flows(to_year=2050)
    retired_gw = fleet.loc[fleet["year"] <= 2050, "retired_gw"].sum()
    assert mass == pytest.approx(retired_gw * C.MODULE_MASS_T_PER_GW / 1e6, rel=1e-6)
    assert 150 <= mass <= 350                       # ~240 Mt for a ~62 TW world


def test_recycling_raises_ceiling_over_time():
    flow = Z.material_flow("TOPCon", "Silver", process="frelp", to_year=2080)
    # Circular ceiling is never below the linear one, and rises.
    assert (flow["ceiling_circular_tw"] >= flow["ceiling_linear_tw"] - 1e-9).all()
    c2030 = flow.loc[flow["year"] == 2030, "ceiling_circular_tw"].iloc[0]
    c2080 = flow.loc[flow["year"] == 2080, "ceiling_circular_tw"].iloc[0]
    assert c2080 > c2030 + 1.0                      # rises by >1 TW/yr


def test_frelp_recovers_silver_standard_does_not():
    frelp = Z.material_flow("TOPCon", "Silver", process="frelp", to_year=2080)
    standard = Z.material_flow("TOPCon", "Silver", process="standard", to_year=2080)
    assert frelp["secondary_t"].iloc[-1] > 0
    assert standard["secondary_t"].sum() == pytest.approx(0.0)
    # High-value recycling reaches a far higher circularity ratio.
    assert frelp["circularity"].max() > standard["circularity"].max()


def test_recycling_lags_growth_then_catches_up():
    flow = Z.material_flow("TOPCon", "Silver", process="frelp", to_year=2080)
    circ_2050 = flow.loc[flow["year"] == 2050, "circularity"].iloc[0]
    circ_2080 = flow.loc[flow["year"] == 2080, "circularity"].iloc[0]
    assert circ_2050 < 0.4                          # recycling lags during growth
    assert circ_2080 > circ_2050                    # catches up at steady state
    crossover = Z.circularity_crossover(flow, 0.5)
    assert crossover is not None and 2050 <= crossover <= 2075


def test_virgin_avoided_positive():
    avoided = Z.cumulative_virgin_avoided_t("TOPCon", "Silver", "frelp", to_year=2080)
    assert avoided > 100_000                        # >100 kt of silver never mined
