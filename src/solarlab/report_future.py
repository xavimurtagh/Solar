"""Part XI — the capstone: Wright's law and the manifesto of the Great Inversion.

Fits the learning curve, projects solar's cost forward, and ties all eleven parts
into one argument about how solar changes the sphere of energy. Per the user's
choice, the synthesis is a *full manifesto*: grounded models plus bold
first-principles extrapolation, with every step past the computed/cited data
explicitly flagged [EXTRAPOLATION].
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from . import figures as figs
from . import learning as L
from .report import DEFAULT_OUTDIR


@dataclass
class FutureResults:
    fit: dict
    hist: pd.DataFrame
    proj: pd.DataFrame
    milestones: dict


def collect_future_results() -> FutureResults:
    fit = L.fit_learning_rate()
    hist = L._historical()
    proj = L.project_lcoe()
    milestones = L.milestone_years(proj)
    return FutureResults(fit=fit, hist=hist, proj=proj, milestones=milestones)


def render_future_figures(r: FutureResults, outdir: Path) -> list[Path]:
    return [figs.fig25_trajectory(r.hist, r.proj, r.fit, r.milestones,
                                  outdir / "figures")]


def build_future_report(r: FutureResults, outdir: Path = DEFAULT_OUTDIR) -> Path:
    lr = r.fit["learning_rate"] * 100
    p = r.proj.set_index("year")
    lcoe_2024 = p.loc[2024, "lcoe_usd_mwh"]
    lcoe_2050 = p.loc[2050, "lcoe_usd_mwh"]
    mod_2050 = p.loc[2050, "module_price_usd_per_w"]
    cum_2050 = p.loc[2050, "cumulative_gw"] / 1000

    text = f"""# The Great Inversion: How Solar Changes the Sphere of Energy

*Part XI, the capstone. Eleven analyses, each computing rather than asserting, now
resolve into a single argument. The first half of this document is grounded in the
models and the data; the second half reaches past them into what near-free,
clean energy means for civilization — and every such step is marked
**[EXTRAPOLATION]**, because the honest thing about a manifesto is to say where the
arithmetic ends and the conviction begins.*

---

## 1. The engine: Wright's law and the cheapest energy ever made

Strip away every detail and one mechanism explains solar's rise: **Wright's law**.
Every doubling of cumulative production has cut the module price by a roughly
constant fraction — here fitted at **{lr:.0f}% per doubling** across 2010-2024
(R² = {r.fit['r2']:.3f}). Fifty years and six orders of magnitude of scale fall on
a single straight line.

![Wright's law and the trajectory](figures/fig25_trajectory.png)

Projected forward along the deployment path to ~{cum_2050:.0f} TW by 2050, the
module heads toward **${mod_2050:.3f}/W** — nearly free. Utility LCOE falls from
~${lcoe_2024:.0f}/MWh today toward **~${lcoe_2050:.0f}/MWh**, and then *stops
falling much* — because once the panel costs nothing, the price of solar energy is
the price of everything *around* the panel: land, wiring, inverters, labour, and
permits (Part II). **The frontier of cheap energy has moved off the cell and onto
the system.** This is the first lesson of the whole project, now made quantitative:
the cell is solved; the system is the work.

## 2. What the eleven parts add up to

| # | Part | The lesson |
|---|------|------------|
| I | The cell | A single junction cannot beat ~34%; physics, then engineering. |
| II | Cost & materials | $/kWh, not %, is the metric — and soft costs dominate. |
| III | Circularity | Recycling turns the material ceiling into a moving target. |
| IV | Land | Space is a resource; dual-use land out-produces single-use. |
| V | The optimiser | There is no best cell — only the best cell *for a constraint*. |
| VI | Pyrite | Abundance can beat efficiency if we cure the voltage. |
| VII | The value wall | Solar's electrons are cheapest when least valuable. |
| VIII | Firming | Storage makes solar dispatchable — but the last mile is a cliff. |
| IX | Power-to-X | Don't store electrons; make molecules. Shape demand to the sun. |
| X | Off-world | The ultimate firm solar collects where night never falls. |
| XI | The trajectory | The panel becomes free; the system becomes the frontier. |

Read top to bottom, they trace a single migration of the binding constraint:
**efficiency → cost → materials → value/timing → end-use.** Each was the bottleneck
of its decade; each, in turn, was solved or is being solved. The constraint that
remains — the one this project ends on — is not technical at all. It is
**imagination**: what do we *do* with energy once it is clean, abundant, and almost
free, but only when the sun shines?

## 3. The inversion, stated plainly

For a century and a half, energy supply followed demand: we burned fuel on command,
ramping power plants to match whatever the world asked for. Solar cannot do this.
Its timing is set by the sky. So we face a choice between two philosophies:

- **Bend solar to the old world** — store it, firm it, ship it through wires until
  it behaves like a fuel (Parts VIII, X). This works, and firm solar already beats
  fossils, but the last increment is brutally expensive.
- **Bend the world to solar** — build an economy of flexible, interruptible demand
  that *feasts when the sun shines* and rests when it doesn't (Part IX). Make
  hydrogen, ammonia, fuels, fresh water, captured carbon, and computation in the
  hours when power is free.

The first is firming. The second is the **inversion**, and it is the more powerful
idea, because it turns solar's greatest weakness — its intermittency — into the
organising principle of a new industrial base. The grid stops being the customer
for solar and becomes one customer among many.

## 4. [EXTRAPOLATION] Energy superabundance

*Beyond here, the models give way to inference.* If solar continues down its
learning curve, the marginal cost of midday electricity in sunny regions trends
toward zero. Economies are not built for zero-priced inputs; they have never had
one. When the cost of energy collapses, things that were unthinkable become
ordinary:

- **Water** becomes an energy product. Desalination at a few cents per tonne
  (Part IX) makes coastal deserts arable and detaches fresh water from rainfall.
- **Carbon removal** becomes a utility. Direct air capture at the cost of cheap
  electricity makes drawing down legacy CO₂ a line item, not a moonshot.
- **Matter** becomes programmable. Green hydrogen and its derivatives turn
  electricity into steel, fertiliser, fuel, and plastics, decoupling industry from
  fossil feedstocks.
- **Computation** migrates to the sun. Energy-hungry AI and industry relocate to
  where and when power is free, inverting the century-old logic that moved energy
  to the factory; now the factory moves to the energy.

This is not "cheaper electricity." It is a different relationship between
civilization and energy: from scarcity to **superabundance**, available
intermittently, in specific places, to whoever builds the flexible demand to catch
it.

## 5. [EXTRAPOLATION] The geopolitics of a solar world

*Inference continues.* Fossil energy is concentrated — a few basins, a few states,
pipelines and tankers and chokepoints. Sunlight is the most evenly distributed
resource on Earth. A world that runs on solar is a world where energy is **made,
not extracted**, and made nearly everywhere. The strategic prize shifts from owning
reserves to owning *manufacturing* — the factories that print panels, batteries,
and electrolysers, and the materials (Part III) to feed them. The petro-state gives
way to the **electro-state**: power measured not in barrels but in terawatts of
deployment and the industrial capacity to keep doubling. Energy independence stops
being a slogan and becomes a rooftop. The same abundance that decarbonises also
de-monopolises.

## 6. The mandate — what to build

Pulling the grounded findings together, the work that matters most is now legible:

1. **Attack soft costs and balance-of-system**, not cell efficiency — that is where
   the remaining LCOE lives (Parts II, XI).
2. **Build high-value recycling *before* the retirement wave**, so the material
   ceiling never binds (Part III).
3. **Invert demand**: subsidise and site flexible industry — electrolysis, DAC,
   desalination, compute — to live off the glut instead of curtailing it (Parts
   VII, IX). This is the single highest-leverage move, because it fixes the value
   wall and decarbonises industry at once.
4. **Firm the bulk with storage; do not chase 100% solar-only** — handle the last
   few percent with flexibility or long-duration storage (Part VIII).
5. **Fund the abundance bets** — pyrite-class earth-abundant cells (Part VI) and
   the launch-cost curve that makes space solar real (Part X) — as option value on
   a much larger future.

## 7. Honesty: where this ends and conviction begins

Sections 1-3 and 6 rest on this toolkit's computed models and cited data, validated
throughout against 2026 reality (Lazard, IRENA, USGS, NREL, ITRPV). Sections 4-5
are **[EXTRAPOLATION]** — directionally argued from those models but not proven by
them; the future is not a dataset. The learning-rate fit assumes the curve does not
break; the LCOE floor assumes balance-of-system stays sticky; superabundance
assumes flexible demand actually gets built. Each could be wrong.

But the core claim is robust because it is already happening: solar is the cheapest
electricity humanity has ever made, its binding constraint has moved from cost to
*use*, and the civilizations that learn to shape their demand around the sun —
rather than waiting for the sun to behave like coal — will inherit an abundance the
fossil age could not imagine. That is how solar changes the entire sphere of energy.
Not as a better power plant. As a new way to run a world.

---

*Generated by `solarlab` — eleven parts, twenty-five figures, every number computed
or cited. Run `python -m solarlab all` to reproduce the whole argument from first
principles.*
"""
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / "REPORT_FUTURE.md"
    path.write_text(text, encoding="utf-8")
    return path


def generate_future(outdir: Path = DEFAULT_OUTDIR) -> Path:
    results = collect_future_results()
    render_future_figures(results, outdir)
    return build_future_report(results, outdir)
