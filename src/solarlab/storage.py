"""Part XVII — storing the midday sun: the duration bottleneck.

Part VIII firmed solar with a generic battery and found a cost cliff at high
reliability. This part opens the black box: *which* storage, and *why* the cliff
exists. The key idea is that every store has **two** costs — the power rating
(\$/kW, how fast it charges/discharges) and the energy capacity (\$/kWh, how much it
holds) — and which one dominates depends entirely on **duration**:

- short durations (hours) are cheapest with high-efficiency, power-optimised
  lithium;
- long durations (days to seasons) are cheapest with dirt-cheap energy capacity —
  iron-air, heat, hydrogen — even though they waste far more energy per cycle,
  because they barely cycle.

The bottleneck humanity actually faces is not "storage" in general; it is
**long-duration** storage, where lithium's \$/kWh is hopeless and the cheap
alternatives are immature. This module computes the cost-vs-duration crossover and
names the winner at each timescale.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

DISCOUNT_RATE = 0.06
LIFETIME_YEARS = 25
DEPTH_OF_DISCHARGE = 0.9
DEFAULT_CHARGE_PRICE = 50.0      # $/MWh paid for the energy stored (cheap solar)


@dataclass
class StorageTech:
    name: str
    power_cost_usd_kw: float      # $/kW of charge/discharge rating
    energy_cost_usd_kwh: float    # $/kWh of capacity
    round_trip_eff: float
    material: str                 # abundance class for the recurring theme
    best_role: str


# Representative 2026 installed parameters. Power vs energy split is the point: a
# lithium pack is dominated by its $/kWh; a hydrogen system by its $/kW (the
# electrolyser + fuel cell) but with almost-free $/kWh in a salt cavern.
TECHS = [
    StorageTech("Lithium-ion (LFP)", 150, 250, 0.90, "Li moderate / Fe-P abundant", "hours (daily shift)"),
    StorageTech("Flow battery (vanadium)", 500, 130, 0.70, "vanadium scarce", "4-12 h"),
    StorageTech("Pumped hydro", 1500, 12, 0.80, "abundant, geography-limited", "hours-days"),
    StorageTech("Iron-air (multi-day)", 350, 25, 0.50, "iron — abundant", "days"),
    StorageTech("Thermal (rock/salt)", 250, 18, 0.45, "abundant", "days (and heat)"),
    StorageTech("Hydrogen (cavern)", 1800, 2, 0.35, "abundant, cavern-limited", "weeks-seasonal"),
]


def cycles_for_duration(duration_h: float) -> float:
    """Annual full cycles a store of this duration naturally achieves.

    Short stores cycle ~daily (capped at 365); a store that holds many days of
    energy inherently cycles far less often.
    """
    return min(365.0, 8760.0 / duration_h)


def _crf() -> float:
    r, n = DISCOUNT_RATE, LIFETIME_YEARS
    return r * (1 + r) ** n / ((1 + r) ** n - 1)


def lcos(tech: StorageTech, duration_h: float,
         charge_price_usd_mwh: float = DEFAULT_CHARGE_PRICE,
         cycles_per_year: float | None = None) -> float:
    """Levelized cost of storage ($/MWh discharged) for a tech at a duration."""
    if cycles_per_year is None:
        cycles_per_year = cycles_for_duration(duration_h)
    capex_per_kw = tech.power_cost_usd_kw + tech.energy_cost_usd_kwh * duration_h
    annual_discharge_kwh = duration_h * DEPTH_OF_DISCHARGE * cycles_per_year
    capex_term = _crf() * capex_per_kw / annual_discharge_kwh * 1000.0   # $/MWh
    # Charging: you must put in 1/RTE kWh for each kWh delivered.
    charge_term = charge_price_usd_mwh / tech.round_trip_eff
    return capex_term + charge_term


def lcos_vs_duration(durations_h=None, charge_price=DEFAULT_CHARGE_PRICE) -> pd.DataFrame:
    """LCOS of every technology across a range of storage durations."""
    if durations_h is None:
        durations_h = np.array([2, 4, 8, 12, 24, 48, 100, 300, 720, 2000], dtype=float)
    rows = []
    for d in durations_h:
        row = {"duration_h": float(d)}
        for t in TECHS:
            row[t.name] = lcos(t, float(d), charge_price)
        rows.append(row)
    return pd.DataFrame(rows)


def best_by_duration(durations_h=None, charge_price=DEFAULT_CHARGE_PRICE) -> pd.DataFrame:
    """The cheapest technology (and its LCOS) at each duration."""
    if durations_h is None:
        durations_h = [4, 12, 24, 100, 720, 2000]
    rows = []
    for d in durations_h:
        costs = {t.name: lcos(t, float(d), charge_price) for t in TECHS}
        winner = min(costs, key=costs.get)
        tech = next(t for t in TECHS if t.name == winner)
        rows.append({"duration_h": float(d), "winner": winner,
                     "lcos_usd_mwh": costs[winner], "material": tech.material})
    return pd.DataFrame(rows)
