"""Part VI report: the pyrite voltage problem — and the prize for solving it.

Iron pyrite (FeS2, "fool's gold") is built from two of the most abundant elements
in the crust and has a near-ideal bandgap, yet makes a hopeless solar cell. This
part uses the External Radiative Efficiency (ERE) extension of the
Shockley-Queisser model to show *why* (a catastrophic voltage deficit) and what
curing it would unlock. Ties directly to Part III: a working pyrite cell would
have an effectively unlimited material ceiling.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from . import constants as C
from . import figures as figs
from .report import DEFAULT_OUTDIR, _md_table
from .spectrum import SpectrumIntegrals, load_am15g
from .sq import ere_sweep, sq_cell, voc_deficit


@dataclass
class PyriteResults:
    sweep: pd.DataFrame
    markers: list
    radiative: object
    today: object
    passivated: object
    si_quality: object
    voc_deficit_today: float


def collect_pyrite_results() -> PyriteResults:
    spec = SpectrumIntegrals(load_am15g())
    eg = C.PYRITE_EG_EV
    sweep = ere_sweep(eg, spec)

    radiative = sq_cell(eg, spec, ere=1.0)
    today = sq_cell(eg, spec, ere=C.PYRITE_ERE_TODAY)
    passivated = sq_cell(eg, spec, ere=C.PYRITE_ERE_PASSIVATED)
    si_quality = sq_cell(eg, spec, ere=C.ERE_SILICON)

    markers = [
        ("today (~1e-9)", C.PYRITE_ERE_TODAY, today.eta, today.voc_v),
        ("Si-quality", C.ERE_SILICON, si_quality.eta, si_quality.voc_v),
        ("passivated", C.PYRITE_ERE_PASSIVATED, passivated.eta, passivated.voc_v),
        ("radiative limit", 1.0, radiative.eta, radiative.voc_v),
    ]
    return PyriteResults(
        sweep=sweep, markers=markers, radiative=radiative, today=today,
        passivated=passivated, si_quality=si_quality,
        voc_deficit_today=voc_deficit(eg, spec, C.PYRITE_ERE_TODAY))


def render_pyrite_figures(r: PyriteResults, outdir: Path) -> list[Path]:
    from .pyrite import voltage_roadmap

    return [figs.fig17_pyrite(r.sweep, r.markers, outdir / "figures"),
            figs.fig28_pyrite_roadmap(voltage_roadmap(), outdir / "figures")]


def build_pyrite_report(r: PyriteResults, outdir: Path = DEFAULT_OUTDIR) -> Path:
    tbl = _md_table(
        pd.DataFrame([
            {"case": "Observed today (ERE ~1e-9)", "voc": r.today.voc_v, "eta": r.today.eta},
            {"case": "Silicon-quality (ERE 1e-3)", "voc": r.si_quality.voc_v, "eta": r.si_quality.eta},
            {"case": "Passivated (ERE 1e-2)", "voc": r.passivated.voc_v, "eta": r.passivated.eta},
            {"case": "Radiative ceiling (ERE 1)", "voc": r.radiative.voc_v, "eta": r.radiative.eta},
        ]),
        ["case", "voc", "eta"],
        ["Material quality", "Voc (V)", "Efficiency"],
        [str, lambda v: f"{v:.2f}", lambda v: f"{v*100:.1f}%"])

    from .pyrite import voltage_roadmap
    roadmap = voltage_roadmap()
    roadmap_tbl = _md_table(
        roadmap, ["stage", "voc_v", "eta", "mechanism"],
        ["Intervention (cumulative)", "Voc", "Efficiency", "What it fixes"],
        [str, lambda v: f"{v:.2f} V", lambda v: f"{v*100:.0f}%", str])

    text = f"""# Fool's Gold: The Pyrite Voltage Problem, and the Prize for Solving It

*Part VI. Part III argued that abundant-element cells are what let solar scale to
tens of terawatts. The most abundant candidate of all is **iron pyrite (FeS₂)** —
iron and sulfur, essentially unlimited and nearly free. It has a near-ideal
{C.PYRITE_EG_EV:.2f} eV bandgap and absorbs sunlight ferociously. And yet it makes
a terrible solar cell. This part models exactly why — and what cracking it would
unlock.*

---

## 1. The paradox

By the Shockley-Queisser logic of Part I, pyrite's {C.PYRITE_EG_EV:.2f} eV bandgap
should support a radiative efficiency limit of **{r.radiative.eta*100:.0f}%**
(open-circuit voltage **{r.radiative.voc_v:.2f} V**). Real pyrite cells have never
exceeded ~3%, with open-circuit voltages stuck near **0.2 V** — a catastrophic
collapse no other near-ideal-bandgap material suffers.

## 2. The diagnosis: a voltage problem, quantified

The collapse is not about absorbing light (pyrite absorbs superbly) — it is about
*holding voltage*. Non-radiative recombination — from sulfur vacancies, surface
states, and a possible conductive surface phase that pins the Fermi level — drains
the photovoltage. The Shockley-Queisser model captures this with one parameter,
the **external radiative efficiency (ERE)**: the dark current scales as
`J0 = J0_radiative / ERE`, so the voltage falls by `kT·ln(ERE)`.

Pyrite's ERE is around **1e-9** — billions of times worse than a GaAs record cell
(~0.2). That single number costs **{r.voc_deficit_today:.2f} V** of open-circuit
voltage and drops the efficiency ceiling from {r.radiative.eta*100:.0f}% to just
**{r.today.eta*100:.1f}%** — and real cells fall short of even that, once shunting
and series resistance (not modelled here) are added.

![Pyrite efficiency and voltage vs material quality](figures/fig17_pyrite.png)

## 3. The prize

The figure's message is the whole point: efficiency climbs steadily with material
quality — about **3 percentage points for every decade of ERE**, because each
decade adds `kT·ln(10) ≈ 0.06 V` of open-circuit voltage. Pyrite today sits at the
very bottom-left; it needs to climb roughly **five to six decades** of ERE to
become useful. Move it up to merely **silicon-grade** material quality and the
model gives:

{tbl}

A passivated pyrite cell could reach **{r.passivated.eta*100:.0f}%** — competitive
with today's commercial silicon — built from two of the cheapest, most abundant
elements on Earth. Combine that with Part III: pyrite's deployment ceiling is
effectively **unlimited** (iron and sulfur are mined in billions of tonnes per
year). A 20%-efficient pyrite cell would be worth more to the energy transition
than a 35%-efficient tandem that indium can never scale.

## 4. The roadmap: a quantified plan to crack it

"Cure the voltage" is too vague to act on, so the toolkit turns it into a ladder.
Each rung is a real, physically-motivated intervention — the same family of moves
that tamed silicon and perovskites — and the model reports exactly how much
efficiency each one would unlock by raising the external radiative efficiency (ERE):

{roadmap_tbl}

![The pyrite voltage roadmap](figures/fig28_pyrite_roadmap.png)

Read it as a research program. The single most important step is **carrier-selective
contacts** — the lesson stolen from heterojunction silicon and perovskites: instead
of begging pyrite's own broken surface to form a good junction, you sandwich it
between dedicated electron- and hole-collecting layers, so the voltage no longer
depends on the surface that has always wrecked it. That one architectural move does
most of the work, lifting pyrite past **20%** — into commercial-silicon territory,
from iron and sulfur.

**Have researchers tried?** Yes — for decades, every rung on this ladder has been
attempted, and pyrite has stubbornly resisted, which is why it remains a lab
curiosity. What the toolkit adds is not a cure but a *target*: it says precisely how
good each fix must get (an ERE of ~1e-2, a Voc of ~0.6 V) for pyrite to graduate
from hopeless to competitive. That turns a romantic "what if" into a measurable
engineering goal — the first thing any serious attempt needs.

## 5. Why it is hard

The voltage problem is widely attributed to the pyrite *surface* (a sulfur-poor,
metallic-like layer) and to bulk sulfur vacancies. The levers above raise ERE by the
~7 orders of magnitude that stand between today's cells and a competitive one. This
is a materials-science moonshot, not a thermodynamic impossibility: the physics
permits {r.radiative.eta*100:.0f}%; only the defects forbid it.

## 6. Assumptions and limitations

- The ERE model captures the *voltage* loss (the dominant, defining failure) but
  assumes ideal current collection and no shunt/series losses, so it is an upper
  bound — real pyrite trails even the {r.today.eta*100:.1f}% shown for ERE 1e-9.
- ERE values are representative (pyrite ~1e-9; GaAs ~0.2; Si ~1e-3); the
  qualitative cliff and the size of the prize are robust to the exact figures.
- One bandgap (0.95 eV) and the standard AM1.5G spectrum.

## 7. References

- M. A. Green, *Radiative efficiency of state-of-the-art photovoltaic cells*,
  Prog. Photovolt. 20 (2012) — the ERE framework.
- W. Shockley & H. J. Queisser, J. Appl. Phys. 32, 510 (1961).
- Pyrite photovoltaics reviews (surface states / sulfur-vacancy voltage deficit),
  e.g. Wadia/Alivisatos abundance analysis; Hu et al. on FeS₂ defect physics.
"""
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / "REPORT_PYRITE.md"
    path.write_text(text, encoding="utf-8")
    return path


def generate_pyrite(outdir: Path = DEFAULT_OUTDIR) -> Path:
    results = collect_pyrite_results()
    render_pyrite_figures(results, outdir)
    return build_pyrite_report(results, outdir)
