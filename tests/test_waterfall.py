"""Tests for the sun-to-AC efficiency waterfall."""

import pytest

from solarlab import constants as C
from solarlab.sq import sq_cell
from solarlab.waterfall import build_waterfall, validate_waterfall


def test_waterfall_descends_to_system(spec, base_sim):
    df = build_waterfall(spec, base_sim)
    eta = df["eta_pct"].values
    assert eta[0] == 100.0
    assert all(b < a for a, b in zip(eta, eta[1:]))   # strictly decreasing
    assert 15.0 <= eta[-1] <= 21.0


def test_waterfall_stages_match_sources(spec, base_sim):
    df = build_waterfall(spec, base_sim).set_index("stage")
    # SQ rung equals the computed silicon detailed-balance efficiency.
    sq_si = sq_cell(C.SI_EG_EV, spec).eta * 100.0
    assert abs(df.loc["Shockley-Queisser limit (Si)", "eta_pct"] - sq_si) < 0.2
    # Auger rung is the cited Richter limit.
    assert df.loc["Practical Si cell limit", "eta_pct"] == C.RICHTER_SI_LIMIT_PCT
    # Final rung equals module_eff * PR.
    expected = base_sim.scenario.module_eff * base_sim.pr * 100.0
    assert abs(df.loc["Deployed system (annual AC)", "eta_pct"] - expected) < 0.01


def test_every_stage_cited(spec, base_sim):
    df = build_waterfall(spec, base_sim)
    assert (df["source"].astype(str).str.len() >= 10).all()


def test_validate_rejects_bad_ladder():
    import pandas as pd
    bad = pd.DataFrame({"eta_pct": [100.0, 20.0, 25.0]})   # not decreasing
    with pytest.raises(ValueError):
        validate_waterfall(bad)
