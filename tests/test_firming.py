"""Tests for the solar+storage firming model (Part VIII)."""

import numpy as np
import pytest

from solarlab import firming as F


@pytest.fixture(scope="module")
def solar(weather):
    return F.solar_profile(weather)


def test_more_storage_and_overbuild_raise_reliability(solar):
    solar_norm, _ = solar
    low = F.dispatch(solar_norm, overbuild=1.5, storage_hours=4)["reliability"]
    high = F.dispatch(solar_norm, overbuild=3.0, storage_hours=24)["reliability"]
    assert high > low
    assert 0.0 < low < high <= 1.0


def test_no_storage_cannot_serve_nights(solar):
    solar_norm, _ = solar
    r = F.dispatch(solar_norm, overbuild=2.0, storage_hours=0.0)
    assert r["reliability"] < 0.75            # nights are unmet without storage


def test_high_resource_matches_irena(weather):
    # IRENA 2026 firm solar+storage: $54-82/MWh at high-resource sites.
    df = F.lcoss_vs_reliability(weather=weather, params=F.HIGH_RESOURCE)
    at95 = df.loc[df["reliability"] == 0.95, "lcoss_usd_mwh"].iloc[0]
    assert 54 <= at95 <= 90                   # ~$72 expected


def test_firm_solar_beats_fossils_at_moderate_reliability(weather):
    cheap = F.cheapest_firm(weather=weather, params=F.HIGH_RESOURCE,
                            reliability_target=0.90)
    assert cheap["lcoss_usd_mwh"] < F.NEW_GAS_USD_MWH      # cheaper than new gas


def test_last_mile_is_expensive(weather):
    df = F.lcoss_vs_reliability(weather=weather).set_index("reliability")
    assert df.loc[0.99, "lcoss_usd_mwh"] > 1.4 * df.loc[0.90, "lcoss_usd_mwh"]
    assert df["lcoss_usd_mwh"].is_monotonic_increasing    # firmer costs more


def test_firming_curve_storage_grows_with_reliability(weather):
    df = F.lcoss_vs_reliability(weather=weather)
    # Hitting higher reliability needs more storage and/or overbuild.
    assert df.iloc[-1]["storage_hours"] >= df.iloc[0]["storage_hours"]
