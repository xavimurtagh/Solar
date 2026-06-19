"""Tests for the panel-collection problem (Part XVI)."""

import pytest

from solarlab import collection as COL


def test_collection_is_the_binding_constraint():
    df = COL.runway_vs_collection().set_index(
        (COL.runway_vs_collection()["collection"] * 100).round().astype(int))
    # Below ~50% collection the runway is barely above the no-recycle cliff.
    low = df.loc[20, "runway_years"]
    high = df.loc[85, "runway_years"]
    assert low < 50                              # ~global reality: still a cliff
    assert high > 2.5 * low                      # collection is the swing variable
    assert df["runway_years"].is_monotonic_increasing


def test_recovered_value_dominated_by_metals():
    v = COL.recovered_value_per_tonne().set_index("material")
    assert v.loc["Silver", "value_usd"] > 100    # silver is a big share by value
    assert v.loc["Silver", "kg_per_tonne"] < 1   # ...from a tiny mass (~0.2 kg/t)
    total = v["value_usd"].sum()
    assert 350 <= total <= 750                    # ~$500/tonne recoverable


def test_recycling_is_net_positive_but_loses_to_landfill():
    e = COL.recycling_economics()
    assert e.net_value_t > 0                       # recovery pays, in principle
    assert e.landfill_cost_t < e.recycle_cost_t    # ...but dumping is cheaper
    assert e.incentive_gap_t > 0


def test_copper_era_erodes_the_recycling_incentive():
    df = COL.silver_thrift_effect().set_index("silver_mg_per_w")
    assert df.loc[0.0, "net_value_t"] < df.loc[13.0, "net_value_t"]
    # Removing silver cuts the recovery margin sharply.
    assert df.loc[0.0, "net_value_t"] < 0.5 * df.loc[13.0, "net_value_t"]


def test_regional_rates_span_the_problem():
    assert COL.REGIONAL_COLLECTION["EU (WEEE mandate)"] > 0.5
    assert COL.REGIONAL_COLLECTION["Global average"] < 0.4
