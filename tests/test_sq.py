"""Tests pinning the Shockley-Queisser core to published values.

Targets:
- peak ~33.7% at Eg ~1.34 eV (Ruehle, Solar Energy 130, 2016)
- silicon (1.12 eV) ~33%, GaAs (1.42 eV) ~33%
- the four losses + extraction sum to 1 to 1e-9
- the ideal 2-junction tandem ~45% near a 1.6 / 0.94 eV pair
"""

import numpy as np

from solarlab.sq import (
    j0_radiative,
    j0_radiative_numeric,
    loss_fractions,
    optimal_bandgap,
    optimal_tandem,
    sq_cell,
    sq_curve,
)


def test_peak_efficiency(spec):
    opt = optimal_bandgap(spec)
    assert 0.330 <= opt.eta <= 0.344
    assert 1.29 <= opt.eg_ev <= 1.40


def test_silicon(spec):
    si = sq_cell(1.12, spec)
    assert 0.315 <= si.eta <= 0.340
    assert 425.0 <= si.jsc_a_m2 <= 450.0     # ~43.8 mA/cm^2
    assert 0.84 <= si.voc_v <= 0.92


def test_gaas(spec):
    ga = sq_cell(1.42, spec)
    assert 0.320 <= ga.eta <= 0.339


def test_fill_factor_reasonable(spec):
    opt = optimal_bandgap(spec)
    assert 0.86 <= opt.ff <= 0.91


def test_j0_analytic_matches_numeric():
    for eg in (0.7, 1.12, 1.7, 2.3):
        a = j0_radiative(eg)
        n = j0_radiative_numeric(eg)
        assert abs(a - n) / n < 1e-5


def test_loss_closure(spec):
    for eg in (0.7, 1.12, 1.34, 1.7, 2.0):
        lf = loss_fractions(eg, spec)
        assert abs(sum(lf.values()) - 1.0) < 1e-9
        assert all(v >= -1e-12 for v in lf.values())


def test_silicon_loss_breakdown(spec):
    lf = loss_fractions(1.12, spec)
    assert 0.17 <= lf["below_gap"] <= 0.22         # ~19% sub-bandgap
    assert 0.28 <= lf["thermalisation"] <= 0.36    # ~33% thermalisation


def test_monotonic_trends(spec):
    df = sq_curve(spec, 0.6, 2.2, 0.01)
    assert np.all(np.diff(df["jsc_a_m2"].values) < 0)   # Jsc falls with Eg
    assert np.all(np.diff(df["voc_v"].values) > 0)      # Voc rises with Eg


def test_tandem(spec):
    t = optimal_tandem(spec)
    assert 0.44 <= t["eta"] <= 0.47
    assert 1.45 <= t["eg_top"] <= 1.80
    assert 0.85 <= t["eg_bot"] <= 1.10
    single = optimal_bandgap(spec).eta
    assert t["eta"] > single + 0.08
