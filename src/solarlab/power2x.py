"""Part IX — solar as feedstock: stop storing electrons, start making molecules.

The second answer to the value wall (Part VII), and the deepest reframe. Firming
(Part VIII) reshapes *solar* to fit demand. Power-to-X reshapes *demand* to fit
solar: build flexible, interruptible loads — electrolysers, direct-air-capture,
desalination, smelters, datacenters — that feast on the near-free midday glut that
the grid throws away.

This module computes:
- the levelized cost of green hydrogen (LCOH) vs electricity price and utilisation
  (validated against the 2026 $2.50-5/kg range),
- the "inversion": flexible electrolysis absorbing the curtailed glut from Part VII,
  raising solar's value factor while making a product, and
- the end-use unlock — what near-free solar electricity does to the cost of
  hydrogen, ammonia, fuels, water, carbon removal, steel and compute.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .value import demand_profile, solar_shape

# Electrolyser: a PEM/alkaline system at ~0.66 efficiency (HHV 39.4 kWh/kg).
H2_ENERGY_KWH_PER_KG = 51.0
# Reference fossil hydrogen (steam methane reforming), $/kg.
GREY_H2_USD_KG = 1.5
BLUE_H2_USD_KG = 2.2


def lcoh(elec_price_usd_mwh: float, capacity_factor: float,
         electrolyzer_capex_per_kw: float = 700.0, opex_per_kw_yr: float = 25.0,
         discount_rate: float = 0.08, lifetime_years: int = 20,
         other_usd_kg: float = 0.30) -> float:
    """Levelized cost of green hydrogen ($/kg).

    Two terms dominate: the electrolyser capital, amortised over how much hydrogen
    it makes (so *utilisation* matters), and the electricity, which is ~55-70% of
    the total. ``other`` lumps water, stack replacement and balance-of-plant.
    """
    crf = (discount_rate * (1 + discount_rate) ** lifetime_years
           / ((1 + discount_rate) ** lifetime_years - 1))
    annual_kg_per_kw = 8760.0 * capacity_factor / H2_ENERGY_KWH_PER_KG
    capex_term = (crf * electrolyzer_capex_per_kw + opex_per_kw_yr) / annual_kg_per_kw
    elec_term = elec_price_usd_mwh * (H2_ENERGY_KWH_PER_KG / 1000.0)
    return capex_term + elec_term + other_usd_kg


def lcoh_curve(capacity_factor: float, elec_prices=None, **kw) -> pd.DataFrame:
    """LCOH across electricity price at a fixed utilisation."""
    if elec_prices is None:
        elec_prices = np.arange(0, 81, 5)
    return pd.DataFrame({
        "elec_price_usd_mwh": elec_prices,
        "lcoh_usd_kg": [lcoh(float(p), capacity_factor, **kw) for p in elec_prices],
    })


def glut_to_hydrogen(penetration: float, annual_demand_twh: float = 1000.0,
                     weather=None) -> dict:
    """Convert the curtailed solar glut at a given penetration into hydrogen.

    Uses the Part VII curtailment: at high penetration a large share of solar is
    spilled. Routed to electrolysers, that otherwise-wasted energy becomes fuel.
    """
    solar = solar_shape(weather)
    demand = demand_profile(solar.index)
    s = solar.to_numpy()
    d = demand.to_numpy()
    spilled = np.maximum(penetration * s - d, 0.0)
    curtail_frac = spilled.sum() / (penetration * s.sum())

    solar_twh = penetration * annual_demand_twh
    curtailed_twh = curtail_frac * solar_twh
    h2_mt = curtailed_twh * 1e9 / H2_ENERGY_KWH_PER_KG / 1e9    # million tonnes
    return {
        "penetration": penetration,
        "curtailment_frac": curtail_frac,
        "curtailed_twh": curtailed_twh,
        "hydrogen_mt": h2_mt,
    }


def flexible_demand_effect(penetration: float, flex_capacity: float,
                           weather=None) -> dict:
    """How flexible electrolysis load (turned on during surplus) lifts solar value.

    ``flex_capacity`` is the flexible load's max power in units of mean demand.
    Flexible demand soaks up the surplus solar that would otherwise be curtailed,
    lifting the midday price out of the negative — so solar's value factor rises
    *and* a product (hydrogen) gets made from energy that was being thrown away.
    """
    from .value import _price

    solar = solar_shape(weather)
    demand = demand_profile(solar.index)
    s = solar.to_numpy()
    d = demand.to_numpy()
    r_max = float(d.max())

    def value_factor(residual):
        price = _price(residual, r_max)
        return float(np.sum(price * s) / np.sum(s) / price.mean())

    residual_base = d - penetration * s
    surplus = np.maximum(penetration * s - d, 0.0)
    flex_load = np.minimum(surplus, flex_capacity)
    residual_flex = residual_base + flex_load          # flex demand lifts net load

    spill_base = surplus.sum()
    spill_flex = np.maximum(surplus - flex_load, 0.0).sum()
    solar_total = penetration * s.sum()

    return {
        "penetration": penetration,
        "value_factor_base": value_factor(residual_base),
        "value_factor_flex": value_factor(residual_flex),
        "curtailment_base": spill_base / solar_total,
        "curtailment_flex": spill_flex / solar_total,
    }


# End-use energy intensities (electricity per unit of useful output). Sources:
# electrolysis 51 kWh/kg; ammonia ~12 MWh/t (incl. H2); e-fuel ~25 kWh/L;
# seawater RO ~3.5 kWh/m^3; direct air capture ~2 MWh/tCO2; H2-DRI green steel
# ~3.5 MWh/t; datacenter is pure $/kWh.
_END_USES = [
    ("Green hydrogen", 51.0, "kg", 4.0),
    ("Green ammonia", 12000.0, "tonne", 600.0),
    ("Synthetic e-fuel", 25.0, "litre", 1.5),
    ("Desalinated water", 3.5, "m^3", 0.8),
    ("Direct air capture", 2000.0, "tonne CO2", 400.0),
    ("Green steel", 3500.0, "tonne", 600.0),
]


def enduse_unlock(cheap_price_usd_mwh: float = 20.0,
                  grid_price_usd_mwh: float = 90.0) -> pd.DataFrame:
    """Electricity-cost component of each product at cheap-solar vs grid prices.

    Shows how near-free midday solar collapses the energy cost of molecules, water
    and carbon removal — the demand-side revolution.
    """
    rows = []
    for name, kwh_per_unit, unit, market_ref in _END_USES:
        cheap = kwh_per_unit / 1000.0 * cheap_price_usd_mwh
        grid = kwh_per_unit / 1000.0 * grid_price_usd_mwh
        rows.append({
            "product": name, "unit": unit,
            "kwh_per_unit": kwh_per_unit,
            "elec_cost_cheap": cheap,
            "elec_cost_grid": grid,
            "market_reference": market_ref,
        })
    return pd.DataFrame(rows)
