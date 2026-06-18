"""Part IV report: optimising for space — land use, dual-use, grid value.

Mirrors the other report modules. ``generate_land`` runs the land-use analysis
and writes ``output/REPORT_LAND.md`` plus figures 14-15, deterministically.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from . import figures as figs
from .landuse import average_day_profile, land_metrics
from .report import DEFAULT_OUTDIR, _md_table
from .system import reference_weather


@dataclass
class LandResults:
    metrics: pd.DataFrame
    profile: pd.DataFrame


def collect_land_results(weather=None) -> LandResults:
    if weather is None:
        weather = reference_weather()
    return LandResults(metrics=land_metrics(weather=weather),
                       profile=average_day_profile(weather=weather))


def render_land_figures(r: LandResults, outdir: Path) -> list[Path]:
    figdir = outdir / "figures"
    return [figs.fig14_landuse(r.metrics, figdir),
            figs.fig15_diurnal(r.profile, figdir)]


def build_land_report(r: LandResults, outdir: Path = DEFAULT_OUTDIR) -> Path:
    m = r.metrics.set_index("archetype")
    agri_ler = m.loc["Agrivoltaics", "ler"]
    vert_ler = m.loc["Vertical bifacial E-W", "ler"]
    vert_sy = m.loc["Vertical bifacial E-W", "specific_yield"]
    ref_sy = m.loc["Ground-mount (reference)", "specific_yield"]
    float_gain = (m.loc["Floating PV", "specific_yield"] / ref_sy - 1) * 100

    table = _md_table(
        r.metrics, ["archetype", "gcr", "specific_yield", "energy_per_land_m2",
                    "crop_fraction", "ler"],
        ["Archetype", "GCR", "Yield (kWh/kWp)", "kWh/m² land/yr",
         "Crop kept", "LER"],
        [str, lambda v: f"{v:.2f}", lambda v: f"{v:,.0f}",
         lambda v: f"{v:.0f}", lambda v: f"{v:.0%}", lambda v: f"{v:.2f}"])

    text = f"""# Optimising for Space: Land, Dual-Use, and Grid Value

*Part IV. Module efficiency (Parts I-III) is energy per square metre of *panel*.
But the constraint that actually bites is energy per square metre of *land* — and
land can often do two jobs at once. This part rethinks **space** itself.*

---

## 1. Why land-use efficiency is the real space metric

A more efficient cell shrinks the panel, but a solar *farm* is mostly the gaps
between rows. What matters for siting is the **Land Equivalent Ratio (LER)**: the
energy a hectare yields plus the crop it still grows, each measured against doing
that one thing alone. LER > 1 means the land is more productive shared than split.

{table}

![Land Equivalent Ratio by archetype](figures/fig14_landuse.png)

- **Agrivoltaics** (elevated, widely spaced panels over crops or grazing) reaches
  **LER {agri_ler:.2f}** — it gives up some energy density but keeps ~85% of the
  crop, so the shared hectare out-produces either single use. This is the headline
  result of the agrivoltaics literature (LER 1.2-1.7).
- **Vertical bifacial east-west** reaches **LER {vert_ler:.2f}**: it yields
  {vert_sy/ref_sy*100:.0f}% of optimal-tilt energy ({vert_sy:,.0f} kWh/kWp) while
  leaving the land between rows fully farmable.
- **Floating PV** uses *no land at all* and the water's evaporative cooling lifts
  yield about **+{float_gain:.0f}%** versus the same array on a warm roof, while
  cutting reservoir evaporation.

## 2. Space and *time*: the grid-value of vertical east-west

Optimising space is not only about area — it is about *when* the power arrives.
Fixed south-facing panels all peak together at midday, exactly when a grid full of
solar is already glutted and prices crash. Standing the (bifacial) panels vertical
facing east-west moves generation to the morning and evening shoulders:

![Average-day generation shape](figures/fig15_diurnal.png)

The vertical array sacrifices a few percent of annual energy for a generation
shape that is worth more per kWh and eases the midday "duck curve". Space
efficiency, properly understood, includes temporal fit to demand.

## 3. Assumptions and limitations

- One site (Greensboro TMY3) and one module efficiency; LER components scale with
  resource and crop choice. Crop-yield fractions are literature mid-points and
  vary widely by species and climate (some shade-tolerant crops exceed open-field
  yield in hot, dry sites).
- Vertical east-west is modelled as a single bifacial module (east face front,
  west face at 0.8 bifaciality); row-to-row shading at low sun angles is captured
  only through the chosen GCR.
- Floating cooling is a flat +3% proxy; real gains depend on water temperature and
  mounting.

## 4. References

- C. Dupraz et al., *Combining solar photovoltaic panels and food crops...*,
  Renewable Energy 36 (2011) — Land Equivalent Ratio for agrivoltaics.
- A. Weselek et al., *Agrophotovoltaic systems: applications, challenges...*,
  Agronomy for Sustainable Development 39 (2019).
- Next2Sun — vertical bifacial east-west field performance.
- World Bank / SERIS, *Where Sun Meets Water: Floating Solar Market Report* (2019).
"""
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / "REPORT_LAND.md"
    path.write_text(text, encoding="utf-8")
    return path


def generate_land(outdir: Path = DEFAULT_OUTDIR, weather=None) -> Path:
    results = collect_land_results(weather=weather)
    render_land_figures(results, outdir)
    return build_land_report(results, outdir)
