"""Orchestration: compute everything, render the figures and the report.

``collect_results`` runs the whole analysis once and returns the numbers;
``build_report`` turns those numbers into ``output/REPORT.md`` with every value
either computed here or carried with a citation.  No timestamps are written, so
re-running produces a byte-identical report (a property the tests check).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from . import constants as C
from . import figures as figs
from .history import (
    improvement_stats,
    lab_to_market_gap,
    load_milestones,
    load_module_market,
)
from .levers import BASE, run_levers
from .spectrum import SpectrumIntegrals, load_am15g
from .sq import optimal_bandgap, optimal_tandem, sq_cell
from .system import simulate
from .waterfall import build_waterfall

DEFAULT_OUTDIR = Path("output")


@dataclass
class Results:
    spectrum_source: str
    spec: SpectrumIntegrals
    opt: object
    si: object
    gaas: object
    tandem: dict
    milestones: pd.DataFrame
    market: pd.DataFrame
    improvement: pd.DataFrame
    gap: dict
    sim: object
    levers: pd.DataFrame
    waterfall: pd.DataFrame


def collect_results(weather=None) -> Results:
    """Run the full analysis pipeline once and return all computed results."""
    spectrum = load_am15g()
    spec = SpectrumIntegrals(spectrum)

    opt = optimal_bandgap(spec)
    si = sq_cell(C.SI_EG_EV, spec)
    gaas = sq_cell(C.GAAS_EG_EV, spec)
    tandem = optimal_tandem(spec)

    milestones = load_milestones()
    market = load_module_market()
    improvement = improvement_stats(milestones)
    gap = lab_to_market_gap(milestones, market)

    sim = simulate(BASE, weather=weather)
    levers = run_levers(weather=weather)
    waterfall = build_waterfall(spec, sim)

    return Results(
        spectrum_source=spectrum.attrs.get("source", "unknown"),
        spec=spec, opt=opt, si=si, gaas=gaas, tandem=tandem,
        milestones=milestones, market=market, improvement=improvement,
        gap=gap, sim=sim, levers=levers, waterfall=waterfall,
    )


def render_figures(results: Results, outdir: Path) -> list[Path]:
    """Write all five figures and return their paths."""
    figdir = outdir / "figures"
    return [
        figs.fig1_sq_limit(results.spec, figdir),
        figs.fig2_waterfall(results.waterfall, figdir),
        figs.fig3_history(results.milestones, results.market, figdir),
        figs.fig4_levers(results.levers, figdir),
        figs.fig5_seasonal(results.sim.monthly, figdir),
    ]


def _md_table(df: pd.DataFrame, cols, headers, fmts) -> str:
    line = "| " + " | ".join(headers) + " |\n"
    line += "| " + " | ".join("---" for _ in headers) + " |\n"
    for _, row in df.iterrows():
        cells = [fmt(row[c]) for c, fmt in zip(cols, fmts)]
        line += "| " + " | ".join(cells) + " |\n"
    return line


def build_report(results: Results, outdir: Path = DEFAULT_OUTDIR) -> Path:
    """Render output/REPORT.md from computed results. Figures must exist first."""
    r = results
    sim = r.sim
    system_eff = sim.scenario.module_eff * sim.pr * 100.0
    top_lever = r.levers.iloc[0]

    waterfall_tbl = _md_table(
        r.waterfall, ["stage", "eta_pct", "loss_label", "source"],
        ["Stage", "Efficiency", "Principal loss to next stage", "Source"],
        [str, lambda v: f"{v:.1f}%", str, str])

    levers_tbl = _md_table(
        r.levers, ["lever", "delta_pct", "note", "source"],
        ["Lever", "Annual energy gain", "What it changes", "Source"],
        [str, lambda v: f"+{v:.1f}%", str, str])

    attribution_tbl = _md_table(
        sim.attribution, ["stage", "energy_kwh", "pct_of_poa_ideal", "loss_label"],
        ["Stage", "Energy (kWh)", "% of POA-ideal", "Loss"],
        [str, lambda v: f"{v:,.0f}", lambda v: f"{v:.1f}%", str])

    improvement_tbl = _md_table(
        r.improvement, ["technology", "first_year", "first_pct", "latest_year",
                        "latest_pct", "pp_per_decade"],
        ["Technology", "First", "First %", "Latest", "Latest %", "pp/decade"],
        [str, lambda v: f"{int(v)}", lambda v: f"{v:.1f}", lambda v: f"{int(v)}",
         lambda v: f"{v:.1f}", lambda v: ("n/a" if v != v else f"{v:.2f}")])

    text = f"""# Why Solar Panels Are Only ~20% Efficient — and How to Change That

*A first-principles analysis. Every number below is either computed by this
toolkit or carried with a citation. Regenerate with `python -m solarlab report`.*

Spectrum: **{r.spectrum_source}**. Reference site: **{C.SITE_NAME}**.
Data curated as of **{C.DATA_AS_OF}**; check the NREL Best Research-Cell
Efficiency chart for newer records.

---

## 1. Executive summary — the five-number answer

A typical rooftop panel turns about a fifth of the sunlight that hits it into
electricity. That is not one failure but a *chain* of them, and only the first
is fundamental physics:

1. **The physics ceiling is ~34%, not 100%.** A perfect single-junction cell at
   the best bandgap is capped at **{r.opt.eta*100:.1f}%** ({r.opt.eg_ev:.2f} eV)
   by the Shockley-Queisser limit. Silicon sits at **{r.si.eta*100:.1f}%**.
2. **Real silicon physics trims it to {C.RICHTER_SI_LIMIT_PCT}%** through
   unavoidable Auger recombination.
3. **The best laboratory cell reaches {C.SI_LAB_RECORD_PCT}%**; the best
   *commercial* module about {C.SI_MODULE_STC_PCT}%.
4. **A deployed system delivers ~{system_eff:.0f}% of incident energy as annual
   AC** (performance ratio {sim.pr:.2f}) once temperature, soiling, wiring and
   inverter losses are counted — simulated here at {sim.specific_yield:.0f}
   kWh/kWp.
5. **The biggest single lever today is the tandem cell.** Stacking a perovskite
   on silicon already beats silicon's single-junction limit in the lab
   (**{r.milestones[r.milestones.technology=='Perovskite-Si tandem'].efficiency_pct.max():.1f}%**)
   and, in this simulation, a tandem module returns **+{top_lever.delta_pct:.0f}%**
   more annual energy on the same roof.

The headline, then: ~20% is mostly *physics plus engineering maturity*, and the
path forward is **multi-junction cells to break the physics ceiling** plus
**well-understood system engineering** to stop losing what the cell already
makes.

![Shockley-Queisser limit](figures/fig1_sq_limit.png)

---

## 2. The physics ceiling: detailed balance and the {r.opt.eta*100:.0f}% limit

In 1961 Shockley and Queisser asked the cleanest possible question: ignore every
manufacturing defect — what is the *best a single-junction cell could ever do*?
Their answer follows from two facts. First, a semiconductor only absorbs photons
with energy above its bandgap `Eg`. Second, a cell warm enough to work must also
*emit* thermal radiation (detailed balance), which sets a hard floor on its dark
current and therefore a ceiling on its voltage.

Four unavoidable losses follow, shown for silicon ({C.SI_EG_EV} eV):

- **Sub-bandgap transmission — {_pct(r, 'below_gap')}:** photons redder than the
  bandgap pass straight through. Lowering the bandgap captures more of them...
- **Thermalisation — {_pct(r, 'thermalisation')}:** ...but every photon *bluer*
  than the bandgap wastes its excess energy as heat. These two losses pull in
  opposite directions, and their tug-of-war is exactly why the efficiency curve
  has a peak near 1.3 eV.
- **Thermodynamic / voltage loss — {_pct(r, 'voltage_boltzmann')}:** the
  open-circuit voltage is forced below `Eg/q` by the cell's own thermal emission.
- **Fill-factor loss — {_pct(r, 'fill_factor')}:** the current-voltage curve is
  not a perfect rectangle.

What is left — **{_pct(r, 'extracted')}** for silicon — is the most a flawless
single-junction silicon cell could deliver. The toolkit computes these five
shares to sum to exactly 100% (checked to 1e-9). The single-junction optimum is
**{r.opt.eta*100:.1f}%** at {r.opt.eg_ev:.2f} eV; GaAs ({C.GAAS_EG_EV} eV) reaches
**{r.gaas.eta*100:.1f}%**.

**The way around the ceiling is to stop using one junction.** A two-junction
tandem — a wide-gap top cell over a narrow-gap bottom cell — splits the spectrum
and cuts both the sub-bandgap and thermalisation losses. The detailed-balance
limit for the ideal pair is **{r.tandem['eta']*100:.1f}%**
({r.tandem['eg_top']:.2f} eV / {r.tandem['eg_bot']:.2f} eV), and this is no longer
theoretical: perovskite-on-silicon tandems have passed silicon's single-junction
limit in the laboratory.

---

## 3. From {r.si.eta*100:.0f}% to ~{system_eff:.0f}%: the loss waterfall

Each rung below names what is lost reaching the next. The first drop is physics;
everything after it is engineering — which means everything after it is
*addressable*.

{waterfall_tbl}

![Efficiency waterfall](figures/fig2_waterfall.png)

---

## 4. Seventy years of progress (and why $/kWh, not %, is the real prize)

Silicon went from {r.gap['best_cell_pct']:.1f}% in the lab while the commercial
fleet still averages {r.gap['market_pct']:.1f}% — a standing **{r.gap['gap_pp']:.1f}
percentage-point** lab-to-market gap. Progress by technology:

{improvement_tbl}

![Efficiency records over time](figures/fig3_history.png)

But efficiency is only half the story. Between 2010 and 2024 module prices fell
from about \\${r.market.iloc[0]['module_price_usd_per_w']:.2f}/W to
\\${r.market.iloc[-1]['module_price_usd_per_w']:.2f}/W while average efficiency
rose from {r.market.iloc[0]['avg_module_eff_pct']:.0f}% to
{r.market.iloc[-1]['avg_module_eff_pct']:.0f}%. The industry's true objective is
the **levelised cost of energy** (\\$/kWh), and a cheaper 20% panel often beats a
pricier 24% one. Efficiency matters most where area is scarce (rooftops, vehicles)
or where it reduces every area-proportional balance-of-system cost at once.

---

## 5. A real rooftop, hour by hour

To get honest *system* numbers rather than datasheet ones, the toolkit simulates
a {BASE.pdc0_w/1000:.0f} kW {BASE.racking.replace('_', ' ')} array for a full
8760-hour year at {C.SITE_NAME} (pvlib, Hay-Davies transposition, Sandia thermal
model, PVWatts losses).

- Plane-of-array irradiation: **{sim.poa_kwh_m2:.0f} kWh/m²**
- Annual AC energy: **{sim.e_ac_kwh:,.0f} kWh** ({sim.specific_yield:.0f} kWh/kWp)
- Performance ratio: **{sim.pr:.2f}**; effective system efficiency
  **{sim.eta_system*100:.1f}%**

{attribution_tbl}

![Seasonal yield and temperature](figures/fig5_seasonal.png)

Temperature is the quiet thief: cells run far hotter than the 25 °C of their
datasheet, and silicon loses roughly 0.34% of its power per degree above it —
worst exactly when the sun is strongest.

---

## 6. How to actually improve efficiency

Ranking concrete changes to the reference system by the extra annual energy each
delivers (technology swaps compared on a **fixed roof area**, so a better module
simply fits more watts on the same roof):

{levers_tbl}

![Improvement levers ranked](figures/fig4_levers.png)

**Reading the ranking:**

- **Tandems are the structural breakthrough.** They are the only lever that
  raises the *cell's* ceiling rather than recovering system losses, and they are
  moving from lab to market now. This is where efficiency-limited research should
  concentrate.
- **Tracking and bifaciality** are large, mature gains for ground-mounted plant.
- **Cooling, anti-soiling, better inverters and module-level electronics** are
  smaller but cheap, reliable, and additive — collectively a meaningful slice of
  the {100-system_eff:.0f} points lost between the module rating and delivered AC.

If the goal is to change the energy industry, the two-front strategy is clear:
**push multi-junction cells to break the {r.opt.eta*100:.0f}% physics ceiling**,
and **deploy the boring, proven system engineering** that stops us wasting what
today's cells already produce.

---

## 7. Assumptions and limitations

- Detailed-balance model assumes unity quantum efficiency, radiative-only
  recombination, a single sun, and a 300 K cell; it is an *upper bound*, not a
  device simulation.
- The tandem model is two-terminal, series-constrained, and ignores luminescent
  coupling, so its limit is conservative.
- The system simulation omits angle-of-incidence/IAM reflection, snow, and
  explicit shading; bifacial and availability gains are applied as constant
  factors; one TMY3 site stands in for "a rooftop".
- Record efficiencies are curated with citations and tested by *range*, not exact
  value, because records move. Verify against the NREL chart.

## 8. References

- W. Shockley & H. J. Queisser, *Detailed Balance Limit of Efficiency of p-n
  Junction Solar Cells*, J. Appl. Phys. 32, 510 (1961).
- S. Rühle, *Tabulated values of the Shockley-Queisser limit for single junction
  solar cells*, Solar Energy 130, 139 (2016).
- A. Richter, M. Hermle & S. W. Glunz, *Reassessment of the Limiting Efficiency
  for Crystalline Silicon Solar Cells*, IEEE J. Photovoltaics 3(4), 2013.
- A. P. Dobos, *PVWatts Version 5 Manual*, NREL/TP-6A20-62641, 2014.
- NREL, *Best Research-Cell Efficiency Chart* (2026).
- Fraunhofer ISE, *Photovoltaics Report* (2024); ITRPV roadmap.
- W. F. Holmgren et al., *pvlib python*, J. Open Source Software 3(29), 884 (2018).
"""
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / "REPORT.md"
    path.write_text(text, encoding="utf-8")
    return path


def _pct(r: Results, key: str) -> str:
    from .sq import loss_fractions
    return f"{loss_fractions(C.SI_EG_EV, r.spec)[key]*100:.0f}%"


def generate(outdir: Path = DEFAULT_OUTDIR, weather=None) -> Path:
    """Full pipeline: compute, render figures, write the report."""
    results = collect_results(weather=weather)
    render_figures(results, outdir)
    return build_report(results, outdir)
