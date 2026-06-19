"""Tests for the storage duration-bottleneck model (Part XVII)."""

import pytest

from solarlab import storage as ST


def test_lithium_wins_short_hydrogen_wins_long():
    short = ST.best_by_duration([4])["winner"].iloc[0]
    longd = ST.best_by_duration([2000])["winner"].iloc[0]
    assert "Lithium" in short                        # hours: lithium
    assert "Hydrogen" in longd                       # seasonal: hydrogen


def test_lithium_lcos_explodes_with_duration():
    li = ST.TECHS[0]
    assert "Lithium" in li.name
    short = ST.lcos(li, 4.0)
    season = ST.lcos(li, 2000.0)
    assert season > 20 * short                       # the long-duration cliff
    assert short < 200                               # ~$120/MWh at 4 h


def test_hydrogen_beats_lithium_for_seasons():
    h2 = next(t for t in ST.TECHS if "Hydrogen" in t.name)
    li = ST.TECHS[0]
    assert ST.lcos(h2, 2000.0) < ST.lcos(li, 2000.0)
    # ...but loses badly at short duration (its power cost dominates).
    assert ST.lcos(h2, 4.0) > ST.lcos(li, 4.0)


def test_cycles_fall_with_duration():
    assert ST.cycles_for_duration(4) == pytest.approx(365)     # daily-capped
    assert ST.cycles_for_duration(2000) < 10                   # seasonal: rare


def test_free_charging_flips_toward_cheap_capacity():
    # With free curtailed input, round-trip efficiency stops mattering and a
    # cheap-capacity tech wins even at a day's duration.
    winner_paid = ST.best_by_duration([24], charge_price=50.0)["winner"].iloc[0]
    winner_free = ST.best_by_duration([24], charge_price=0.0)["winner"].iloc[0]
    li_free = ST.lcos(ST.TECHS[0], 24.0, charge_price_usd_mwh=0.0)
    thermal = next(t for t in ST.TECHS if "Thermal" in t.name)
    assert ST.lcos(thermal, 24.0, charge_price_usd_mwh=0.0) < li_free


def test_power_energy_cost_split_is_the_framework():
    li = ST.TECHS[0]
    h2 = next(t for t in ST.TECHS if "Hydrogen" in t.name)
    # Lithium: cheap power, dear energy. Hydrogen: dear power, near-free energy.
    assert li.energy_cost_usd_kwh > h2.energy_cost_usd_kwh
    assert h2.power_cost_usd_kw > li.power_cost_usd_kw
