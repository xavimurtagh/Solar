"""Tests for the techno-economic optimiser."""

import pytest

from solarlab.frontier import build_frontier
from solarlab.optimizer import Constraints, evaluate, optimize


@pytest.fixture(scope="module")
def frontier(weather):
    return build_frontier(weather=weather)


def test_area_limited_favours_efficiency(frontier):
    # On a fixed roof, the most efficient cell should win.
    res = optimize("max_energy",
                   Constraints(area_m2=40, budget_usd=80_000, deployment="residential"),
                   frontier_df=frontier)
    assert res["binding"] == "area"
    assert "tandem" in res["best"]["technology"].lower()


def test_budget_limited_favours_cheap(frontier):
    # With money the constraint and land ample, the cheapest cell wins on total
    # energy (more capacity per dollar).
    res = optimize("max_energy",
                   Constraints(budget_usd=1_000_000, area_m2=1e9, deployment="utility"),
                   frontier_df=frontier)
    assert res["binding"] == "budget"
    assert res["best"]["technology"] == "PERC"


def test_optimal_flips_between_scenarios(frontier):
    area = optimize("max_energy",
                    Constraints(area_m2=40, budget_usd=80_000, deployment="residential"),
                    frontier_df=frontier)["best"]["technology"]
    budget = optimize("max_energy",
                      Constraints(budget_usd=1_000_000, area_m2=1e9, deployment="utility"),
                      frontier_df=frontier)["best"]["technology"]
    assert area != budget                       # the winner genuinely flips


def test_min_lcoe_objective(frontier):
    res = optimize("min_lcoe", Constraints(), frontier_df=frontier)
    assert res["best"]["lcoe_usd_mwh"] == res["ranked"]["lcoe_usd_mwh"].min()


def test_min_cost_for_target(frontier):
    res = optimize("min_cost_for_target",
                   Constraints(target_kwh=10_000, area_m2=60, deployment="residential"),
                   frontier_df=frontier)
    assert res["feasible"]
    assert res["best"]["annual_kwh"] == pytest.approx(10_000)
    assert res["best"]["area_needed_m2"] <= 60

    # A tiny roof makes the target infeasible.
    tiny = optimize("min_cost_for_target",
                    Constraints(target_kwh=10_000, area_m2=5, deployment="residential"),
                    frontier_df=frontier)
    assert not tiny["feasible"]


def test_evaluate_reports_binding(frontier):
    df = evaluate(frontier, Constraints(area_m2=30, budget_usd=1e9))
    assert (df["binding"] == "area").all()
    assert (df["capacity_kw"] > 0).all()
