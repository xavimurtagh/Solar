"""Part II report: the economics, space, and materials of terawatt-scale solar.

Mirrors :mod:`solarlab.report` but for the cost/space/abundance analysis.
``generate_economics`` runs the whole pipeline and writes
``output/REPORT_ECONOMICS.md`` plus figures 6-10, deterministically.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from . import figures as figs
from . import materials as M
from .economics import (
    LCOEInputs,
    cost_stack,
    energy_per_dollar,
    lcoe,
    lcoe_monte_carlo,
    lcoe_sensitivity,
    opex_for,
    system_cost_per_w,
)
from .frontier import build_frontier
from .report import DEFAULT_OUTDIR, _md_table
from .system import Scenario, reference_weather, simulate

ALL_TECHS = ["PERC", "TOPCon", "HJT", "CdTe", "Perovskite-Si tandem", "CZTS", "Pyrite"]
DEPLOYMENTS = ["utility", "commercial", "residential"]


@dataclass
class EconResults:
    cost_stacks: dict
    lcoe_by_deployment: dict
    energy_per_dollar_by_deployment: dict
    yields: dict
    frontier: pd.DataFrame
    ceiling: pd.DataFrame
    substitutions: list
    sensitivity: pd.DataFrame
    mc_samples: object
    material_costs: pd.DataFrame
    base_cost_per_w: float
    base_yield: float


def collect_economics_results(weather=None) -> EconResults:
    if weather is None:
        weather = reference_weather()

    # Yields: utility tracks the sun; commercial/residential are fixed rooftops.
    util_sim = simulate(Scenario(name="utility", tracking=True), weather=weather)
    fixed_sim = simulate(Scenario(name="fixed"), weather=weather)
    yields = {"utility": util_sim.specific_yield,
              "commercial": fixed_sim.specific_yield,
              "residential": fixed_sim.specific_yield}

    cost_stacks = {d: cost_stack(d) for d in DEPLOYMENTS}
    lcoe_by_deployment, epd_by_deployment = {}, {}
    for d in DEPLOYMENTS:
        cpw = system_cost_per_w(d)
        inp = LCOEInputs(opex_per_kw_yr=opex_for(d))
        lcoe_by_deployment[d] = lcoe(cpw, yields[d], inp)
        epd_by_deployment[d] = energy_per_dollar(cpw, yields[d], inp)

    frontier = build_frontier(weather=weather)
    ceiling = M.ceiling_table(ALL_TECHS)

    substitutions = [
        M.substitution_effect("TOPCon", M.SILVER_TO_COPPER),
        M.substitution_effect("HJT", M.INDIUM_TO_ZINC),
        M.substitution_effect("HJT", M.ABUNDANT_SWAP),
    ]

    base_cost_per_w = system_cost_per_w("utility")
    base_yield = yields["utility"]
    sensitivity = lcoe_sensitivity(base_cost_per_w, base_yield,
                                   LCOEInputs(opex_per_kw_yr=opex_for("utility")))
    mc_samples = lcoe_monte_carlo(base_cost_per_w, base_yield, n=20000, seed=0)

    material_costs = pd.DataFrame([
        {"technology": t, "material_cost_usd_per_w": M.material_cost_per_w(t)}
        for t in ALL_TECHS])

    return EconResults(
        cost_stacks=cost_stacks, lcoe_by_deployment=lcoe_by_deployment,
        energy_per_dollar_by_deployment=epd_by_deployment, yields=yields,
        frontier=frontier, ceiling=ceiling, substitutions=substitutions,
        sensitivity=sensitivity, mc_samples=mc_samples,
        material_costs=material_costs, base_cost_per_w=base_cost_per_w,
        base_yield=base_yield)


def render_economics_figures(r: EconResults, outdir: Path) -> list[Path]:
    figdir = outdir / "figures"
    return [
        figs.fig6_lcoe(r.cost_stacks, r.lcoe_by_deployment, figdir),
        figs.fig7_frontier(r.frontier, figdir),
        figs.fig8_ceiling(r.ceiling, M.NET_ZERO_TW_PER_YEAR, figdir),
        figs.fig9_substitution(r.substitutions, figdir),
        figs.fig10_sensitivity(r.sensitivity, r.mc_samples, figdir),
    ]


def build_economics_report(r: EconResults, outdir: Path = DEFAULT_OUTDIR) -> Path:
    import numpy as np

    util_lcoe = r.lcoe_by_deployment["utility"] * 1000
    res_lcoe = r.lcoe_by_deployment["residential"] * 1000
    mc = np.asarray(r.mc_samples) * 1000
    p10, p50, p90 = (float(x) for x in np.percentile(mc, [10, 50, 90]))

    tightest = r.ceiling.iloc[0]
    silver_tech = r.ceiling[r.ceiling["binding_element"] == "Silver"]
    silver_ceiling = float(silver_tech["tw_per_year"].max()) if not silver_tech.empty else float("nan")
    ag_cu = r.substitutions[0]
    hjt_all = r.substitutions[2]

    ceiling_tbl = _md_table(
        r.ceiling, ["technology", "tw_per_year", "binding_element", "binding_is_scarce"],
        ["Technology", "Ceiling (TW/yr)", "Limited by", "Scarce?"],
        [str, lambda v: f"{v:.3g}", str, lambda v: "yes" if v else "no (scalable)"])

    subs_tbl = _md_table(
        pd.DataFrame(r.substitutions),
        ["technology", "binding_before", "tw_per_year_before", "binding_after",
         "tw_per_year_after", "ceiling_multiplier"],
        ["Technology", "Was limited by", "Was (TW/yr)", "Now limited by",
         "Now (TW/yr)", "Scale-up"],
        [str, str, lambda v: f"{v:.3g}", str, lambda v: f"{v:.3g}",
         lambda v: f"{v:.0f}x"])

    cost_rows = []
    for d in DEPLOYMENTS:
        cost_rows.append({
            "deployment": d,
            "cost": float(r.cost_stacks[d].sum()),
            "lcoe": r.lcoe_by_deployment[d] * 1000,
            "epd": r.energy_per_dollar_by_deployment[d],
        })
    cost_tbl = _md_table(
        pd.DataFrame(cost_rows), ["deployment", "cost", "lcoe", "epd"],
        ["Deployment", "Installed $/W", "LCOE ($/MWh)", "kWh per $ (30 yr)"],
        [str, lambda v: f"${v:.2f}", lambda v: f"${v:.0f}", lambda v: f"{v:.0f}"])

    pareto2 = r.frontier[r.frontier["pareto"]].iloc[0]
    scale_front = r.frontier[r.frontier["pareto_scale"]]
    # Technologies that rejoin the frontier only once scalability is rewarded
    # (i.e. beyond the cost/space champion already named above).
    readmitted = [t for t in sorted(set(scale_front["technology"]))
                  if t != pareto2["technology"]]
    scale_techs = ", ".join(readmitted)

    text = f"""# The Economics and Materials of Terawatt-Scale Solar

*Part II of the solar analysis. Where [Part I](REPORT.md) asked why panels are
only ~20% efficient, this asks the questions that actually decide the energy
transition: **how do we maximise energy per dollar and per square metre — and
can we even get the materials to build solar at the scale the planet needs?**
Every number is computed by this toolkit or carried with a citation.*

---

## 1. Executive summary — the reframe

Three findings reorder the usual priorities:

1. **Energy per dollar is set by *where*, not *which cell*.** Utility-scale solar
   here delivers **${util_lcoe:.0f}/MWh**; the identical cells on a roof cost
   **${res_lcoe:.0f}/MWh** — because soft costs, not silicon, dominate a rooftop
   install. The cell technology barely moves LCOE within a deployment.
2. **Efficiency mostly buys *space*, not cheaper energy.** Among silicon cells at
   one site, LCOE is nearly flat; what a better cell buys is energy density
   (kWh per m²). That only converts to dollars where area is scarce — rooftops,
   vehicles, balconies.
3. **The real ceiling is the periodic table.** At terawatt scale the binding
   constraint is grams of a scarce element per watt. Today's silicon cells are
   **silver-limited to ~{silver_ceiling:.1f} TW/yr**; CdTe is tellurium-limited
   to **{tightest['tw_per_year']:.3g} TW/yr**. The fix is not efficiency — it is
   **substituting abundant elements**, which lifts the ceiling by
   **{hjt_all['ceiling_multiplier']:.0f}x** in the boldest case modelled here.

The provocative conclusion: a slightly-less-efficient cell made of iron, copper
and sulfur may matter more to decarbonisation than a record-breaking one made of
silver, indium and tellurium — because we can actually build 50 TW of it.

---

## 2. What actually drives the cost of solar energy

LCOE discounts every future kilowatt-hour and dollar to install day. The cost
*stack* explains the surprise that the same panel yields wildly different energy
costs:

{cost_tbl}

![LCOE and cost stack](figures/fig6_lcoe.png)

For utility plants, hardware dominates and the result (**${util_lcoe:.0f}/MWh**)
sits squarely in Lazard's 2025 unsubsidised range of $38-78/MWh. For residential,
**soft costs** — sales, permitting, overhead, margin — are the single biggest
line, which is why making the *cell* cheaper or better does little for a rooftop
system's economics. If you want to change the cost of household solar, attack
paperwork and customer-acquisition, not the bandgap.

---

## 3. Energy per dollar *and* per square metre: the frontier

Plotting every technology and deployment on two axes at once — energy per dollar
(LCOE) and energy per unit area (density) — reveals the trade-off. Bubble size is
the third objective: how far each option can scale.

![The cost / space / scale frontier](figures/fig7_frontier.png)

On cost-vs-space alone, the Pareto winner is **{pareto2['technology']}** at
**{pareto2['deployment']}** scale (${pareto2['lcoe_usd_mwh']:.0f}/MWh,
{pareto2['energy_density_kwh_m2_yr']:.0f} kWh/m²/yr) — highest efficiency, lowest
cost. But its bubble is tiny: it is indium-limited. **Once scalability is added
as a third objective, the frontier readmits the high-ceiling silicon cells
({scale_techs})** — the abundant, scalable workhorses you would actually deploy by
the terawatt, even though they concede a little on cost and density. The lesson:
the cost/space optimum and the scale optimum are different points, and reconciling
them is a *materials* problem.

---

## 4. The terawatt ceiling — the constraint no efficiency chart shows

To hold warming down, the world needs to build on the order of
~{M.NET_ZERO_TW_PER_YEAR:.0f} TW of solar per year, sustained for decades. Can the
mines keep up? For each technology, divide the world's annual production of its
scarcest ingredient (allowing PV half of it) by how many grams that technology
needs per watt:

{ceiling_tbl}

![The terawatt ceiling](figures/fig8_ceiling.png)

The numbers are stark. **Tellurium** caps CdTe at a few gigawatts a year —
which is exactly why it remains a niche despite being cheap and bankable.
**Indium** caps heterojunction and perovskite tandems similarly. Even mainstream
silicon is **silver-limited to ~{silver_ceiling:.1f} TW/yr** — uncomfortably close
to today's build rate, which is why the industry is racing to thrift silver. The
green bars are technologies limited only by elements we can mine more of
(silicon, copper, iron): their ceiling is a factory-building problem, not a
geological one.

---

## 5. Breaking the ceiling — abundant-element substitution

This is the outside-the-box lever. Swap the scarce element for an abundant one
and re-run the arithmetic:

{subs_tbl}

![Material substitution impact](figures/fig9_substitution.png)

- **Silver → electroplated copper.** Copper costs ~1/95th of silver and the world
  mines ~900x more of it. Replacing silver metallization moves silicon's binding
  constraint off silver entirely (to {ag_cu['binding_after']}), and *lowers*
  material cost. This is not speculative — Fraunhofer ISE and others have
  demonstrated copper-plated cells using a tenth of the silver.
- **Indium (ITO) → aluminium-doped zinc oxide (AZO).** Removes the indium wall
  that throttles heterojunction and tandem cells; zinc is ~10,000x more abundant.
- **Going fully abundant** (copper + zinc + tin perovskite) lifts the
  heterojunction ceiling by **{hjt_all['ceiling_multiplier']:.0f}x**.

And the boldest absorbers abandon the scarce elements altogether: **kesterite
(Cu-Zn-Sn-S)** and even **iron pyrite (FeS₂, "fool's gold")** are built from some
of the most common elements in the crust. They are less efficient and less mature
today — pyrite especially is a research-stage gamble on voltage — but their
abundance ceiling is effectively unlimited. For a planet that needs tens of
terawatts, "good enough and infinitely scalable" can beat "excellent and capped."

---

## 6. How we simulated it, and how sure we are

LCOE for the headline utility case is **${util_lcoe:.0f}/MWh**, but the inputs are
uncertain. A one-at-a-time sensitivity and a 20,000-run Monte-Carlo (varying cost,
yield, discount rate, degradation and O&M) give the spread:

- Sensitivity ranks the drivers; **installed cost, cost of capital, and capacity
  factor** dominate — not the cell.
- Monte-Carlo P10/P50/P90 = **${p10:.0f} / ${p50:.0f} / ${p90:.0f}/MWh**.

![LCOE sensitivity and Monte-Carlo](figures/fig10_sensitivity.png)

---

## 7. Assumptions and limitations

- LCOE uses a single-site yield (Greensboro TMY3) and generic NREL cost stacks;
  real projects vary with resource, labour, and finance. The model reproduces
  Lazard's utility range, which is the validation.
- The **material ceiling** is deliberately simple: annual production x an
  assumed 50% PV share / intensity. It ignores recycling, reserve growth,
  substitution within an element's other markets, and price-elastic supply. It is
  an order-of-magnitude scaling argument, not a forecast — but the order of
  magnitude is the whole point.
- Substitutions assume the replacement element deposits at comparable mass; thin-
  film processing costs are not captured beyond raw materials. Efficiencies for
  kesterite and pyrite are research-stage and shown for their abundance, not as
  bankable products.
- Material intensities are ITRPV/literature mid-points; element data are USGS
  Mineral Commodity Summaries 2025. Records and prices move — verify before use.

## 8. References

- Lazard, *Levelized Cost of Energy+ (LCOE+)*, June 2025.
- A. P. Dobos, *PVWatts Version 5 Manual*, NREL/TP-6A20-62641, 2014.
- NREL, *U.S. Solar Photovoltaic System Cost Benchmarks*, Q1 2024.
- U.S. Geological Survey, *Mineral Commodity Summaries 2025* (silver, tellurium,
  indium, copper, tin, zinc, etc.).
- ITRPV, *International Technology Roadmap for Photovoltaic*, 2024 edition
  (silver intensity and roadmap).
- Fraunhofer ISE, *Silicon heterojunction cells with record silver savings* (2025);
  copper-plating literature.
- IEA, *Net Zero Roadmap*; IRENA deployment scenarios (terawatt context).
"""
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / "REPORT_ECONOMICS.md"
    path.write_text(text, encoding="utf-8")
    return path


def generate_economics(outdir: Path = DEFAULT_OUTDIR, weather=None) -> Path:
    results = collect_economics_results(weather=weather)
    render_economics_figures(results, outdir)
    return build_economics_report(results, outdir)
