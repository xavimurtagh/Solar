"""Part XIII report: can solar be truly renewable?"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from . import figures as figs
from .renewable import closed_loop_fraction, renewability_verdict, runway_scenarios
from .report import DEFAULT_OUTDIR, _md_table


@dataclass
class RenewableResults:
    runway: pd.DataFrame
    verdict: dict


def collect_renewable_results(weather=None) -> RenewableResults:
    return RenewableResults(runway=runway_scenarios(), verdict=renewability_verdict())


def render_renewable_figures(r: RenewableResults, outdir: Path) -> list[Path]:
    return [figs.fig27_renewable(r.runway, outdir / "figures")]


def build_renewable_report(r: RenewableResults, outdir: Path = DEFAULT_OUTDIR) -> Path:
    v = r.verdict

    def runway_str(y):
        return "effectively infinite" if y >= 1e5 else f"{y:.0f} years"

    tbl = _md_table(
        r.runway, ["scenario", "closed_loop", "virgin_t_yr",
                   "virgin_share_of_production", "runway_years"],
        ["Scenario", "Loop closed", "Virgin metal/yr", "% of world prod.", "Runway"],
        [str, lambda x: f"{x*100:.0f}%", lambda x: f"{x:,.0f} t",
         lambda x: f"{x*100:.1f}%", lambda x: runway_str(x)])

    text = f"""# Can Solar Be Truly Renewable?

*Part XIII. "Renewable" usually means the *fuel* is endless — and sunlight is. But a
solar panel is built from *metals*, and metals are mined. So a fair sceptic asks:
if every panel needs silver, won't we eventually run out, and isn't calling that
"renewable" a sleight of hand? This part takes the objection seriously and answers
it with arithmetic.*

---

## 1. First, the good news: metals don't wear out

A crucial fact that decides everything below: **metals are infinitely recyclable.**
Unlike a plastic bottle (which "downcycles" into something lower-grade) or a sheet
of glass (usually crushed for roadbed), the silver and copper in a retired solar
panel can be refined back to **original, cell-grade purity** and used again in a
brand-new panel, with no loss of quality. Silicon, too, can be re-purified to solar
grade (it costs energy, but solar has energy to spare). The recovered metal is not a
downgrade — it is the same atom, ready to work for another thirty years.

So the only thing lost each cycle is what we **fail to collect or recover**. With a
realistic chain — 90% of panels collected, 95% of the metal recovered, 99%
surviving refining — about **{v['closed_loop']*100:.0f}% of the metal comes back**
each ~30-year cycle. The other ~15% is the leak we must replace with fresh mining.

## 2. Now the hard question: do we run out?

Imagine a *mature* world running on **50 terawatts** of solar — enough to power a
fully electrified civilization. Each year it retires and rebuilds about a thirtieth
of itself. How much metal does that take, and how long can the Earth supply it?

{tbl}

![Material runway by scenario](figures/fig27_renewable.png)

The numbers tell a sharp story:

- **Silver, no recycling:** a 50 TW silver-based fleet would consume **87% of all
  the silver mined on Earth every year**, and exhaust known silver *reserves* in
  about **{runway_str(v['silver_no_recycle_runway'])}**. Called that way, the
  sceptic is right — this is *not* renewable. It's a 30-year resource cliff.
- **Silver, tight recycling loop:** close the loop to ~85% and fresh silver demand
  collapses to **{v['silver_tight_share']*100:.0f}% of world production**, stretching
  the runway to about **{runway_str(v['silver_tight_runway'])}**. Recycling doesn't
  just help — it converts an unsustainable system into a multi-century one.
- **Copper, tight loop:** copper-based metallisation (Part XII) needs only
  **{v['copper_share']*100:.2f}% of world copper production**, against reserves so
  large the runway is **effectively infinite**.

## 3. The verdict: yes — on two conditions

So can solar be *truly* renewable? **Yes, but it is a choice, not an automatic
property**, and it rests on two pillars:

1. **Close the loop.** Recycling is not optional housekeeping; it is the difference
   between a 30-year cliff and a multi-century supply. And because the recovered
   metal returns to full purity, the loop genuinely closes — this is real
   circularity, not a slogan. The danger is a *leaky* loop: poor collection (panels
   abandoned, exported, landfilled) drops you back toward the cliff.
2. **Move to abundant metals.** Even a perfect loop on silver is *finite* — every
   cycle leaks ~15%, so reserves still drain, just slowly. Only a shift to abundant
   materials (copper, aluminium, iron, silicon — the stuff of Parts VI and XII)
   makes the runway effectively endless. That is what "truly renewable" actually
   requires.

The scarce-silver era we are in now is best understood as a **bootstrap**: it gets
solar started, but a civilization that intends to run on solar *forever* must
graduate to abundant materials and a tightly closed loop. Do both, and solar earns
the name "renewable" in the fullest sense — not just an endless fuel, but an endless
*material* basis too. Do neither, and we simply trade an oil cliff for a silver one.

## 4. Assumptions and limitations

- A simplified steady-state (non-growing) 50 TW fleet on a 30-year lifetime; during
  *growth*, demand is higher and scarcer (Part III). The steady state is the
  long-run question this part addresses.
- Recovery chain figures (collection/recovery/refining) are representative; real
  collection rates today are far below 90%, which is precisely the risk.
- "Reserves" are economically-recoverable today; they grow as prices rise and
  exploration continues, so the silver runways are conservative — but the
  *direction* (scarce = finite, abundant = endless) is robust.

## 5. References

- USGS Mineral Commodity Summaries 2025 (production, reserves).
- IEA / IRENA on PV material circularity and end-of-life recovery.
- Metal recyclability and refining-to-purity: standard hydro/pyrometallurgy.
"""
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / "REPORT_RENEWABLE.md"
    path.write_text(text, encoding="utf-8")
    return path


def generate_renewable(outdir: Path = DEFAULT_OUTDIR, weather=None) -> Path:
    results = collect_renewable_results(weather=weather)
    render_renewable_figures(results, outdir)
    return build_renewable_report(results, outdir)
