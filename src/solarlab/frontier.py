"""The multi-objective frontier: dollars, space, and abundance together.

"Maximise energy per dollar" and "optimise for space used" are different
objectives that usually trade off, and both interact with the material ceiling
from :mod:`solarlab.materials`. This module evaluates each technology across
deployment types on three axes at once:

- **LCOE** ($/kWh) — energy per dollar (lower is better),
- **energy density** (kWh/m^2/yr) — energy per unit of space (higher is better),
- **deployment ceiling** (TW/yr) — how far it can scale (higher is better).

and identifies the Pareto-optimal set — the options where you cannot improve one
objective without sacrificing another.
"""

from __future__ import annotations

import pandas as pd

from .economics import LCOEInputs, lcoe, opex_for, system_cost_per_w
from .history import load_technologies
from .materials import deployment_ceiling
from .system import Scenario, simulate

# Deployment archetypes: utility plants track the sun; rooftops are fixed.
DEPLOYMENTS = {
    "utility": dict(tracking=True),
    "commercial": dict(tracking=False),
    "residential": dict(tracking=False),
}


def technology_options() -> pd.DataFrame:
    """Bankable technologies with module efficiency and temperature coefficient."""
    return load_technologies()


def build_frontier(weather=None) -> pd.DataFrame:
    """Evaluate every (technology, deployment) pair on cost, space, and ceiling."""
    techs = technology_options()
    rows = []
    for _, t in techs.iterrows():
        eff = float(t["module_eff_frac"])
        gamma = float(t["gamma_pdc_per_c"])
        ceiling = deployment_ceiling(t["technology"])
        for dep, cfg in DEPLOYMENTS.items():
            sc = Scenario(name=f"{t['technology']} / {dep}", module_eff=eff,
                          gamma_pdc=gamma, **cfg)
            sim = simulate(sc, weather=weather)
            cost_per_w = system_cost_per_w(dep)
            L = lcoe(cost_per_w, sim.specific_yield,
                     LCOEInputs(opex_per_kw_yr=opex_for(dep)))
            rows.append({
                "technology": t["technology"],
                "deployment": dep,
                "module_eff": eff,
                "specific_yield": sim.specific_yield,
                "lcoe_usd_kwh": L,
                "lcoe_usd_mwh": L * 1000.0,
                # energy per unit module area per year:
                "energy_density_kwh_m2_yr": sim.specific_yield * eff,
                "tw_per_year": ceiling["tw_per_year"],
                "binding_element": ceiling["binding_element"],
            })
    df = pd.DataFrame(rows)
    # Two-objective frontier: energy per dollar vs energy per unit space.
    df["pareto"] = pareto_mask(
        df, minimise=["lcoe_usd_kwh"], maximise=["energy_density_kwh_m2_yr"])
    # Three-objective frontier: also reward how far a technology can scale.
    df["pareto_scale"] = pareto_mask(
        df, minimise=["lcoe_usd_kwh"],
        maximise=["energy_density_kwh_m2_yr", "tw_per_year"])
    return df


def pareto_mask(df: pd.DataFrame, minimise: list[str],
                maximise: list[str]) -> pd.Series:
    """Boolean mask of Pareto-optimal rows over arbitrary objectives.

    A row is dominated if another is at least as good on every objective and
    strictly better on at least one.
    """
    mins = df[minimise].values
    maxs = df[maximise].values
    n = len(df)
    optimal = [True] * n
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            no_worse = ((mins[j] <= mins[i]).all() and (maxs[j] >= maxs[i]).all())
            strictly_better = ((mins[j] < mins[i]).any() or (maxs[j] > maxs[i]).any())
            if no_worse and strictly_better:
                optimal[i] = False
                break
    return pd.Series(optimal, index=df.index)
