"""Tests for the non-ideal (ERE) pyrite voltage model."""

import numpy as np
import pytest

from solarlab import constants as C
from solarlab.spectrum import SpectrumIntegrals, load_am15g
from solarlab.sq import ere_sweep, sq_cell, voc_deficit


@pytest.fixture(scope="module")
def spec():
    return SpectrumIntegrals(load_am15g())


def test_ere_one_recovers_shockley_queisser(spec):
    # ere=1 must reproduce the ideal SQ cell exactly (Part I unchanged).
    a = sq_cell(1.12, spec, ere=1.0)
    b = sq_cell(1.12, spec)
    assert a.eta == pytest.approx(b.eta)
    assert 0.33 <= a.eta <= 0.34


def test_voc_falls_with_ere(spec):
    eg = C.PYRITE_EG_EV
    high = sq_cell(eg, spec, ere=1.0).voc_v
    low = sq_cell(eg, spec, ere=1e-9).voc_v
    assert low < high
    # Each decade of ERE costs ~kT*ln(10) ~= 0.0595 V.
    drop = sq_cell(eg, spec, ere=1e-2).voc_v - sq_cell(eg, spec, ere=1e-3).voc_v
    assert drop == pytest.approx(0.0595, abs=0.005)


def test_pyrite_today_is_hopeless(spec):
    today = sq_cell(C.PYRITE_EG_EV, spec, ere=C.PYRITE_ERE_TODAY)
    assert today.voc_v < 0.25                      # observed ~0.2 V collapse
    assert today.eta < 0.10                        # single-digit efficiency


def test_pyrite_radiative_ceiling_is_high(spec):
    rad = sq_cell(C.PYRITE_EG_EV, spec, ere=1.0)
    assert 0.28 <= rad.eta <= 0.33                 # ~31% if defects were gone


def test_passivation_unlocks_the_prize(spec):
    passivated = sq_cell(C.PYRITE_EG_EV, spec, ere=C.PYRITE_ERE_PASSIVATED)
    assert passivated.eta > 0.20                   # competitive with silicon
    today = sq_cell(C.PYRITE_EG_EV, spec, ere=C.PYRITE_ERE_TODAY)
    assert passivated.eta > 3 * today.eta          # curing voltage multiplies output


def test_voc_deficit_is_large(spec):
    assert voc_deficit(C.PYRITE_EG_EV, spec, C.PYRITE_ERE_TODAY) > 0.4


def test_ere_sweep_monotonic(spec):
    df = ere_sweep(C.PYRITE_EG_EV, spec)
    assert (np.diff(df["eta"].values) >= -1e-9).all()    # efficiency rises with ERE
    assert (np.diff(df["voc_v"].values) >= -1e-9).all()  # so does Voc
