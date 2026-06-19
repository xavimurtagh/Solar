"""Part XII report: the copper question — efficiency, longevity, and LCOE."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from . import figures as figs
from . import materials as M
from .metallization import breakeven_degradation, comparison, degradation_sweep
from .report import DEFAULT_OUTDIR, _md_table


@dataclass
class MetalResults:
    comparison: pd.DataFrame
    sweep: pd.DataFrame
    breakeven: dict
    silver_ceiling: float
    copper_ceiling: float


def collect_metal_results(weather=None) -> MetalResults:
    comp = comparison()
    sweep = degradation_sweep()
    be = breakeven_degradation()
    silver_ceiling = M.deployment_ceiling("TOPCon")["tw_per_year"]
    copper_ceiling = M.deployment_ceiling("TOPCon", swaps=M.SILVER_TO_COPPER)["tw_per_year"]
    return MetalResults(comparison=comp, sweep=sweep, breakeven=be,
                        silver_ceiling=silver_ceiling, copper_ceiling=copper_ceiling)


def render_metal_figures(r: MetalResults, outdir: Path) -> list[Path]:
    return [figs.fig26_metallization(r.comparison, r.sweep, r.breakeven,
                                     outdir / "figures")]


def build_metal_report(r: MetalResults, outdir: Path = DEFAULT_OUTDIR) -> Path:
    silver = r.comparison.iloc[0]
    cu_nom = r.comparison.iloc[1]
    cu_caut = r.comparison.iloc[2]
    extra = r.breakeven["extra_degradation_tolerated"] * 100

    tbl = _md_table(
        r.comparison, ["name", "metal_cost_per_w", "degradation", "lifetime_years",
                       "lcoe_usd_mwh"],
        ["Metallisation", "Metal+process cost", "Degradation", "Lifetime", "LCOE"],
        [str, lambda v: f"${v*1000:.1f}/kW", lambda v: f"{v*100:.2f}%/yr",
         lambda v: f"{int(v)} yr", lambda v: f"${v:.2f}/MWh"])

    text = f"""# The Copper Question: Is Silver's Replacement Actually as Good?

*Part XII. Earlier parts called copper metallisation a near-free win — but that was
only ever a cost-and-abundance argument. It never modelled what copper does to a
cell's **efficiency** or **lifetime**. This part closes that gap, and the answer is
more interesting (and more honest) than "copper saves money".*

---

## 1. What copper actually does to a cell

Real engineering, three effects:

- **Efficiency: neutral, even slightly positive.** Copper is only ~6% more
  resistive than silver — negligible. And cells don't use pure silver; they use
  screen-printed silver *paste*, which is less conductive than it sounds.
  Electroplated copper is more conductive than that paste and forms narrower,
  taller lines, so **less of the cell is shaded** and a touch more light gets in.
  Copper-plated cells have matched and even set efficiency records. We model copper
  as marginally *better*, not worse.
- **Longevity: the genuine question.** Copper diffuses into silicon and poisons it
  if it reaches the active layer — so plated copper needs a **barrier** (a nickel
  underlayer; in heterojunction cells the transparent-oxide layer does the job for
  free). Copper also corrodes more readily than silver, so it needs capping and
  good sealing. None of this is fatal — it is solved in the lab and entering mass
  production — but the **field track record is years, not the ~30 silver has**.
- **Cost: a small saving, net of a new process.** Silver removed is worth more than
  the plating added, but the net is modest.

## 2. The like-for-like LCOE

Holding everything else equal and propagating these through the cost-of-energy:

{tbl}

![Copper vs silver metallisation](figures/fig26_metallization.png)

The uncomfortable result: on a whole-system basis, **copper barely wins**. Silver
comes in at **${silver['lcoe_usd_mwh']:.2f}/MWh** and nominal copper at
**${cu_nom['lcoe_usd_mwh']:.2f}/MWh** — a difference of cents. And it is fragile:
the moment copper's reliability slips (the "cautious" case: faster degradation, a
25-year life), its cost jumps to **${cu_caut['lcoe_usd_mwh']:.2f}/MWh** — *more
expensive than proven silver*. The break-even is brutal: copper can tolerate only
about **+{extra:.2f} percentage points per year** of extra degradation before the
saving vanishes.

**Why so thin?** Because silver, for all the headlines, is only ~1% of a finished
system's cost. Saving it barely moves the LCOE needle. So if the case for copper
were *only* cost, it would be a coin-flip riding on long-term reliability data we
do not yet have.

## 3. The real reason copper matters

The case for copper was never LCOE. It is **abundance** (Part III). At today's
intensity, silver caps silicon PV at about **{r.silver_ceiling:.1f} TW/year** of
manufacturing even if solar took half the world's silver. Switch to copper and that
ceiling rises to **~{r.copper_ceiling:.0f} TW/year** — effectively unlimited.

So the honest framing is:

- **At the system level**, copper is roughly LCOE-neutral — a small saving that a
  reliability penalty could erase.
- **At the module-maker's level**, silver is a much bigger share of *module* cost
  (not system cost), so the saving is real and is why manufacturers are switching.
- **At the planet's level**, copper is non-negotiable: you simply cannot build
  tens of terawatts a year on silver, at any LCOE.

Copper is not a way to make solar cheaper. It is a way to make solar **possible at
scale** — provided the reliability question, which this model flags but cannot
settle, is closed by field data. That is the honest version of the story the
earlier parts told too breezily.

## 4. Assumptions and limitations

- Efficiency and reliability deltas are representative, not measured; the model's
  job is to show the *sensitivity*, not to certify a product. The conclusion —
  that LCOE is reliability-limited and the real case is abundance — is robust to
  the exact numbers.
- Reliability is modelled as a degradation-rate and lifetime change; real failure
  modes (barrier breakdown, corrosion under damp heat) are lumped into that knob.
- Silver is ~1% of system cost but a larger share of module cost; this part reports
  the system view, which is the conservative one for copper.

## 5. References

- pv magazine (2025-26): copper-metallised HJT matching silver efficiency; LONGi
  beginning copper-module mass production in 2026 as silver prices rose.
- SunDrive: >99% copper-plating production yield.
- ScienceDirect: *Copper metallization of silicon heterojunction cells — process,
  reliability and challenges* (nickel barrier, diffusion, damp-heat).
"""
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / "REPORT_METAL.md"
    path.write_text(text, encoding="utf-8")
    return path


def generate_metal(outdir: Path = DEFAULT_OUTDIR, weather=None) -> Path:
    results = collect_metal_results(weather=weather)
    render_metal_figures(results, outdir)
    return build_metal_report(results, outdir)
