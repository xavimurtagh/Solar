"""Part XII — the copper question: does replacing silver actually pay off?

Parts II-III claimed copper metallisation is a near-free win. That was only ever a
cost-and-abundance argument; it never modelled what copper does to a cell's
*performance* or *lifetime*. This module closes that gap.

It compares three metallisations on a like-for-like LCOE basis, propagating the
real engineering differences:
- **efficiency** — plated copper forms finer lines than screen-printed silver
  paste, so it is neutral-to-slightly-better, not worse;
- **reliability** — copper's open question is longevity (diffusion into silicon,
  corrosion), modelled as a degradation-rate / lifetime knob;
- **cost** — the silver saving, net of the extra plating process cost.

The headline result is deliberately uncomfortable: copper's *LCOE* edge is small
and easily erased by a modest reliability penalty, because silver is only ~1% of a
system's cost. Copper's real value is not cheaper energy — it is escaping the
silver supply ceiling (Part III). The case for copper is abundance, not price.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .economics import LCOEInputs, lcoe, system_cost_per_w

# Metal prices ($/g) consistent with materials.csv.
SILVER_USD_G = 0.90
COPPER_USD_G = 0.0095
NICKEL_USD_G = 0.020


@dataclass
class Metallization:
    name: str
    module_eff: float            # STC module efficiency
    silver_mg_per_w: float
    copper_mg_per_w: float
    nickel_mg_per_w: float
    process_cost_per_w: float    # extra manufacturing cost vs screen-print baseline
    degradation: float           # 1/yr (annual power loss)
    lifetime_years: int
    note: str


# Three options. Silver = today's proven screen print. Copper(nominal) assumes the
# reliability problem is solved (HJT's TCO blocks Cu diffusion; Ni barrier for
# others) and credits a small efficiency gain from finer lines. Copper(cautious)
# prices in the shorter field track record as faster degradation + shorter life.
OPTIONS = [
    Metallization("Silver (screen-print)", 0.223, 13.0, 0.0, 0.0, 0.0,
                  0.0050, 30, "proven ~30-yr field history"),
    Metallization("Copper Ni/Cu (nominal)", 0.225, 0.0, 15.0, 1.5, 0.006,
                  0.0050, 30, "finer lines; reliability assumed solved"),
    Metallization("Copper (cautious reliability)", 0.225, 0.0, 15.0, 1.5, 0.006,
                  0.0065, 25, "prices in shorter track record"),
]


def _metal_cost_per_w(m: Metallization) -> float:
    """Raw metal + plating process cost ($/W) of a metallisation."""
    metal = (m.silver_mg_per_w * SILVER_USD_G
             + m.copper_mg_per_w * COPPER_USD_G
             + m.nickel_mg_per_w * NICKEL_USD_G) / 1000.0
    return metal + m.process_cost_per_w


def metal_lcoe(m: Metallization, deployment: str = "utility",
               specific_yield: float = 1537.0, baseline_silver_mg: float = 13.0) -> dict:
    """LCOE ($/MWh) for a metallisation, holding everything else equal.

    The system cost has its baseline silver stripped out and this metallisation's
    metal+process cost added back, so the comparison isolates the swap.
    """
    baseline_silver_cost = baseline_silver_mg * SILVER_USD_G / 1000.0
    non_metal_system = system_cost_per_w(deployment) - baseline_silver_cost
    system = non_metal_system + _metal_cost_per_w(m)
    inp = LCOEInputs(degradation=m.degradation, lifetime_years=m.lifetime_years)
    return {
        "name": m.name,
        "system_cost_per_w": system,
        "metal_cost_per_w": _metal_cost_per_w(m),
        "degradation": m.degradation,
        "lifetime_years": m.lifetime_years,
        "lcoe_usd_mwh": lcoe(system, specific_yield, inp) * 1000.0,
        "note": m.note,
    }


def comparison(deployment: str = "utility") -> pd.DataFrame:
    return pd.DataFrame([metal_lcoe(m, deployment) for m in OPTIONS])


def breakeven_degradation(deployment: str = "utility",
                          specific_yield: float = 1537.0) -> dict:
    """Copper degradation rate at which its LCOE equals proven silver's.

    Quantifies how thin copper's cost advantage is: a tiny extra annual power loss
    wipes it out, because the silver saving is a small share of system cost.
    """
    silver = metal_lcoe(OPTIONS[0], deployment, specific_yield)["lcoe_usd_mwh"]
    copper = OPTIONS[1]

    def copper_lcoe(degr):
        m = Metallization(**{**copper.__dict__, "degradation": degr})
        return metal_lcoe(m, deployment, specific_yield)["lcoe_usd_mwh"]

    grid = np.linspace(0.005, 0.020, 600)
    diffs = np.array([copper_lcoe(d) - silver for d in grid])
    cross = np.where(diffs >= 0)[0]
    be = float(grid[cross[0]]) if len(cross) else float("nan")
    return {
        "silver_degradation": OPTIONS[0].degradation,
        "breakeven_copper_degradation": be,
        "extra_degradation_tolerated": be - OPTIONS[0].degradation,
        "silver_lcoe": silver,
    }


def degradation_sweep(deployment: str = "utility") -> pd.DataFrame:
    """LCOE vs copper degradation rate, against the proven-silver line."""
    silver = metal_lcoe(OPTIONS[0], deployment)["lcoe_usd_mwh"]
    copper = OPTIONS[1]
    rows = []
    for d in np.linspace(0.004, 0.012, 30):
        m = Metallization(**{**copper.__dict__, "degradation": float(d)})
        rows.append({"copper_degradation": d,
                     "copper_lcoe": metal_lcoe(m, deployment)["lcoe_usd_mwh"],
                     "silver_lcoe": silver})
    return pd.DataFrame(rows)
