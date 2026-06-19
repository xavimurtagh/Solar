"""Tests for the copper-vs-silver metallisation model (Part XII)."""

import pytest

from solarlab.metallization import (
    OPTIONS,
    breakeven_degradation,
    comparison,
    metal_lcoe,
)


def test_nominal_copper_marginally_cheaper_than_silver():
    df = comparison().set_index("name")
    silver = df.loc["Silver (screen-print)", "lcoe_usd_mwh"]
    copper = df.loc["Copper Ni/Cu (nominal)", "lcoe_usd_mwh"]
    assert copper < silver                              # copper wins...
    assert (silver - copper) / silver < 0.02            # ...but only barely (<2%)


def test_reliability_penalty_flips_the_result():
    df = comparison().set_index("name")
    silver = df.loc["Silver (screen-print)", "lcoe_usd_mwh"]
    cautious = df.loc["Copper (cautious reliability)", "lcoe_usd_mwh"]
    assert cautious > silver                            # a reliability slip loses


def test_breakeven_margin_is_thin():
    be = breakeven_degradation()
    # Copper can only tolerate a tiny extra degradation before losing on LCOE.
    assert 0 < be["extra_degradation_tolerated"] < 0.002    # < 0.2 pp/yr


def test_copper_metal_cost_below_silver():
    silver_cost = metal_lcoe(OPTIONS[0])["metal_cost_per_w"]
    copper_cost = metal_lcoe(OPTIONS[1])["metal_cost_per_w"]
    assert copper_cost < silver_cost                    # the headline saving is real
    assert silver_cost > 0.01                           # ~$11/kW of silver


def test_lcoe_is_in_realistic_band():
    for _, r in comparison().iterrows():
        assert 50 <= r["lcoe_usd_mwh"] <= 70            # utility-scale ballpark
