"""Part V report: the techno-economic optimiser.

``generate_optimizer`` runs a few canonical decision scenarios, shows how the
optimal technology flips with the binding constraint, and writes
``output/REPORT_OPTIMIZER.md`` plus figure 16.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from . import figures as figs
from .frontier import build_frontier
from .optimizer import Constraints, optimize
from .report import DEFAULT_OUTDIR, _md_table


@dataclass
class OptResults:
    area_limited: dict
    budget_limited: dict
    min_lcoe: dict
    frontier: pd.DataFrame


# Canonical worked examples.
AREA_LIMITED = Constraints(area_m2=40, budget_usd=80_000, deployment="residential")
BUDGET_LIMITED = Constraints(budget_usd=1_000_000, area_m2=1e9, deployment="utility")


def collect_optimizer_results(weather=None) -> OptResults:
    frontier = build_frontier(weather=weather)
    return OptResults(
        area_limited=optimize("max_energy", AREA_LIMITED, frontier_df=frontier),
        budget_limited=optimize("max_energy", BUDGET_LIMITED, frontier_df=frontier),
        min_lcoe=optimize("min_lcoe", Constraints(), frontier_df=frontier),
        frontier=frontier)


def render_optimizer_figures(r: OptResults, outdir: Path) -> list[Path]:
    figdir = outdir / "figures"
    scenarios = [
        ("(a) Area-limited rooftop (40 m²)", r.area_limited["ranked"],
         r.area_limited["best"]["technology"]),
        ("(b) Budget-limited utility ($1M)", r.budget_limited["ranked"],
         r.budget_limited["best"]["technology"]),
    ]
    return [figs.fig16_optimizer(scenarios, figdir)]


def build_optimizer_report(r: OptResults, outdir: Path = DEFAULT_OUTDIR) -> Path:
    a = r.area_limited["best"]
    b = r.budget_limited["best"]
    lc = r.min_lcoe["best"]

    def pick_table(result):
        d = result["ranked"].head(4)
        return _md_table(
            d, ["technology", "deployment", "capacity_kw", "annual_kwh", "total_cost_usd"],
            ["Technology", "Deployment", "Capacity (kW)", "Annual kWh", "Cost ($)"],
            [str, str, lambda v: f"{v:,.1f}", lambda v: f"{v:,.0f}",
             lambda v: f"{v:,.0f}"])

    text = f"""# The Optimiser: Which Cell Wins, and Why

*Part V. Parts I-IV map the trade-offs; this part makes the decision. Given a
budget, an available area, and a goal, the optimiser searches every technology
and deployment and returns the best choice — and, crucially, *which constraint
binds*, so the recommendation is explained rather than asserted.*

---

## 1. The optimal technology is not fixed — it flips with the constraint

![Optimiser: the winner flips with the binding constraint](figures/fig16_optimizer.png)

**When area binds, efficiency wins.** On a fixed {AREA_LIMITED.area_m2:.0f} m²
roof, every square metre must work as hard as possible, so the optimiser picks
**{a['technology']}** — the highest-efficiency cell — delivering
**{a['annual_kwh']:,.0f} kWh/yr** ({a['capacity_kw']:.1f} kW) even though it costs
the most per watt. Binding constraint: **{r.area_limited['binding']}**.

{pick_table(r.area_limited)}

**When money binds, the cheapest energy wins.** With a fixed
${BUDGET_LIMITED.budget_usd:,.0f} budget and ample land, the optimiser instead
picks **{b['technology']}** — the *least* expensive cell — because more dollars
go to capacity, yielding **{b['annual_kwh']:,.0f} kWh/yr** ({b['capacity_kw']:,.0f}
kW). The premium cell's higher efficiency cannot overcome its higher price here.
Binding constraint: **{r.budget_limited['binding']}**.

{pick_table(r.budget_limited)}

This flip is the whole point: there is no single "best" cell. Efficiency is
worth paying for exactly when space — not money — is the limiting resource:
rooftops, vehicles, balconies, satellites. For open land, the cheapest reliable
watt wins.

## 2. Lowest cost of energy, overall

Ignoring size and asking only for the cheapest energy, the optimiser returns
**{lc['technology']} at {lc['deployment']} scale** at **${lc['lcoe_usd_mwh']:.0f}/MWh**
— the utility-scale, high-efficiency combination that anchors the cost frontier.

## 3. How to use it

```python
from solarlab.optimizer import optimize, Constraints
optimize("max_energy", Constraints(area_m2=40, budget_usd=80_000,
                                   deployment="residential"))
optimize("min_cost_for_target", Constraints(target_kwh=10_000, area_m2=40))
```

The optimiser is a thin, transparent layer over the frontier: it sizes each
option against the budget and area, ranks by the chosen objective, and reports
the binding constraint. Swap in a different location's weather, cost stack, or
technology list and the recommendation updates.

## 4. Assumptions and limitations

- Technology module premiums (PERC < TOPCon < HJT << tandem) are typical 2024
  spreads; the *direction* of the flip is robust, the exact crossover budget is
  not.
- One site and one cost stack per deployment; a real quote varies with resource,
  labour, and finance.
- The search space is the discrete frontier (4 technologies x 3 deployments);
  it does not co-optimise tilt, tracking, or storage — those are the levers of
  Parts I and IV.

## 5. References

- Builds on the cost model (Part II, Lazard/NREL) and the system simulation
  (Part I, pvlib). Module price spreads from ITRPV 2024 / market data.
"""
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / "REPORT_OPTIMIZER.md"
    path.write_text(text, encoding="utf-8")
    return path


def generate_optimizer(outdir: Path = DEFAULT_OUTDIR, weather=None) -> Path:
    results = collect_optimizer_results(weather=weather)
    render_optimizer_figures(results, outdir)
    return build_optimizer_report(results, outdir)
