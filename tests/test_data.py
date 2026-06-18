"""Tests for the curated datasets and their analysis."""

import pytest

from solarlab.history import (
    improvement_stats,
    lab_to_market_gap,
    load_milestones,
    load_module_market,
    load_technologies,
    validate_milestones,
)


def test_milestones_schema_and_citations():
    df = load_milestones()
    validate_milestones(df)  # must not raise
    assert (df["source"].astype(str).str.len() >= 15).all()
    assert df["year"].between(1950, 2026).all()
    assert df["efficiency_pct"].between(0, 50).all()


def test_key_records_present():
    df = load_milestones()
    si = df[(df["technology"] == "Silicon") & (df["kind"] == "cell")]
    assert si["efficiency_pct"].max() >= 27.8         # current Si lab record
    tandem = df[df["technology"] == "Perovskite-Si tandem"]
    assert tandem["efficiency_pct"].max() >= 34.5      # tandem record
    conc = df[df["technology"] == "III-V multijunction"]
    assert conc["efficiency_pct"].max() >= 47.0        # overall record


def test_record_series_non_decreasing():
    df = load_milestones()
    for tech in ("Silicon", "Perovskite", "Perovskite-Si tandem"):
        cells = df[(df["technology"] == tech) & (df["kind"] == "cell")]
        cells = cells.sort_values("year")
        vals = cells["efficiency_pct"].values
        assert all(b >= a - 1e-9 for a, b in zip(vals, vals[1:]))


def test_market_trends():
    m = load_module_market().sort_values("year")
    assert all(b >= a for a, b in zip(m["avg_module_eff_pct"], m["avg_module_eff_pct"][1:]))
    assert all(b <= a for a, b in zip(m["module_price_usd_per_w"], m["module_price_usd_per_w"][1:]))


def test_improvement_stats():
    stats = improvement_stats()
    assert "pp_per_decade" in stats.columns
    si = stats[stats["technology"] == "Silicon"].iloc[0]
    assert si["pp_per_decade"] > 0


def test_lab_to_market_gap():
    gap = lab_to_market_gap()
    assert gap["gap_pp"] > 0
    assert gap["best_cell_pct"] > gap["market_pct"]


def test_technologies_table():
    t = load_technologies()
    assert {"technology", "module_eff_frac", "gamma_pdc_per_c"} <= set(t.columns)
    assert t["module_eff_frac"].between(0.15, 0.30).all()
    assert (t["gamma_pdc_per_c"] < 0).all()           # power falls with temperature
