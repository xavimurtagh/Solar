"""Circularity: recycling turns the terawatt ceiling into a moving target.

The static ceiling in :mod:`solarlab.materials` assumes every watt is built from
freshly-mined metal. But a panel installed today is feedstock tomorrow. This
module runs a dynamic material-flow analysis of the global PV fleet:

- panels are installed each year along a historical + projected trajectory,
- they retire decades later following a Weibull survival curve,
- the retired fleet is an "urban mine" whose recovered metal *adds* to annual
  supply, raising the deployment ceiling year on year.

The headline: the silver and indium ceilings that look like hard walls today
*rise over time*, and by mid-century the retired fleet can meet a large share of
demand. The model is validated against IRENA's projection of ~78 Mt of
recoverable PV material by 2050.
"""

from __future__ import annotations

from importlib.resources import files

import numpy as np
import pandas as pd

from . import constants as C
from .materials import _materials_indexed, technology_bom


# --- Lifetime / retirement --------------------------------------------------

def weibull_survival(age, shape: float, scale: float):
    """Fraction of a cohort still operating at ``age`` years: S=exp(-(a/T)^k)."""
    age = np.maximum(np.asarray(age, dtype=float), 0.0)
    return np.exp(-((age / scale) ** shape))


def retirement_fraction(age, shape: float, scale: float):
    """Fraction of a cohort retiring during year ``age`` (between a-1 and a)."""
    return (weibull_survival(np.asarray(age) - 1, shape, scale)
            - weibull_survival(age, shape, scale))


# --- Deployment trajectory --------------------------------------------------

def load_deployment() -> pd.DataFrame:
    """Historical global annual PV additions (GW), gap-filled to a full series."""
    with files("solarlab.data").joinpath("deployment.csv").open("r", encoding="utf-8") as fh:
        df = pd.read_csv(fh)
    years = np.arange(int(df["year"].min()), int(df["year"].max()) + 1)
    s = (df.set_index("year")["annual_gw"]
         .reindex(years).interpolate(method="linear"))
    return pd.DataFrame({"year": years, "annual_gw": s.values, "kind": "actual"})


def project_deployment(to_year: int = 2050, plateau_gw: float = 3000.0,
                       approach_rate: float = 0.12) -> pd.DataFrame:
    """Full installs series (GW/yr), historical actuals + a projection.

    Projected annual additions approach a ``plateau_gw`` (~3.5 TW/yr, consistent
    with IEA Net-Zero / IRENA 1.5C build rates) via bounded exponential growth
    from the last actual year:

        add(t) = plateau - (plateau - add_last) * exp(-approach_rate*(t - last))

    This is a smooth, monotone scenario; the resulting cumulative by 2050 lands
    near ~70 TW (tested to be in 50-90 TW).
    """
    hist = load_deployment()
    last_year = int(hist["year"].max())
    add_last = float(hist["annual_gw"].iloc[-1])

    fut_years = np.arange(last_year + 1, to_year + 1)
    fut_add = plateau_gw - (plateau_gw - add_last) * np.exp(
        -approach_rate * (fut_years - last_year))
    fut = pd.DataFrame({"year": fut_years, "annual_gw": fut_add,
                        "kind": "projected"})
    out = pd.concat([hist, fut], ignore_index=True)
    out["cumulative_gw"] = out["annual_gw"].cumsum()
    return out


# --- Stock-and-flow fleet model --------------------------------------------

def fleet_flows(scenario: str = "regular", to_year: int = 2050) -> pd.DataFrame:
    """In-field stock and annual retirements for the whole fleet (GW).

    ``scenario`` selects the Weibull set in ``constants.PV_LIFETIME_WEIBULL``.
    """
    shape, scale = C.PV_LIFETIME_WEIBULL[scenario]
    dep = project_deployment(to_year=to_year)
    years = dep["year"].values
    installs = dep["annual_gw"].values

    stock = np.zeros(len(years))
    retired = np.zeros(len(years))
    for i, t in enumerate(years):
        ages = t - years[: i + 1]
        cohort = installs[: i + 1]
        stock[i] = float(np.sum(cohort * weibull_survival(ages, shape, scale)))
        retired[i] = float(np.sum(cohort * retirement_fraction(ages, shape, scale)))

    dep = dep.copy()
    dep["stock_gw"] = stock
    dep["retired_gw"] = retired
    return dep


# --- Material flow for one technology / element -----------------------------

def _element_intensity(technology: str, element: str) -> float:
    """Intensity (g/kW == tonnes/GW) of ``element`` in ``technology``'s BOM."""
    bom = technology_bom(technology)
    row = bom[bom["element"] == element]
    if row.empty:
        raise ValueError(f"{element} not in {technology} bill of materials")
    return float(row["intensity_g_per_kw"].iloc[0])


def load_recovery() -> pd.DataFrame:
    """Recovery efficiency by recycling process and element."""
    with files("solarlab.data").joinpath("recovery.csv").open("r", encoding="utf-8") as fh:
        return pd.read_csv(fh)


def _recovery(process: str, element: str) -> float:
    rec = load_recovery()
    row = rec[(rec["process"] == process) & (rec["element"] == element)]
    return float(row["recovery_efficiency"].iloc[0]) if not row.empty else 0.0


def material_flow(technology: str, element: str, scenario: str = "regular",
                  process: str = "frelp", supply_share: float = 0.5,
                  to_year: int = 2050) -> pd.DataFrame:
    """Per-year material flow and the recycling-relaxed ceiling for one element.

    Columns added to the fleet flows: ``demand_t`` (virgin metal a year's installs
    need), ``secondary_t`` (metal recovered from that year's retirements),
    ``circularity`` (secondary/demand), and the linear vs circular deployment
    ceilings in TW/yr.
    """
    flows = fleet_flows(scenario=scenario, to_year=to_year)
    intensity = _element_intensity(technology, element)          # tonnes/GW
    recovery = _recovery(process, element)
    production = float(_materials_indexed().loc[element, "annual_production_tonnes"])

    demand_t = flows["annual_gw"].values * intensity             # tonnes/yr
    secondary_t = flows["retired_gw"].values * intensity * recovery
    with np.errstate(divide="ignore", invalid="ignore"):
        circularity = np.where(demand_t > 0, secondary_t / demand_t, 0.0)

    # Linear (primary-only) ceiling for this element, constant over time.
    ceiling_linear_tw = (production * supply_share / intensity) / 1000.0
    # Circular ceiling: recovered metal adds GW-equivalent headroom each year.
    ceiling_circular_tw = ceiling_linear_tw + flows["retired_gw"].values * recovery / 1000.0

    out = flows.copy()
    out["technology"] = technology
    out["element"] = element
    out["demand_t"] = demand_t
    out["secondary_t"] = secondary_t
    out["circularity"] = circularity
    out["ceiling_linear_tw"] = ceiling_linear_tw
    out["ceiling_circular_tw"] = ceiling_circular_tw
    return out


def circularity_crossover(flow_df: pd.DataFrame, threshold: float = 0.5):
    """First year recovered metal supplies >= ``threshold`` of annual demand."""
    hit = flow_df[flow_df["circularity"] >= threshold]
    return int(hit["year"].iloc[0]) if not hit.empty else None


def cumulative_recovered_mass_mt(to_year: int = 2050,
                                 scenario: str = "regular") -> float:
    """Cumulative retired module mass by ``to_year`` (Mt) — the urban mine.

    Validation target: IRENA projects ~78 Mt of recoverable PV material by 2050.
    """
    flows = fleet_flows(scenario=scenario, to_year=to_year)
    retired_gw = flows[flows["year"] <= to_year]["retired_gw"].sum()
    return float(retired_gw * C.MODULE_MASS_T_PER_GW / 1e6)


def cumulative_virgin_avoided_t(technology: str, element: str,
                                process: str = "frelp", scenario: str = "regular",
                                to_year: int = 2050) -> float:
    """Cumulative tonnes of virgin ``element`` displaced by recycling, to year."""
    flow = material_flow(technology, element, scenario=scenario, process=process,
                         to_year=to_year)
    return float(flow[flow["year"] <= to_year]["secondary_t"].sum())
