"""Tests for the multi-objective cost / space / scale frontier."""

import pytest

from solarlab.frontier import build_frontier, pareto_mask


@pytest.fixture(scope="module")
def frontier(weather):
    return build_frontier(weather=weather)


def test_frontier_covers_all_combinations(frontier):
    assert len(frontier) == 12                       # 4 technologies x 3 deployments
    assert frontier["lcoe_usd_mwh"].between(40, 200).all()
    assert (frontier["energy_density_kwh_m2_yr"] > 0).all()


def test_utility_cheaper_than_residential(frontier):
    util = frontier[frontier["deployment"] == "utility"]["lcoe_usd_mwh"].mean()
    res = frontier[frontier["deployment"] == "residential"]["lcoe_usd_mwh"].mean()
    assert util < res


def test_higher_efficiency_raises_energy_density(frontier):
    res = frontier[frontier["deployment"] == "residential"].sort_values("module_eff")
    densities = res["energy_density_kwh_m2_yr"].values
    assert all(b >= a for a, b in zip(densities, densities[1:]))


def test_two_objective_pareto_picks_tandem(frontier):
    # On cost vs space alone, the highest-efficiency utility option wins.
    opt = frontier[frontier["pareto"]]
    assert len(opt) >= 1
    assert "tandem" in opt.iloc[0]["technology"].lower()


def test_scale_objective_readmits_silicon(frontier):
    # Once scalability counts, silver/silicon cells (huge ceiling) rejoin the
    # frontier alongside the indium-limited tandem.
    scale_front = frontier[frontier["pareto_scale"]]
    techs = set(scale_front["technology"])
    assert len(scale_front) > frontier["pareto"].sum()
    assert any(t in techs for t in ("PERC", "TOPCon"))


def test_pareto_mask_simple_case():
    import pandas as pd
    df = pd.DataFrame({
        "cost": [1.0, 2.0, 1.0],
        "benefit": [2.0, 1.0, 1.0],
    })
    mask = pareto_mask(df, minimise=["cost"], maximise=["benefit"])
    assert mask.tolist() == [True, False, False]    # row 0 dominates row 2
