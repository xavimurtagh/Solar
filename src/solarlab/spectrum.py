"""The solar spectrum and fast integrals over it.

All integration happens in the **wavelength domain** (W/m^2 per nm).  This is a
deliberate choice: the temptation to convert the spectrum onto an energy grid
introduces the Jacobian ``|d(lambda)/dE| = h*c/E^2`` and is the single most
common source of bugs in Shockley-Queisser implementations.  By staying in
wavelength and computing photon energies pointwise we never need it.

Photon flux (photons / m^2 / s / nm) at wavelength ``lambda`` is

    phi(lambda) = S(lambda) / E_photon(lambda)

where ``S`` is spectral irradiance (W/m^2/nm) and ``E_photon = q * EV_NM /
lambda`` is the per-photon energy in joules.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .constants import C, EV_NM, H, Q


def load_am15g() -> pd.Series:
    """Return the ASTM G173-03 AM1.5 global spectrum.

    Index is wavelength in nm; values are spectral irradiance in W/m^2/nm.
    The integral over wavelength is ~1000.37 W/m^2 (the "one sun" reference).

    Falls back to a 5778 K blackbody normalised to 1000 W/m^2 if pvlib's
    bundled data cannot be loaded, recording which source was used in
    ``series.attrs['source']`` so the report can state it.
    """
    try:
        from pvlib import spectrum as _pvspec

        df = _pvspec.get_reference_spectra(standard="ASTM G173-03")
        s = df["global"].copy()
        s.index = s.index.astype(float)
        s.attrs["source"] = "ASTM G173-03 AM1.5G (via pvlib)"
        s.name = "spectral_irradiance_w_m2_nm"
        return s
    except Exception:  # pragma: no cover - exercised only without pvlib data
        s = blackbody_spectrum()
        s.attrs["source"] = "5778 K blackbody (fallback; pvlib data unavailable)"
        return s


def blackbody_spectrum(
    t_k: float = 5778.0,
    wl_nm: np.ndarray | None = None,
    total_w_m2: float = 1000.0,
) -> pd.Series:
    """A Planck blackbody spectral-irradiance *shape* normalised to ``total_w_m2``.

    Used only as a fallback / teaching reference.  ``t_k`` defaults to the Sun's
    effective photosphere temperature (5778 K).  The absolute scale of a true
    blackbody depends on solid angle, so we simply renormalise the integral to
    one sun (1000 W/m^2) over 280-4000 nm to match the AM1.5G convention.
    """
    if wl_nm is None:
        wl_nm = np.linspace(280.0, 4000.0, 2002)
    wl_m = wl_nm * 1e-9
    # Planck spectral radiance vs wavelength (arbitrary scale; renormalised).
    a = 2.0 * H * C**2 / wl_m**5
    b = H * C / (wl_m * 1.380649e-23 * t_k)
    radiance = a / np.expm1(b)
    shape = radiance / np.trapezoid(radiance, wl_nm)  # normalise area to 1
    s = pd.Series(shape * total_w_m2, index=pd.Index(wl_nm, name="wavelength"))
    s.name = "spectral_irradiance_w_m2_nm"
    return s


class SpectrumIntegrals:
    """Precomputed cumulative integrals for O(1) bandgap queries.

    Building this once turns every ``photon_flux_above(Eg)`` / ``power_above(Eg)``
    call into an interpolation, so scanning the full Shockley-Queisser curve and
    the 2-D tandem grid is effectively free.
    """

    def __init__(self, spectrum: pd.Series):
        wl = np.asarray(spectrum.index, dtype=float)        # nm
        s = np.asarray(spectrum.values, dtype=float)        # W/m^2/nm
        order = np.argsort(wl)
        self.wl = wl[order]
        self.s = s[order]

        # Per-photon energy in joules at each wavelength.
        e_photon_j = (EV_NM / self.wl) * Q                  # J
        # Photon flux density: (W/m^2/nm) / (J/photon) = photons/m^2/s/nm.
        self.phi = self.s / e_photon_j

        # Cumulative integrals from the short-wavelength (high-energy) edge.
        # cumulative_power[i] = integral of S over [wl[0], wl[i]].
        self._cum_power = _cumtrapz(self.s, self.wl)
        self._cum_flux = _cumtrapz(self.phi, self.wl)

        self.p_in_w_m2 = float(self._cum_power[-1])
        self._total_flux = float(self._cum_flux[-1])

        # Wavelength corresponding to each bandgap: lambda_g[nm] = EV_NM / Eg[eV].
        # Photons with energy >= Eg are those with wavelength <= lambda_g.

    def _cum_to(self, wl_cut: np.ndarray, cum: np.ndarray) -> np.ndarray:
        """Interpolated cumulative integral from wl[0] up to ``wl_cut``."""
        return np.interp(wl_cut, self.wl, cum, left=0.0, right=cum[-1])

    def photon_flux_above(self, eg_ev):
        """Photon flux (photons/m^2/s) with energy >= ``eg_ev``.

        Photons with energy >= Eg are exactly those with wavelength <=
        ``lambda_g = EV_NM / Eg``.  The cumulative integral of photon flux from
        the short-wavelength edge up to ``lambda_g`` is therefore the flux above
        the gap directly.
        """
        eg_ev = np.asarray(eg_ev, dtype=float)
        wl_cut = EV_NM / eg_ev                              # nm
        return self._cum_to(wl_cut, self._cum_flux)

    def power_above(self, eg_ev):
        """Incident power (W/m^2) carried by photons with energy >= ``eg_ev``."""
        eg_ev = np.asarray(eg_ev, dtype=float)
        wl_cut = EV_NM / eg_ev
        return self._cum_to(wl_cut, self._cum_power)


def _cumtrapz(y: np.ndarray, x: np.ndarray) -> np.ndarray:
    """Cumulative trapezoidal integral with a leading zero (length preserved)."""
    out = np.zeros_like(y, dtype=float)
    out[1:] = np.cumsum(0.5 * (y[1:] + y[:-1]) * np.diff(x))
    return out
