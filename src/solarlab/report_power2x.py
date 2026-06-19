"""Part IX report: solar as feedstock — power-to-X and the demand-side inversion."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from . import figures as figs
from . import power2x as PX
from .report import DEFAULT_OUTDIR, _md_table

CHEAP_PRICE = 20.0
GRID_PRICE = 90.0


@dataclass
class P2XResults:
    lcoh_curves: dict
    flex: pd.DataFrame
    enduse: pd.DataFrame
    glut_high: dict


def collect_power2x_results(weather=None) -> P2XResults:
    lcoh_curves = {
        "Dedicated solar (CF 0.25, $700/kW)": PX.lcoh_curve(0.25),
        "High-resource future (CF 0.30, $500/kW)": PX.lcoh_curve(0.30, electrolyzer_capex_per_kw=500),
        "Grid-coupled (CF 0.45, $700/kW)": PX.lcoh_curve(0.45),
    }
    flex = pd.DataFrame([
        PX.flexible_demand_effect(p, flex_capacity=0.6, weather=weather)
        for p in np.linspace(0.1, 0.6, 11)])
    enduse = PX.enduse_unlock(CHEAP_PRICE, GRID_PRICE)
    glut_high = PX.glut_to_hydrogen(0.45, weather=weather)
    return P2XResults(lcoh_curves=lcoh_curves, flex=flex, enduse=enduse,
                      glut_high=glut_high)


def render_power2x_figures(r: P2XResults, outdir: Path) -> list[Path]:
    figdir = outdir / "figures"
    refs = {"grey": PX.GREY_H2_USD_KG, "blue": PX.BLUE_H2_USD_KG}
    return [
        figs.fig22_lcoh(r.lcoh_curves, refs, (15, 25), figdir),
        figs.fig23_inversion(r.flex, r.enduse, CHEAP_PRICE, GRID_PRICE, figdir),
    ]


def build_power2x_report(r: P2XResults, outdir: Path = DEFAULT_OUTDIR) -> Path:
    lcoh_solar = PX.lcoh(20.0, 0.30, electrolyzer_capex_per_kw=500)
    flex_high = r.flex.iloc[-1]
    curt_cut = (flex_high["curtailment_base"] - flex_high["curtailment_flex"]) * 100

    tbl = _md_table(
        r.enduse, ["product", "unit", "elec_cost_cheap", "elec_cost_grid", "market_reference"],
        ["Product", "Unit", "Elec @ $20 solar", "Elec @ $90 grid", "Market price"],
        [str, str, lambda v: f"${v:,.2f}", lambda v: f"${v:,.2f}", lambda v: f"~${v:,.0f}"])

    text = f"""# Solar as Feedstock: Stop Storing Electrons, Start Making Molecules

*Part IX — the deepest reframe in this whole project. Firming (Part VIII) reshapes
**solar** to fit demand. This part does the opposite, and the more powerful thing:
it reshapes **demand** to fit solar. When midday power is nearly free — and
increasingly negative-priced — the winning move is not to store those electrons,
but to build flexible, interruptible industries that feast on them: electrolysers,
direct-air-capture, desalination, smelters, datacenters. Solar stops being a
source of *electricity* and becomes a source of cheap **molecules, heat, water,
and carbon removal**.*

---

## 1. Cheap solar makes cheap molecules

Green hydrogen is the keystone — the gateway from cheap electrons to storable,
shippable, industrial energy. Its cost (LCOH) is dominated by two things: the
electrolyser's capital (amortised over how hard it runs) and the electricity
price (55-70% of the total). Both now point the right way:

![Levelized cost of green hydrogen](figures/fig22_lcoh.png)

At a solar PPA of $20/MWh with a modern electrolyser, the model gives
**${lcoh_solar:.2f}/kg** — inside the 2026 range of $2.50-5 and closing on fossil
("grey") hydrogen at ~$1.50. A subtle but crucial result: hydrogen made *only*
from curtailed midday power is **more** expensive, not less, because a
capital-heavy electrolyser idle 80% of the time can't amortise its cost. The sweet
spot is a flexible electrolyser that runs most of the day on cheap solar and leans
into — not exclusively on — the glut.

## 2. The inversion: demand that eats the glut

Part VII showed that at high penetration a fifth or more of all solar is curtailed.
That waste is not a problem to be mourned — it is a **feedstock to be claimed.**
Add flexible electrolysis that switches on whenever solar floods the grid:

![The inversion](figures/fig23_inversion.png)

Flexible demand collapses curtailment — at 60% solar share, from a third of all
solar wasted to a small remainder ({curt_cut:.0f} percentage points reclaimed) —
and turns that energy into hydrogen. On a 1000 TWh grid at 45% solar, the
otherwise-spilled glut alone is **~{r.glut_high['curtailed_twh']:.0f} TWh/yr**,
enough for **~{r.glut_high['hydrogen_mt']:.1f} million tonnes of hydrogen** — from
energy that was being thrown away. The "duck curve" problem and the "where do we
get green hydrogen" problem are the same problem, and they solve each other.

## 3. How, exactly, does electricity become *things*?

"Make molecules from sunlight" sounds like hand-waving, so here is the actual
chain, step by physical step. The pivot is **water-splitting**: pass a solar
current through water and it tears apart into hydrogen and oxygen
(`2 H₂O + electricity → 2 H₂ + O₂`). That hydrogen is the master key — almost
everything else is built from it:

- **Fertiliser (ammonia).** Combine that hydrogen with nitrogen pulled straight
  from the air, over an iron catalyst at heat and pressure (the century-old
  Haber-Bosch reaction: `N₂ + 3 H₂ → 2 NH₃`). Ammonia is the nitrogen fertiliser
  that already grows roughly half the world's food — today made from fossil gas,
  tomorrow from sunlight and air.
- **Steel.** Steel is made by stripping the oxygen out of iron ore. Today that is
  done with coal, which dumps CO₂ (`Fe₂O₃ + 3 CO → 2 Fe + 3 CO₂`). Swap in
  hydrogen and the *exhaust becomes water* (`Fe₂O₃ + 3 H₂ → 2 Fe + 3 H₂O`). Same
  steel, no carbon — "green steel".
- **Fuels for planes and ships.** Capture CO₂ from the air (see below), react it
  with the hydrogen, and you can build liquid hydrocarbons — jet fuel, diesel,
  methanol — molecule by molecule (the Fischer-Tropsch process). These are
  drop-in fuels for the things batteries can't easily move.
- **Carbon removal.** Big fans push air over a chemical sponge that grabs CO₂;
  gentle heat then releases it, pure, to be buried or turned into the fuels above.
  It is electricity-hungry, which is exactly why it wants the free midday glut.
- **Fresh water.** Electric pumps force seawater through a fine membrane that lets
  water molecules through but blocks the salt (reverse osmosis). A few
  kilowatt-hours buys a tonne of drinking water.
- **Industrial heat.** Much of industry just needs *heat*. Solar electricity can
  charge a "thermal battery" — a stack of cheap firebricks or rocks heated to
  ~1500 °C at midday — that releases that heat steadily to a factory all night.

Notice the pattern: every one of these is a **flexible, interruptible** load that
is happy to run hard when the sun blazes and idle when it sets. That is the whole
trick — they are designed *around* solar's rhythm, not in spite of it.

## 4. What near-free solar unlocks

Because electricity is the dominant input to all of these processes, driving its
price toward zero at midday doesn't just make them cheaper — it makes whole new
industries *possible*. The electricity-cost component of each product at cheap
solar versus grid power:

{tbl}

At grid prices several of these are uneconomic; at $20/MWh solar their energy cost
falls below their market value and they flip to viable. Desalinated water for a few
cents a tonne makes fresh water an energy product. Direct air capture at ~$40/tonne
of electricity makes carbon removal scalable. Green steel and ammonia — a tenth of
all industrial CO2 — decarbonise. **This is how solar changes the energy sphere:
not by lighting bulbs more cheaply, but by becoming the feedstock for the physical
economy whenever the sun is up.**

## 5. Assumptions and limitations

- LCOH uses representative techno-economics (51 kWh/kg, $500-700/kW electrolyser,
  8%/20-yr finance); it reproduces the 2026 $2.50-5/kg range but a real project
  varies with utilisation, location, and stack lifetime.
- End-use intensities are literature mid-points; "viable" depends on full capex and
  logistics, not energy alone — the table isolates the *electricity* component to
  show the unlock, not a complete cost.
- Flexible-demand dispatch is a simple surplus-following heuristic; it captures the
  glut but is not a market or unit-commitment model.

## 6. References

- IEA, *Global Hydrogen Review* (2025-26); BNEF / RMI green-hydrogen cost analyses.
- Electrolyser CAPEX and LCOH 2026: $700-1000/kW falling; LCOH $2.50-5/kg.
- Energy intensities: seawater RO (~3.5 kWh/m^3), DAC (~2 MWh/tCO2), H2-DRI steel
  (~3.5 MWh/t), Haber-Bosch ammonia (~12 MWh/t incl. hydrogen).
"""
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / "REPORT_POWER2X.md"
    path.write_text(text, encoding="utf-8")
    return path


def generate_power2x(outdir: Path = DEFAULT_OUTDIR, weather=None) -> Path:
    results = collect_power2x_results(weather=weather)
    render_power2x_figures(results, outdir)
    return build_power2x_report(results, outdir)
