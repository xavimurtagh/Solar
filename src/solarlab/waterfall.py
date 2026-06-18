"""The efficiency waterfall: sunlight in, AC energy out.

This assembles the report's central narrative as a single descending ladder of
efficiencies, from the Shockley-Queisser ceiling for silicon down to the annual
effective efficiency of a deployed rooftop.  Each step names the mechanism that
costs those percentage points, blending three sources:

- the **computed** SQ silicon limit (from :mod:`solarlab.sq`),
- **published** limits and records (Auger limit, lab and module records), and
- the **simulated** system performance ratio (from :mod:`solarlab.system`).
"""

from __future__ import annotations

import pandas as pd

from . import constants as C
from .sq import sq_cell


def build_waterfall(spec, sim) -> pd.DataFrame:
    """Return the sun -> AC efficiency ladder as a DataFrame.

    Columns: ``stage``, ``eta_pct`` (efficiency at that rung), ``loss_label``
    (what is lost reaching the next rung), and ``source``.
    """
    sq_si = sq_cell(C.SI_EG_EV, spec).eta * 100.0
    # Annual effective system efficiency = module STC efficiency x performance
    # ratio (POA basis) — the honest "sunlight to yearly AC" number.
    system_eff = sim.scenario.module_eff * sim.pr * 100.0

    stages = [
        ("Incident sunlight (AM1.5G)", 100.0,
         "100% of plane-of-array energy", spec_source(spec)),
        ("Shockley-Queisser limit (Si)", sq_si,
         "sub-bandgap + thermalisation + voltage + fill-factor losses",
         "Computed (detailed balance, this toolkit)"),
        ("Practical Si cell limit", C.RICHTER_SI_LIMIT_PCT,
         "intrinsic Auger recombination",
         "Richter, Hermle & Glunz 2013 (IEEE JPV)"),
        ("Best lab Si cell", C.SI_LAB_RECORD_PCT,
         "surface/contact recombination, series resistance",
         "NREL Best Research-Cell Efficiency Chart 2026"),
        ("Best commercial Si cell", C.SI_COMMERCIAL_CELL_PCT,
         "manufacturing tolerances vs the lab champion",
         "ITRPV 2024 (TOPCon production class)"),
        ("Module at STC", C.SI_MODULE_STC_PCT,
         "cell-to-module: glass reflection, gaps, interconnects",
         "PERC module datasheet (LONGi Hi-MO 5 class)"),
        ("Deployed system (annual AC)", system_eff,
         "temperature, soiling, mismatch, wiring, inverter, availability",
         "Simulated, this toolkit (pvlib, Greensboro TMY3)"),
    ]
    df = pd.DataFrame(stages, columns=["stage", "eta_pct", "loss_label", "source"])
    df["drop_pp"] = df["eta_pct"].shift(1) - df["eta_pct"]
    validate_waterfall(df)
    return df


def spec_source(spec) -> str:
    """Best-effort provenance string for the spectrum used."""
    # SpectrumIntegrals doesn't carry attrs; the spectrum loader records them.
    return "ASTM G173-03 AM1.5G (reference spectrum)"


def validate_waterfall(df: pd.DataFrame) -> None:
    """Raise ``ValueError`` if the ladder is not a strictly descending sequence."""
    eta = df["eta_pct"].values
    if not all(b < a for a, b in zip(eta, eta[1:])):
        raise ValueError("waterfall efficiencies must strictly decrease")
    if abs(eta[0] - 100.0) > 1e-9:
        raise ValueError("waterfall must start at 100%")
    if not (15.0 <= eta[-1] <= 21.0):
        raise ValueError(f"final system efficiency {eta[-1]:.1f}% outside [15, 21]")
