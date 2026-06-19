"""Part X report: solar off-world — space-based solar power."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from . import figures as figs
from . import spacepv as SP
from .report import DEFAULT_OUTDIR, _md_table


@dataclass
class SpaceResults:
    curves: dict
    crossovers: pd.DataFrame


def collect_space_results() -> SpaceResults:
    curves = {name: SP.sbsp_curve(params=p) for name, p in SP.SCENARIOS.items()}
    rows = []
    for name, p in SP.SCENARIOS.items():
        rows.append({
            "scenario": name,
            "lcoe_at_starship": SP.sbsp_lcoe(SP.LAUNCH_STARSHIP_TARGET, p),
            "lcoe_at_falcon9": SP.sbsp_lcoe(SP.LAUNCH_FALCON9, p),
            "crossover_high": SP.crossover_launch_cost(SP.FIRM_TERRESTRIAL_HIGH, p),
            "crossover_moderate": SP.crossover_launch_cost(SP.FIRM_TERRESTRIAL_MODERATE, p),
        })
    return SpaceResults(curves=curves, crossovers=pd.DataFrame(rows))


def render_space_figures(r: SpaceResults, outdir: Path) -> list[Path]:
    figdir = outdir / "figures"
    refs = {"firm_high": SP.FIRM_TERRESTRIAL_HIGH,
            "firm_moderate": SP.FIRM_TERRESTRIAL_MODERATE,
            "raw": SP.RAW_TERRESTRIAL}
    markers = {"Starship target ($100)": SP.LAUNCH_STARSHIP_TARGET,
               "Starship early ($1000)": SP.LAUNCH_STARSHIP_EARLY,
               "Falcon 9 ($2700)": SP.LAUNCH_FALCON9}
    return [figs.fig24_sbsp(r.curves, refs, markers, figdir)]


def build_space_report(r: SpaceResults, outdir: Path = DEFAULT_OUTDIR) -> Path:
    cx = r.crossovers
    nominal = cx[cx["scenario"].str.startswith("Nominal")].iloc[0]

    tbl = _md_table(
        cx, ["scenario", "lcoe_at_starship", "lcoe_at_falcon9", "crossover_high"],
        ["Satellite mass", "LCOE @ Starship ($100/kg)", "LCOE @ Falcon 9 ($2700/kg)",
         "Launch cost to beat firm solar"],
        [str, lambda v: f"${v:.0f}/MWh", lambda v: f"${v:.0f}/MWh",
         lambda v: f"${v:.0f}/kg"])

    text = f"""# Solar Off-World: Escaping Intermittency by Leaving the Planet

*Part X — the third and most radical answer to the value wall. Firming (VIII) and
power-to-X (IX) work around the night. Space-based solar power (SBSP) **abolishes**
it. In geostationary orbit the sun never sets and no atmosphere dims it, so a solar
satellite delivers ~95% capacity factor at ~1361 W/m² — then beams the power to a
ground rectenna by microwave. It is the only solar that is firm by nature.*

---

## 1. The right comparison

SBSP is often dismissed by comparing it to dirt-cheap daytime solar (~$30/MWh) —
which is unfair, because SBSP delivers power around the clock. The honest
benchmark is **firm** terrestrial solar from Part VIII (~$72/MWh at high-resource
sites, ~$130 at moderate ones). Against that bar, the only question is launch cost,
because the cost of an SBSP system is dominated by the mass it must lift to orbit.

## 2. The launch-cost threshold

Modelling SBSP LCOE as (annualised launch + hardware) / round-the-clock energy,
across satellite-mass scenarios:

{tbl}

![SBSP cost vs launch cost](figures/fig24_sbsp.png)

The result is decisive. At today's Falcon 9 prices (~$2700/kg) SBSP is hopeless —
hundreds to thousands of dollars per MWh. But the curve is steep, and at **Starship's
target of ~$100/kg** the nominal design lands at **${nominal['lcoe_at_starship']:.0f}/MWh**
— below firm terrestrial solar. The break-even launch cost to beat high-resource
firm solar is **~${nominal['crossover_high']:.0f}/kg** for the nominal case (and as
high as a few hundred $/kg for ultralight designs). That is precisely the range the
next generation of reusable heavy-lift rockets is targeting.

This reframes SBSP from science fiction to a **launch-cost bet**. It does not need
a physics breakthrough; it needs the cost of reaching orbit to fall by ~20-50×,
which is already underway. Caltech's flight demonstration of in-space power beaming
(2023), ESA's SOLARIS, and China's planned megawatt test station are the opening
moves. Reproduced here: Caltech's own ~$0.09/kWh estimate sits squarely on our
nominal curve.

## 3. Why it could change the sphere of energy

If launch costs fall as projected, SBSP offers something no terrestrial system
can: **gigawatt-scale, 24/7, weather-proof, land-free power deliverable anywhere a
rectenna can be built** — including places with poor sun, high latitudes, or no
land to spare. It is firmness without storage, baseload without fuel. It would not
replace cheap terrestrial solar for daytime bulk energy; it would compete for the
high-value firm capacity that Parts VII-VIII showed is the hard, expensive part.
The sun delivers ~10¹⁷ W to Earth's vicinity; we have, so far, only ever reached up
and taken a little of what misses the planet entirely.

## 4. Assumptions and limitations

- A deliberately simple cost model: LCOE = (CRF·(specific_mass·launch + hardware) +
  opex) / annual delivered energy. Specific mass (10-50 kg/kW ground-delivered) and
  hardware cost fold in beam efficiency (~50% DC-RF-DC), pointing, and the ground
  rectenna. These are the central uncertainties.
- Ignores orbital assembly, station-keeping, space-debris and radiation
  degradation, spectrum/safety regulation, and end-of-life — all real, none
  obviously fatal.
- The break-even is against *our* firm-terrestrial numbers (Part VIII); cheaper
  long-duration storage would raise the bar SBSP must clear.

## 5. References

- Caltech Space Solar Power Project (MAPLE in-space beaming demo, 2023);
  Atwater et al. LCOE estimates ($0.09-0.50/kWh).
- ESA SOLARIS; China 2030 MW test-station plan; UK/Japan SBSP roadmaps.
- Starship LEO launch-cost targets (~$100/kg) enabling the threshold here.
"""
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / "REPORT_SPACE.md"
    path.write_text(text, encoding="utf-8")
    return path


def generate_space(outdir: Path = DEFAULT_OUTDIR) -> Path:
    results = collect_space_results()
    render_space_figures(results, outdir)
    return build_space_report(results, outdir)
