"""Tests for the improvement-lever simulator."""

import pytest

from solarlab.levers import run_levers


@pytest.fixture(scope="module")
def levers(weather):
    return run_levers(weather=weather)


def test_at_least_eight_levers_all_cited(levers):
    assert len(levers) >= 8
    assert (levers["source"].astype(str).str.len() >= 10).all()


def test_levers_are_positive_improvements(levers):
    # Every lever here is a genuine improvement over the baseline.
    assert (levers["delta_pct"] > 0).all()


def test_technology_ranking(levers):
    d = levers.set_index("lever")["delta_pct"]
    tandem = d[[i for i in d.index if "tandem" in i.lower()]].iloc[0]
    hjt = d[[i for i in d.index if i.startswith("HJT")]].iloc[0]
    topcon = d[[i for i in d.index if i.startswith("TOPCon")]].iloc[0]
    assert tandem > hjt > topcon > 0


def test_tracking_gain_reasonable(levers):
    d = levers.set_index("lever")["delta_pct"]
    track = d[[i for i in d.index if "tracking" in i.lower()]].iloc[0]
    assert 8.0 <= track <= 30.0


def test_small_levers_bounded(levers):
    d = levers.set_index("lever")["delta_pct"]
    soiling = d[[i for i in d.index if "soiling" in i.lower()]].iloc[0]
    inverter = d[[i for i in d.index if "inverter" in i.lower()]].iloc[0]
    assert 0 < soiling <= 2.5
    assert 0 < inverter <= 4.0
