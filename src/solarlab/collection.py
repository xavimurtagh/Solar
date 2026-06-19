"""Part XVI — the collection problem: a closed loop only works if panels come back.

Part XIII showed recycling can make solar materially renewable — *if* the loop is
tight. But it quietly assumed we collect ~90% of retired panels. We don't. Today
most end-of-life PV is exported, landfilled, or abandoned; formal collection is in
the low tens of percent outside the EU. This module makes collection the variable
it really is, and surfaces two uncomfortable truths:

1. **Collection, not recycling technology, is the binding constraint.** Below ~50%
   collection the closed loop leaks so badly that the material runway collapses back
   toward the no-recycling cliff — however good the recycler is.
2. **The economics fight us, and the copper transition makes it worse.** Recovering
   a retired panel is only worth doing because of the *silver* inside; thrift the
   silver away (Part XII) and recycling's margin thins, so the copper era will need
   *more* policy to drive collection, not less.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .renewable import closed_loop_fraction, steady_state

# Representative formal end-of-life collection rates (share of retired panels that
# actually enter a recycling chain). The EU mandates it (WEEE covers PV); most of
# the world does not.
REGIONAL_COLLECTION = {
    "EU (WEEE mandate)": 0.80,
    "Global average": 0.20,
    "Most regions (no mandate)": 0.10,
}

# Mass composition of a framed c-Si module (fractions) and the price its recovered
# material fetches ($/kg). Recovered metals sell at a discount to virgin.
MODULE_COMPOSITION = {
    # element:        (mass_fraction, recovered_price_usd_per_kg)
    "Glass":          (0.70, 0.04),
    "Aluminium":      (0.10, 1.80),
    "Silicon":        (0.035, 2.50),
    "Copper":         (0.010, 7.00),
    "Silver":         (0.0002, 850.0),
    "Polymer/other":  (0.1548, 0.0),
}

RECYCLE_COST_USD_T = 280.0       # high-value (FRELP-class) recycling, $/tonne
LANDFILL_COST_USD_T = 75.0       # the cheap alternative the disposer compares to


def runway_vs_collection(collections=None, fleet_tw: float = 50.0,
                         intensity_t_per_gw: float = 13.0,
                         element: str = "Silver") -> pd.DataFrame:
    """Material runway and virgin demand as the collection rate varies.

    Everything downstream (recovery, refining) is held at best practice, so this
    isolates collection as the swing variable.
    """
    if collections is None:
        collections = [0.0, 0.1, 0.2, 0.3, 0.5, 0.7, 0.85, 0.95]
    rows = []
    for c in collections:
        cl = closed_loop_fraction(collection=c)
        ss = steady_state(element, intensity_t_per_gw, fleet_tw=fleet_tw, closed_loop=cl)
        rows.append({
            "collection": c, "closed_loop": cl,
            "virgin_t_yr": ss.virgin_t_yr,
            "virgin_share_of_production": ss.virgin_share_of_production,
            "runway_years": ss.runway_years,
        })
    return pd.DataFrame(rows)


def recovered_value_per_tonne(silver_mg_per_w: float = 13.0,
                              module_mass_t_per_gw: float = 65000.0) -> pd.DataFrame:
    """Value of the recoverable materials in one tonne of retired modules.

    ``silver_mg_per_w`` lets us shrink the silver content (Part XII thrifting /
    copper swap) and watch the recycling incentive fade.
    """
    # kW of panel per tonne, to scale the silver content from mg/W.
    # module_mass_t_per_gw t/GW == kg/MW, so kg/kW = t_per_gw / 1000.
    kw_per_tonne = 1e6 / module_mass_t_per_gw              # 1000 kg / (kg/kW)
    rows = []
    for material, (frac, price) in MODULE_COMPOSITION.items():
        if material == "Silver":
            kg = silver_mg_per_w * kw_per_tonne / 1e6 * 1000.0   # mg/W * kW / 1e6 -> kg
        else:
            kg = frac * 1000.0
        rows.append({"material": material, "kg_per_tonne": kg,
                     "value_usd": kg * price})
    return pd.DataFrame(rows)


@dataclass
class RecyclingEconomics:
    silver_mg_per_w: float
    recovered_value_t: float
    recycle_cost_t: float
    landfill_cost_t: float
    net_value_t: float          # recovered value - recycle cost
    incentive_gap_t: float      # how much cheaper landfill is for the disposer


def recycling_economics(silver_mg_per_w: float = 13.0) -> RecyclingEconomics:
    """Does recovering a retired panel pay — and does the disposer have any reason to?"""
    value = float(recovered_value_per_tonne(silver_mg_per_w)["value_usd"].sum())
    net = value - RECYCLE_COST_USD_T
    # The disposer pays to recycle (cost) vs pays to landfill; without capturing the
    # recovered value, recycling is the dearer option by this gap.
    gap = RECYCLE_COST_USD_T - LANDFILL_COST_USD_T
    return RecyclingEconomics(
        silver_mg_per_w=silver_mg_per_w, recovered_value_t=value,
        recycle_cost_t=RECYCLE_COST_USD_T, landfill_cost_t=LANDFILL_COST_USD_T,
        net_value_t=net, incentive_gap_t=gap)


def silver_thrift_effect(silver_levels=(13.0, 7.5, 0.0)) -> pd.DataFrame:
    """How recycling's value erodes as silver is thrifted toward copper (Part XII)."""
    rows = []
    for ag in silver_levels:
        e = recycling_economics(ag)
        rows.append({"silver_mg_per_w": ag, "recovered_value_t": e.recovered_value_t,
                     "net_value_t": e.net_value_t})
    return pd.DataFrame(rows)
