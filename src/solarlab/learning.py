"""Part XI — the trajectory: Wright's law and where solar is going.

Solar's defining feature is not its efficiency or even its cost today, but its
*learning rate*: every doubling of cumulative production has cut the price by a
near-constant fraction for fifty years (Wright's law). This module fits that law
to the module-price history and projects it forward along the deployment
trajectory, to ask the only question that ultimately matters — how cheap does
solar get, and what does the world do when it gets there?
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .circularity import project_deployment
from .economics import LCOEInputs, lcoe, system_cost_per_w
from .history import load_module_market


def _historical() -> pd.DataFrame:
    """Module price joined to cumulative capacity, for the learning-curve fit."""
    market = load_module_market()                       # year, module_price_usd_per_w
    dep = project_deployment(to_year=int(market["year"].max()))
    merged = market.merge(dep[["year", "cumulative_gw"]], on="year", how="inner")
    return merged.dropna(subset=["module_price_usd_per_w", "cumulative_gw"])


def fit_learning_rate() -> dict:
    """Fit Wright's law: log(price) = a + b·log(cumulative). LR = 1 - 2^b."""
    df = _historical()
    x = np.log(df["cumulative_gw"].to_numpy())
    y = np.log(df["module_price_usd_per_w"].to_numpy())
    b, a = np.polyfit(x, y, 1)
    yhat = a + b * x
    ss_res = float(np.sum((y - yhat) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    return {
        "a": float(a), "b": float(b),
        "learning_rate": float(1 - 2 ** b),            # fractional cut per doubling
        "r2": 1 - ss_res / ss_tot if ss_tot else float("nan"),
    }


def project_module_price(to_year: int = 2050) -> pd.DataFrame:
    """Historical + Wright's-law-projected module price ($/W) by year."""
    fit = fit_learning_rate()
    dep = project_deployment(to_year=to_year)
    market = load_module_market().set_index("year")["module_price_usd_per_w"]

    price = np.exp(fit["a"]) * dep["cumulative_gw"].to_numpy() ** fit["b"]
    out = dep[["year", "cumulative_gw", "kind"]].copy()
    out["module_price_usd_per_w"] = price
    # Use the actual historical price where we have it.
    out["module_price_usd_per_w"] = [
        market.get(int(y), p) for y, p in zip(out["year"], out["module_price_usd_per_w"])]
    return out


def project_lcoe(to_year: int = 2050, deployment: str = "utility") -> pd.DataFrame:
    """Projected utility LCOE ($/MWh) as module price follows Wright's law.

    System cost = projected module + balance-of-system. BOS is assumed to decline
    at half the module learning rate (conservative — soft costs are stickier),
    floored so the projection does not run to absurdity.
    """
    prices = project_module_price(to_year=to_year)
    fit = fit_learning_rate()

    base_system = system_cost_per_w(deployment)          # $/W today
    base_module = 0.27                                   # utility module line (costs.csv)
    bos = base_system - base_module                      # $/W non-module

    # BOS follows a gentler learning curve along cumulative capacity.
    dep0 = prices["cumulative_gw"].iloc[
        (prices["year"] - load_module_market()["year"].max()).abs().idxmin()]
    bos_b = fit["b"] / 2.0
    bos_series = bos * (prices["cumulative_gw"] / dep0) ** bos_b
    bos_series = np.maximum(bos_series, 0.15)            # floor: irreducible BOS

    system_cost = prices["module_price_usd_per_w"].to_numpy() + bos_series.to_numpy()
    # Specific yield ~ utility tracking (kWh/kWp); held constant.
    specific_yield = 1537.0
    lc = [lcoe(float(c), specific_yield, LCOEInputs()) * 1000.0 for c in system_cost]

    out = prices[["year", "cumulative_gw", "kind", "module_price_usd_per_w"]].copy()
    out["system_cost_per_w"] = system_cost
    out["lcoe_usd_mwh"] = lc
    return out


def milestone_years(proj: pd.DataFrame, thresholds=(35.0, 30.0, 25.0)) -> dict:
    """First projected year LCOE falls below each threshold ($/MWh)."""
    out = {}
    for t in thresholds:
        below = proj[proj["lcoe_usd_mwh"] <= t]
        out[t] = int(below["year"].iloc[0]) if not below.empty else None
    return out
