"""A techno-economic optimiser: pick the best cell + deployment for a goal.

The frontier (:mod:`solarlab.frontier`) lays out every technology and deployment
on cost, space, and scale. This module turns that map into a decision: given a
**budget**, an **available area**, and an **objective**, which option wins?

The interesting behaviour is emergent, not assumed: when money is the binding
constraint the optimiser favours the cheapest energy; when *area* binds it
favours the most efficient cell, because every square metre must work harder.
The optimiser reports which constraint binds, so the recommendation is explained,
not just asserted.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .economics import system_cost_per_w
from .frontier import build_frontier


# Module price premium ($/W) over baseline PERC, by technology. Higher-efficiency
# cells command a premium; this is what makes the area-vs-budget trade-off real.
# Source: typical 2024 module price spreads (PERC < TOPCon < HJT << tandem).
MODULE_PREMIUM_USD_W = {
    "PERC": 0.00,
    "TOPCon": 0.01,
    "HJT": 0.03,
    "Perovskite-Si tandem": 0.08,
}


@dataclass
class Constraints:
    budget_usd: float | None = None
    area_m2: float | None = None          # module/array area available
    deployment: str | None = None         # restrict to one deployment, else search all
    target_kwh: float | None = None       # for the min-cost-for-target objective


def evaluate(frontier_df: pd.DataFrame, c: Constraints) -> pd.DataFrame:
    """Annotate each (tech, deployment) with what it achieves under constraints.

    Adds installed capacity (limited by budget and/or area), annual energy, total
    cost, and which constraint binds.
    """
    df = frontier_df.copy()
    if c.deployment:
        df = df[df["deployment"] == c.deployment].copy()

    cost_per_w = np.array([
        system_cost_per_w(d) + MODULE_PREMIUM_USD_W.get(t, 0.0)
        for d, t in zip(df["deployment"], df["technology"])])
    df["cost_per_w"] = cost_per_w

    cap_budget = (c.budget_usd / (cost_per_w * 1000.0)
                  if c.budget_usd is not None else np.full(len(df), np.inf))
    cap_area = (c.area_m2 * df["module_eff"].values
                if c.area_m2 is not None else np.full(len(df), np.inf))

    capacity = np.minimum(cap_budget, cap_area)
    # If no sizing constraint is given, evaluate a nominal 1 kW (size-independent
    # metrics like LCOE are unaffected).
    capacity = np.where(np.isfinite(capacity), capacity, 1.0)

    df["capacity_kw"] = capacity
    df["annual_kwh"] = capacity * df["specific_yield"].values
    df["total_cost_usd"] = capacity * 1000.0 * cost_per_w
    df["binding"] = np.where(cap_budget <= cap_area, "budget", "area")
    if c.budget_usd is None and c.area_m2 is None:
        df["binding"] = "none"
    return df


def optimize(objective: str = "max_energy", constraints: Constraints | None = None,
             frontier_df: pd.DataFrame | None = None, weather=None) -> dict:
    """Return the best option for an objective under constraints.

    Objectives:
      - ``max_energy``: most annual kWh within budget and area.
      - ``min_lcoe``: cheapest energy ($/MWh), independent of size.
      - ``min_cost_for_target``: cheapest system meeting ``target_kwh`` (and
        fitting in ``area_m2`` / ``budget_usd`` if given).
    """
    c = constraints or Constraints()
    if frontier_df is None:
        frontier_df = build_frontier(weather=weather)
    df = evaluate(frontier_df, c)

    if objective == "max_energy":
        ranked = df.sort_values("annual_kwh", ascending=False)
    elif objective == "min_lcoe":
        ranked = df.sort_values("lcoe_usd_mwh")
    elif objective == "min_cost_for_target":
        if not c.target_kwh:
            raise ValueError("min_cost_for_target needs constraints.target_kwh")
        cap_needed = c.target_kwh / df["specific_yield"].values
        df = df.assign(
            capacity_kw=cap_needed,
            annual_kwh=c.target_kwh,
            total_cost_usd=cap_needed * 1000.0 * df["cost_per_w"].values,
            area_needed_m2=cap_needed / df["module_eff"].values)
        feasible = df
        if c.area_m2 is not None:
            feasible = feasible[feasible["area_needed_m2"] <= c.area_m2]
        if c.budget_usd is not None:
            feasible = feasible[feasible["total_cost_usd"] <= c.budget_usd]
        if feasible.empty:
            return {"objective": objective, "feasible": False, "best": None,
                    "ranked": df.sort_values("total_cost_usd").reset_index(drop=True)}
        ranked = feasible.sort_values("total_cost_usd")
    else:
        raise ValueError(f"unknown objective: {objective}")

    ranked = ranked.reset_index(drop=True)
    best = ranked.iloc[0]
    return {
        "objective": objective,
        "feasible": True,
        "best": best,
        "binding": best.get("binding", "n/a"),
        "ranked": ranked,
    }
