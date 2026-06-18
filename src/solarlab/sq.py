"""The Shockley-Queisser detailed-balance limit — the physics ceiling.

This module answers the user's first question, *"why are panels only ~20%
efficient?"*, from first principles.  In 1961 Shockley and Queisser showed that
even a flawless single-junction cell is bounded by four unavoidable losses:

1. **Sub-bandgap transmission** — photons with energy below the bandgap ``Eg``
   are not absorbed at all (~19% of the incident energy for silicon).
2. **Thermalisation** — a photon with energy ``E > Eg`` excites a carrier that
   immediately relaxes to the band edge, wasting ``E - Eg`` as heat (~33% for
   silicon).
3. **Boltzmann / thermodynamic voltage loss** — the open-circuit voltage is
   strictly below ``Eg/q`` because the cell must also emit thermal radiation
   (detailed balance).
4. **Fill-factor loss** — the current-voltage curve is not a perfect rectangle.

What remains is ~33.7% at the optimal bandgap (1.34 eV) and ~32% for silicon.
The four losses plus the extracted power sum to exactly 100% of the incident
energy — which the test-suite checks to 1e-9.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import minimize_scalar

from .constants import C, H, K_B, Q, T_CELL
from .spectrum import SpectrumIntegrals


@dataclass(frozen=True)
class SQResult:
    """The complete operating point of a detailed-balance cell at one bandgap."""

    eg_ev: float
    jsc_a_m2: float      # short-circuit current density, A/m^2
    j0_a_m2: float       # radiative dark saturation current, A/m^2
    voc_v: float         # open-circuit voltage, V
    vmp_v: float         # voltage at maximum power, V
    jmp_a_m2: float      # current at maximum power, A/m^2
    ff: float            # fill factor, dimensionless
    eta: float           # efficiency, fraction of incident power
    p_in_w_m2: float     # incident power, W/m^2


def j0_radiative(eg_ev: float, t_k: float = T_CELL) -> float:
    """Radiative dark-saturation current density (A/m^2) from detailed balance.

    A cell at temperature ``t_k`` emits thermal photons.  In the dark, the rate
    of radiative emission above the bandgap sets the reverse saturation current
    ``J0``.  Integrating the blackbody photon flux from ``Eg`` to infinity under
    the Boltzmann approximation ``exp(E/kT) - 1 ~= exp(E/kT)`` (exact to better
    than 1e-18 for Eg >= 1 eV) gives the closed form used here:

        J0 = (2*pi*q / (h^3 c^2)) * kT * exp(-Eg/kT)
                 * (Eg^2 + 2*Eg*kT + 2*(kT)^2)

    with ``Eg`` and ``kT`` in joules.  This is the single-face emission
    convention (perfect rear mirror) that reproduces the canonical 33.7% limit.
    """
    kt_j = K_B * t_k
    eg_j = eg_ev * Q
    prefactor = 2.0 * np.pi * Q / (H**3 * C**2)
    poly = eg_j**2 + 2.0 * eg_j * kt_j + 2.0 * kt_j**2
    return prefactor * kt_j * np.exp(-eg_j / kt_j) * poly


def j0_radiative_numeric(eg_ev: float, t_k: float = T_CELL) -> float:
    """Same quantity as :func:`j0_radiative`, by direct numerical quadrature.

    Kept as an independent cross-check for the test-suite — it integrates the
    full Bose-Einstein blackbody flux (the ``-1`` is retained) rather than the
    Boltzmann approximation.
    """
    kt_j = K_B * t_k
    eg_j = eg_ev * Q
    # Integrate E^2 / (exp(E/kT) - 1) from Eg to Eg + 60 kT (tail is negligible).
    e = np.linspace(eg_j, eg_j + 60.0 * kt_j, 20000)
    integrand = e**2 / np.expm1(e / kt_j)
    integral = np.trapezoid(integrand, e)
    prefactor = 2.0 * np.pi * Q / (H**3 * C**2)
    return prefactor * integral


def solve_cell(jsc: float, j0: float, t_k: float = T_CELL):
    """Solve the ideal diode for (Voc, Vmp, Jmp, FF).

    The cell obeys ``J(V) = Jsc - J0*(exp(qV/kT) - 1)``.  Open circuit (J=0)
    gives ``Voc = (kT/q) ln(Jsc/J0 + 1)``; the maximum-power point is found by
    maximising ``P(V) = V * J(V)`` on ``[0, Voc]``.
    """
    vth = K_B * t_k / Q  # thermal voltage, V
    voc = vth * np.log(jsc / j0 + 1.0)

    def neg_power(v: float) -> float:
        j = jsc - j0 * np.expm1(v / vth)
        return -(v * j)

    res = minimize_scalar(neg_power, bounds=(0.0, voc), method="bounded",
                          options={"xatol": 1e-9})
    vmp = float(res.x)
    jmp = jsc - j0 * np.expm1(vmp / vth)
    ff = (vmp * jmp) / (voc * jsc)
    return voc, vmp, jmp, ff


def sq_cell(eg_ev: float, spec: SpectrumIntegrals, t_k: float = T_CELL) -> SQResult:
    """Full Shockley-Queisser operating point at bandgap ``eg_ev``.

    Assumes unity quantum efficiency: every photon with ``E >= Eg`` produces one
    collected electron, so ``Jsc = q * (photon flux above Eg)``.
    """
    jsc = Q * float(spec.photon_flux_above(eg_ev))
    j0 = j0_radiative(eg_ev, t_k)
    voc, vmp, jmp, ff = solve_cell(jsc, j0, t_k)
    eta = (vmp * jmp) / spec.p_in_w_m2
    return SQResult(
        eg_ev=float(eg_ev), jsc_a_m2=jsc, j0_a_m2=j0, voc_v=voc, vmp_v=vmp,
        jmp_a_m2=jmp, ff=ff, eta=eta, p_in_w_m2=spec.p_in_w_m2,
    )


def sq_curve(spec: SpectrumIntegrals, eg_min: float = 0.5, eg_max: float = 2.3,
             step: float = 0.005):
    """Efficiency (and Jsc, Voc, FF) versus bandgap across the usable range.

    Returns a :class:`pandas.DataFrame`.  A fine, global grid is used rather
    than a local optimiser because the AM1.5G spectrum's water-absorption bands
    put small local maxima near 1.1 and 1.3 eV.
    """
    import pandas as pd

    egs = np.arange(eg_min, eg_max + 0.5 * step, step)
    rows = [sq_cell(eg, spec) for eg in egs]
    return pd.DataFrame(
        {
            "eg_ev": [r.eg_ev for r in rows],
            "eta": [r.eta for r in rows],
            "jsc_a_m2": [r.jsc_a_m2 for r in rows],
            "voc_v": [r.voc_v for r in rows],
            "ff": [r.ff for r in rows],
        }
    )


def optimal_bandgap(spec: SpectrumIntegrals) -> SQResult:
    """The single-junction bandgap that maximises efficiency (global scan)."""
    df = sq_curve(spec, 0.5, 2.3, 0.002)
    best = df.loc[df["eta"].idxmax(), "eg_ev"]
    return sq_cell(float(best), spec)


def loss_fractions(eg_ev: float, spec: SpectrumIntegrals,
                   t_k: float = T_CELL) -> dict:
    """Decompose 100% of incident energy into the four losses plus extraction.

    By construction the five returned fractions sum to exactly 1.0:

        below_gap + thermalisation + voltage_boltzmann + fill_factor
            + extracted == 1.0
    """
    p_in = spec.p_in_w_m2
    cell = sq_cell(eg_ev, spec, t_k)
    eg_j = eg_ev * Q

    p_abs = float(spec.power_above(eg_ev))             # absorbed (above-gap) power
    p_after_thermal = cell.jsc_a_m2 * (eg_j / Q)       # = N * Eg, post-thermalisation
    p_at_voc = cell.jsc_a_m2 * cell.voc_v              # Jsc * Voc envelope
    p_max = cell.vmp_v * cell.jmp_a_m2                 # extracted power

    below_gap = (p_in - p_abs) / p_in
    thermalisation = (p_abs - p_after_thermal) / p_in
    voltage_boltzmann = (p_after_thermal - p_at_voc) / p_in
    fill_factor = (p_at_voc - p_max) / p_in
    extracted = p_max / p_in

    return {
        "below_gap": below_gap,
        "thermalisation": thermalisation,
        "voltage_boltzmann": voltage_boltzmann,
        "fill_factor": fill_factor,
        "extracted": extracted,
    }


def _tandem_voltage(j, jsc_i, j0_i, vth):
    """Voltage of sub-cell ``i`` carrying current ``j`` (clipped at its Jsc)."""
    arg = (jsc_i - j) / j0_i + 1.0
    return vth * np.log(np.clip(arg, 1e-300, None))


def tandem_2j(eg_top: float, eg_bot: float, spec: SpectrumIntegrals,
              t_k: float = T_CELL) -> dict:
    """Two-terminal, series-constrained 2-junction tandem efficiency.

    The top cell (wide gap ``eg_top``) absorbs the high-energy photons; the
    bottom cell (``eg_bot < eg_top``) absorbs what passes through.  Wired in
    series they must carry the same current ``J``; the stack voltage is the sum
    of the two sub-cell voltages.  We maximise ``P(J) = J * (Vtop + Vbot)``.
    """
    vth = K_B * t_k / Q
    n_top = float(spec.photon_flux_above(eg_top))
    n_bot_band = float(spec.photon_flux_above(eg_bot)) - n_top
    jsc_top = Q * n_top
    jsc_bot = Q * n_bot_band
    j0_top = j0_radiative(eg_top, t_k)
    j0_bot = j0_radiative(eg_bot, t_k)
    j_limit = max(min(jsc_top, jsc_bot), 1e-12)

    def neg_power(j: float) -> float:
        v = (_tandem_voltage(j, jsc_top, j0_top, vth)
             + _tandem_voltage(j, jsc_bot, j0_bot, vth))
        return -(j * v)

    res = minimize_scalar(neg_power, bounds=(0.0, j_limit * (1 - 1e-9)),
                          method="bounded", options={"xatol": 1e-6})
    jmp = float(res.x)
    pmax = -neg_power(jmp)
    return {
        "eg_top": eg_top,
        "eg_bot": eg_bot,
        "eta": pmax / spec.p_in_w_m2,
        "jsc_top_a_m2": jsc_top,
        "jsc_bot_a_m2": jsc_bot,
    }


def optimal_tandem(spec: SpectrumIntegrals) -> dict:
    """Grid-search the optimal 2-junction bandgap pair (coarse then refined)."""
    best = None
    # Coarse sweep.
    for et in np.arange(1.40, 2.00, 0.02):
        for eb in np.arange(0.70, et - 0.05, 0.02):
            r = tandem_2j(et, eb, spec)
            if best is None or r["eta"] > best["eta"]:
                best = r
    # Refine around the coarse optimum.
    et0, eb0 = best["eg_top"], best["eg_bot"]
    for et in np.arange(et0 - 0.04, et0 + 0.04, 0.005):
        for eb in np.arange(eb0 - 0.04, eb0 + 0.04, 0.005):
            if eb >= et - 0.05:
                continue
            r = tandem_2j(float(et), float(eb), spec)
            if r["eta"] > best["eta"]:
                best = r
    return best
