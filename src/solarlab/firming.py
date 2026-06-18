"""Part VIII — firming the sun: the cost of dispatchable, 24/7 solar.

The first answer to the value wall (Part VII): store the midday glut to serve the
evening peak. This module runs an hourly battery-dispatch simulation of a
solar+storage plant serving a flat (round-the-clock) load, and computes the
**levelized cost of solar+storage (LCOSS)** — the honest price of *firm* solar.

Two findings emerge, both quantified rather than asserted:
- firm solar already beats new fossil generation up to high reliability, and
- the last few percent of reliability is brutally expensive (the "100% renewable"
  tail), which is exactly why Parts IX-X exist.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .system import Scenario, reference_weather, simulate

# Reference fossil benchmarks ($/MWh, new-build, for the headline comparison).
NEW_GAS_USD_MWH = 100.0
NEW_COAL_USD_MWH = 80.0
UNFIRMED_SOLAR_USD_MWH = 40.0


@dataclass
class FirmParams:
    rt_efficiency: float = 0.87       # battery round-trip efficiency
    solar_cost_per_w: float = 0.85    # utility solar, $/W (2026)
    battery_cost_per_kwh: float = 180.0   # utility LFP installed, $/kWh (2026)
    discount_rate: float = 0.06
    lifetime_years: int = 25
    opex_per_mw_load_yr: float = 12000.0
    cf_override: float | None = None  # use a high-resource capacity factor


# A high-resource scenario (sunny site + cheaper hardware) that reproduces
# IRENA's 2026 firm-solar range of $54-82/MWh.
HIGH_RESOURCE = FirmParams(solar_cost_per_w=0.65, battery_cost_per_kwh=130.0,
                           cf_override=0.28)


def solar_profile(weather=None) -> tuple[np.ndarray, float]:
    """Normalised hourly solar (mean 1) and capacity factor (single-axis tracking).

    Computed once and passed into the sweeps — the pvlib simulation is the
    expensive step, so callers should reuse the result.
    """
    if weather is None:
        weather = reference_weather()
    sim = simulate(Scenario(name="firm", tracking=True), weather=weather)
    s = sim.hourly_ac_w.astype(float).to_numpy()
    return s / s.mean(), sim.specific_yield / 8760.0


def dispatch(solar_norm: np.ndarray, overbuild: float, storage_hours: float,
             rt_efficiency: float = 0.87) -> dict:
    """Hourly battery dispatch serving a flat unit load.

    Units: mean load power = 1, a year of load = ``len(solar_norm)``, battery
    capacity = ``storage_hours`` (hours of mean load), solar mean = ``overbuild``.
    """
    gen = overbuild * solar_norm
    cap = storage_hours
    eff = np.sqrt(rt_efficiency)               # split round-trip charge/discharge
    soc = 0.5 * cap
    unmet = 0.0
    curtailed = 0.0
    soc_series = np.empty(len(gen))

    for i in range(len(gen)):
        net = gen[i] - 1.0
        if net >= 0:                            # surplus -> charge, spill the rest
            charge = min(net, (cap - soc) / eff)
            soc += charge * eff
            curtailed += net - charge
        else:                                   # deficit -> discharge battery
            discharge = min(-net, soc * eff)
            soc -= discharge / eff
            unmet += -net - discharge
        soc_series[i] = soc

    total_load = float(len(gen))
    return {
        "reliability": 1.0 - unmet / total_load,
        "curtailment": curtailed / gen.sum() if gen.sum() else 0.0,
        "soc_series": soc_series,
        "gen": gen,
    }


def _cost(overbuild: float, storage_hours: float, cf: float, reliability: float,
          n_hours: int, p: FirmParams) -> dict:
    """LCOSS ($/MWh) for one config given its dispatch reliability. Per MW load."""
    cf_used = p.cf_override or cf
    solar_mwp = overbuild / cf_used
    solar_capex = solar_mwp * p.solar_cost_per_w * 1e6
    battery_capex = storage_hours * p.battery_cost_per_kwh * 1000.0
    capex = solar_capex + battery_capex

    r, n = p.discount_rate, p.lifetime_years
    crf = r * (1 + r) ** n / ((1 + r) ** n - 1)
    annual_cost = crf * capex + p.opex_per_mw_load_yr
    firm_mwh = n_hours * reliability
    return {
        "lcoss_usd_mwh": annual_cost / firm_mwh,
        "solar_capex_frac": solar_capex / capex,
        "battery_capex_frac": battery_capex / capex,
    }


def lcoss(overbuild: float, storage_hours: float, weather=None,
          params: FirmParams | None = None) -> dict:
    """LCOSS and dispatch metrics for a single (overbuild, storage) configuration."""
    p = params or FirmParams()
    solar_norm, cf = solar_profile(weather)
    disp = dispatch(solar_norm, overbuild, storage_hours, p.rt_efficiency)
    cost = _cost(overbuild, storage_hours, cf, disp["reliability"], len(solar_norm), p)
    return {"overbuild": overbuild, "storage_hours": storage_hours,
            "reliability": disp["reliability"], "curtailment": disp["curtailment"],
            **cost}


def evaluate_grid(weather=None, params: FirmParams | None = None,
                  overbuilds=None, storage_set=None) -> pd.DataFrame:
    """LCOSS over a grid of overbuild x storage (one pvlib sim, reused)."""
    p = params or FirmParams()
    solar_norm, cf = solar_profile(weather)
    n = len(solar_norm)
    if overbuilds is None:
        overbuilds = np.round(np.arange(1.2, 4.01, 0.2), 2)
    if storage_set is None:
        storage_set = np.arange(2, 49, 3)

    rows = []
    for ob in overbuilds:
        for st in storage_set:
            disp = dispatch(solar_norm, float(ob), float(st), p.rt_efficiency)
            cost = _cost(float(ob), float(st), cf, disp["reliability"], n, p)
            rows.append({"overbuild": float(ob), "storage_hours": float(st),
                         "reliability": disp["reliability"],
                         "curtailment": disp["curtailment"], **cost})
    return pd.DataFrame(rows)


def lcoss_vs_reliability(weather=None, params: FirmParams | None = None,
                         targets=None) -> pd.DataFrame:
    """Cheapest LCOSS achievable at each reliability target (the firming curve)."""
    grid = evaluate_grid(weather=weather, params=params)
    if targets is None:
        targets = [0.80, 0.85, 0.90, 0.93, 0.95, 0.97, 0.98, 0.99, 0.995]
    rows = []
    for t in targets:
        feasible = grid[grid["reliability"] >= t]
        if not feasible.empty:
            best = feasible.loc[feasible["lcoss_usd_mwh"].idxmin()]
            rows.append({"reliability": t, "lcoss_usd_mwh": best["lcoss_usd_mwh"],
                         "overbuild": best["overbuild"],
                         "storage_hours": best["storage_hours"]})
    return pd.DataFrame(rows)


def cheapest_firm(weather=None, params: FirmParams | None = None,
                  reliability_target: float = 0.95) -> dict:
    """The minimum-cost config meeting a reliability target."""
    grid = evaluate_grid(weather=weather, params=params)
    feasible = grid[grid["reliability"] >= reliability_target]
    return feasible.loc[feasible["lcoss_usd_mwh"].idxmin()].to_dict()


def representative_week(overbuild: float, storage_hours: float, weather=None,
                        params: FirmParams | None = None, start_hour=4080,
                        hours=240) -> pd.DataFrame:
    """A slice of the dispatch (solar, load, battery SOC) for visualisation."""
    p = params or FirmParams()
    solar_norm, _ = solar_profile(weather)
    disp = dispatch(solar_norm, overbuild, storage_hours, p.rt_efficiency)
    sl = slice(start_hour, start_hour + hours)
    return pd.DataFrame({
        "hour": np.arange(hours),
        "solar": disp["gen"][sl],
        "soc": disp["soc_series"][sl],
        "soc_max": storage_hours,
    })
