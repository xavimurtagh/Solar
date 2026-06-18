"""Levelised cost of energy (LCOE) — energy per dollar over a system's life.

Efficiency is a vanity metric; the energy industry is bought and sold in dollars
per kilowatt-hour. LCOE discounts every future kilowatt-hour and every future
cost back to the day of installation:

    LCOE = ( CapEx + sum_t OpEx_t / (1+r)^t )
           ---------------------------------------
           ( sum_t E_0 (1-d)^(t-1) / (1+r)^t )

where ``r`` is the discount rate (cost of capital), ``d`` the annual degradation,
``E_0`` the first-year yield (kWh/kWp from :mod:`solarlab.system`), and the sums
run over the system lifetime.  The model reproduces published benchmarks
(utility-scale ~US$40-60/MWh, Lazard 2025) which the tests check.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from importlib.resources import files

import numpy as np
import pandas as pd


def load_costs() -> pd.DataFrame:
    with files("solarlab.data").joinpath("costs.csv").open("r", encoding="utf-8") as fh:
        return pd.read_csv(fh)


def cost_stack(deployment: str) -> pd.Series:
    """The installed-cost breakdown ($/W) for one deployment type."""
    df = load_costs()
    sub = df[df["deployment"] == deployment]
    if sub.empty:
        raise ValueError(f"unknown deployment: {deployment}")
    return sub.set_index("component")["usd_per_w"]


def system_cost_per_w(deployment: str, module_cost_delta_per_w: float = 0.0) -> float:
    """Total installed $/W, optionally shifting the module line (e.g. after a
    material substitution that makes the cell cheaper or dearer)."""
    stack = cost_stack(deployment).copy()
    stack["module"] = max(stack["module"] + module_cost_delta_per_w, 0.0)
    return float(stack.sum())


# Default O&M ($/kW/yr) and finance assumptions by deployment.
_OPEX = {"utility": 16.0, "commercial": 18.0, "residential": 25.0}


@dataclass
class LCOEInputs:
    """Finance and lifetime assumptions.  Defaults follow NREL ATB 2024."""

    discount_rate: float = 0.06       # real WACC
    lifetime_years: int = 30
    degradation: float = 0.005        # per year (0.5%/yr)
    opex_per_kw_yr: float = 16.0


def lcoe(system_cost_per_w: float, annual_kwh_per_kw: float,
         inp: LCOEInputs | None = None) -> float:
    """LCOE in $/kWh from installed $/W and first-year specific yield."""
    inp = inp or LCOEInputs()
    capex_per_kw = system_cost_per_w * 1000.0           # $/W -> $/kW
    r, d, n = inp.discount_rate, inp.degradation, inp.lifetime_years

    years = np.arange(1, n + 1)
    discount = (1.0 + r) ** years
    pv_opex = float(np.sum(inp.opex_per_kw_yr / discount))
    pv_energy = float(np.sum(annual_kwh_per_kw * (1.0 - d) ** (years - 1) / discount))

    return (capex_per_kw + pv_opex) / pv_energy


def energy_per_dollar(system_cost_per_w: float, annual_kwh_per_kw: float,
                      inp: LCOEInputs | None = None) -> float:
    """Lifetime (undiscounted) kWh produced per dollar of installed capacity.

    A blunt, intuitive companion to LCOE: how many kWh does each up-front dollar
    eventually buy?
    """
    inp = inp or LCOEInputs()
    capex_per_kw = system_cost_per_w * 1000.0
    years = np.arange(1, inp.lifetime_years + 1)
    lifetime_kwh = float(np.sum(annual_kwh_per_kw * (1.0 - inp.degradation) ** (years - 1)))
    return lifetime_kwh / capex_per_kw


def lcoe_sensitivity(base_cost_per_w: float, base_yield: float,
                     inp: LCOEInputs | None = None) -> pd.DataFrame:
    """One-at-a-time sensitivity of LCOE to each driver (for a tornado chart).

    Each driver is swung to a low and high plausible value; everything else is
    held at base.  Returns low/high LCOE per driver, sorted by swing magnitude.
    """
    inp = inp or LCOEInputs()
    base = lcoe(base_cost_per_w, base_yield, inp)

    def with_inp(**kw):
        d = LCOEInputs(**{**inp.__dict__, **kw})
        return d

    drivers = {
        "Discount rate": (
            lcoe(base_cost_per_w, base_yield, with_inp(discount_rate=0.03)),
            lcoe(base_cost_per_w, base_yield, with_inp(discount_rate=0.09))),
        "Capacity factor / yield": (
            lcoe(base_cost_per_w, base_yield * 1.3, inp),
            lcoe(base_cost_per_w, base_yield * 0.75, inp)),
        "Installed cost": (
            lcoe(base_cost_per_w * 0.7, base_yield, inp),
            lcoe(base_cost_per_w * 1.3, base_yield, inp)),
        "Lifetime": (
            lcoe(base_cost_per_w, base_yield, with_inp(lifetime_years=40)),
            lcoe(base_cost_per_w, base_yield, with_inp(lifetime_years=20))),
        "Degradation": (
            lcoe(base_cost_per_w, base_yield, with_inp(degradation=0.002)),
            lcoe(base_cost_per_w, base_yield, with_inp(degradation=0.010))),
        "O&M cost": (
            lcoe(base_cost_per_w, base_yield, with_inp(opex_per_kw_yr=8.0)),
            lcoe(base_cost_per_w, base_yield, with_inp(opex_per_kw_yr=30.0))),
    }
    rows = [{"driver": k, "low": lo, "high": hi, "base": base,
             "swing": abs(hi - lo)} for k, (lo, hi) in drivers.items()]
    return pd.DataFrame(rows).sort_values("swing").reset_index(drop=True)


def lcoe_monte_carlo(base_cost_per_w: float, base_yield: float, n: int = 20000,
                     seed: int = 0) -> np.ndarray:
    """Monte-Carlo LCOE distribution from uncertainty in the key drivers.

    Deterministic given ``seed`` so the report is reproducible.
    """
    rng = np.random.default_rng(seed)
    cost = base_cost_per_w * rng.normal(1.0, 0.12, n).clip(0.6, 1.5)
    yield_ = base_yield * rng.normal(1.0, 0.10, n).clip(0.6, 1.4)
    rate = rng.normal(0.06, 0.015, n).clip(0.02, 0.11)
    deg = rng.normal(0.005, 0.0015, n).clip(0.001, 0.012)
    opex = rng.normal(16.0, 4.0, n).clip(6.0, 35.0)

    out = np.empty(n)
    for i in range(n):
        out[i] = lcoe(cost[i], yield_[i],
                      LCOEInputs(discount_rate=rate[i], degradation=deg[i],
                                 opex_per_kw_yr=opex[i]))
    return out


# Default O&M lookup is exposed for callers that build LCOEInputs per deployment.
def opex_for(deployment: str) -> float:
    return _OPEX.get(deployment, 16.0)
