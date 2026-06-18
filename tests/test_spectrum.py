"""Tests for the solar spectrum and its integrals.

The two sentinel values here — 1000 W/m^2 integrated power and ~69 mA/cm^2 of
total photon current — fail loudly on any wavelength/energy unit slip, which is
the most likely class of bug in this code.
"""

import numpy as np

from solarlab.constants import Q
from solarlab.spectrum import SpectrumIntegrals, blackbody_spectrum, load_am15g


def test_am15g_integrated_power(spectrum):
    power = np.trapezoid(spectrum.values, spectrum.index.values)
    assert 995.0 <= power <= 1005.0  # true value 1000.37 W/m^2


def test_spectrum_shape(spectrum):
    wl = spectrum.index.values
    assert np.all(np.diff(wl) > 0)          # strictly increasing wavelength
    assert wl.min() <= 290 and wl.max() >= 3900
    assert np.all(spectrum.values >= 0)


def test_blackbody_fallback_normalised():
    bb = blackbody_spectrum()
    power = np.trapezoid(bb.values, bb.index.values)
    assert abs(power - 1000.0) < 1.0


def test_total_photon_current(spec):
    # All photons above 0.31 eV (lambda < 4000 nm) -> short-circuit current of a
    # hypothetical zero-gap cell, ~69 mA/cm^2.
    j = Q * float(spec.photon_flux_above(0.31))
    assert 640.0 <= j <= 740.0


def test_power_above_monotonic(spec):
    egs = np.linspace(0.5, 2.3, 50)
    p = spec.power_above(egs)
    assert np.all(np.diff(p) < 0)           # higher gap -> less power above it
    assert np.all(p <= spec.p_in_w_m2)


def test_source_recorded(spectrum):
    assert "source" in spectrum.attrs
    assert "G173" in spectrum.attrs["source"] or "blackbody" in spectrum.attrs["source"]
