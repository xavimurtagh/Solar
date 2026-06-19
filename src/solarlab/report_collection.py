"""Part XVI report: the collection problem — digging up the urban mine."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from . import collection as COL
from . import figures as figs
from .report import DEFAULT_OUTDIR, _md_table


@dataclass
class CollectionResults:
    runway: pd.DataFrame
    thrift: pd.DataFrame
    econ: COL.RecyclingEconomics
    regional: dict


def collect_collection_results(weather=None) -> CollectionResults:
    return CollectionResults(
        runway=COL.runway_vs_collection(),
        thrift=COL.silver_thrift_effect(),
        econ=COL.recycling_economics(),
        regional=COL.REGIONAL_COLLECTION)


def render_collection_figures(r: CollectionResults, outdir: Path) -> list[Path]:
    econ = {"recycle_cost": r.econ.recycle_cost_t, "landfill_cost": r.econ.landfill_cost_t}
    return [figs.fig30_collection(r.runway, r.thrift, r.regional, econ,
                                  outdir / "figures")]


def _runway_at(df, collection):
    return df.iloc[(df["collection"] - collection).abs().idxmin()]


def build_collection_report(r: CollectionResults, outdir: Path = DEFAULT_OUTDIR) -> Path:
    e = r.econ
    at_global = _runway_at(r.runway, 0.20)
    at_high = _runway_at(r.runway, 0.85)
    cu = r.thrift[r.thrift["silver_mg_per_w"] == 0.0].iloc[0]
    ag = r.thrift[r.thrift["silver_mg_per_w"] == 13.0].iloc[0]

    tbl = _md_table(
        r.runway[r.runway["collection"].isin([0.0, 0.2, 0.5, 0.85, 0.95])],
        ["collection", "closed_loop", "virgin_share_of_production", "runway_years"],
        ["Collection rate", "Loop closed", "Virgin metal (% of world prod.)", "Runway"],
        [lambda v: f"{v*100:.0f}%", lambda v: f"{v*100:.0f}%",
         lambda v: f"{v*100:.0f}%", lambda v: f"{v:.0f} yr"])

    text = f"""# The Collection Problem: The Urban Mine Only Counts If We Dig It Up

*Part XVI — the least glamorous and possibly most important analysis in the project.
Part XIII proved solar can be materially renewable with a tight recycling loop. But
"the loop" quietly assumed we **collect** ~90% of retired panels. We don't —
globally, formal collection is in the low tens of percent. This part makes
collection the variable it really is, and the result reframes recycling from a
technology problem into a **logistics and policy** problem.*

---

## 1. Collection, not the recycler, is the binding constraint

Hold the recycler at best practice (95% recovery, 99% refining) and vary only how
many retired panels actually reach it:

{tbl}

![Collection rate and recycling economics](figures/fig30_collection.png)

The curve is brutal in its honesty. Below about **50% collection — which is where
most of the world sits today** — the loop leaks so badly that the multi-century
runway of Part XIII collapses back toward the ~30-year no-recycling cliff. At a
realistic **global ~20%** collection rate, the runway is just **{at_global['runway_years']:.0f}
years** and fresh mining still swallows **{at_global['virgin_share_of_production']*100:.0f}%**
of world silver production. Push collection to **85%** (the EU's WEEE mandate level)
and it leaps to **{at_high['runway_years']:.0f} years**.

The uncomfortable implication: **the world's best recycling technology is worthless
on a pile of panels nobody collected.** All the elegant chemistry of Part III, all
the closed-loop math of Part XIII, hinges on a mundane question — does the dead
panel get picked up, or dumped?

## 2. The economics quietly push the wrong way

Why is collection so low? Because the disposer's incentives point at the landfill.
A tonne of retired modules holds about **${e.recovered_value_t:.0f}** of recoverable
material, and high-value recycling costs about **${e.recycle_cost_t:.0f}/tonne** — so
recovery is genuinely **net-positive (~${e.net_value_t:.0f}/tonne)**. But the person
holding the panel doesn't see that value; they see a choice between *paying*
${e.recycle_cost_t:.0f} to recycle or ${e.landfill_cost_t:.0f} to landfill. **Landfill
is ${e.incentive_gap_t:.0f}/tonne cheaper**, so unless the recovered value is captured
by whoever pays — or a law forbids the landfill — the panel gets dumped.

## 3. The cruel twist: copper makes it worse

And here is the sharp interaction that ties this part to Part XII. The reason a
retired panel is worth recovering at all is mostly the **silver** inside it. As the
industry thrifts silver down and switches to **copper** metallisation — exactly the
move that fixes the supply ceiling (Parts II, XII) — the recoverable value falls:

- Today (13 mg/W silver): ~${ag['recovered_value_t']:.0f}/tonne, net ~${ag['net_value_t']:.0f}.
- Copper era (no silver): ~${cu['recovered_value_t']:.0f}/tonne, net ~${cu['net_value_t']:.0f}.

So the very transition that makes solar *scalable* makes its panels *less worth
recycling* — the recovery margin shrinks by two-thirds. **The copper era will need
more policy to drive collection, not less.** Solving the supply problem quietly
deepens the collection problem.

## 4. What actually fixes it

The good news: this is a solved problem in principle, with a working precedent.

- **Extended Producer Responsibility (EPR).** Make the manufacturer responsible for
  the panel's end of life. The EU's WEEE directive already covers PV and drives
  ~80% collection — which, the curve above shows, is the difference between a
  30-year cliff and a 150-year runway.
- **Deposit / take-back schemes.** A refundable fee at sale that is repaid on
  return turns the disposer's incentive from "dump it cheaply" to "claim my deposit".
- **Design for disassembly.** Panels built to come apart (recyclable encapsulants,
  separable frames) cut the recycling cost, widening the net-positive margin.
- **Mandated landfill bans** for PV, closing the cheap exit entirely.

None of these are technologies. They are **rules and logistics** — and they are the
cheapest, highest-leverage climate intervention hiding in this entire project. We
spent fifteen parts on physics, cost, materials, and orbits. The thing most likely
to decide whether solar is *truly* renewable is whether a truck shows up to collect
the old panels.

## 5. Assumptions and limitations

- Collection rates are representative; precise figures vary by region and year, and
  "collection" blurs into reuse/export (which often just defers the problem).
- Recovered-material values use discounted recovered prices; recycling and landfill
  costs are mid-range estimates that vary widely by location and process.
- The steady-state fleet framing follows Part XIII; during growth the picture is
  tighter still.

## 6. References

- IRENA & IEA-PVPS, *End-of-Life Management: Solar PV Panels* (collection, value).
- EU WEEE Directive (PV included); extended-producer-responsibility literature.
- Global e-waste collection statistics (the low-tens-of-percent reality).
"""
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / "REPORT_COLLECTION.md"
    path.write_text(text, encoding="utf-8")
    return path


def generate_collection(outdir: Path = DEFAULT_OUTDIR, weather=None) -> Path:
    results = collect_collection_results(weather=weather)
    render_collection_figures(results, outdir)
    return build_collection_report(results, outdir)
