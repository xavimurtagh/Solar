"""Tests for the pyrite voltage roadmap (Part XIV)."""

from solarlab.pyrite import INTERVENTIONS, roadmap_summary, voltage_roadmap


def test_roadmap_climbs():
    df = voltage_roadmap()
    assert len(df) == len(INTERVENTIONS) == 5
    # Both efficiency and voltage rise monotonically up the ladder.
    assert df["eta"].is_monotonic_increasing
    assert df["voc_v"].is_monotonic_increasing
    assert df["ere"].is_monotonic_increasing


def test_endpoints_match_part_vi():
    s = roadmap_summary()
    assert s["today_eta"] < 0.10                # hopeless today
    assert s["final_eta"] > 0.20                # competitive after the full ladder
    assert s["final_voc"] > 0.55                # voltage recovered


def test_every_rung_has_a_mechanism():
    df = voltage_roadmap()
    assert (df["mechanism"].astype(str).str.len() > 20).all()
    # The decisive final step is carrier-selective contacts.
    assert "selective" in df.iloc[-1]["stage"].lower()
