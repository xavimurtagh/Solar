"""Part VIII report: firming the sun — the cost of dispatchable 24/7 solar."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from . import figures as figs
from . import firming as F
from .report import DEFAULT_OUTDIR, _md_table


@dataclass
class FirmResults:
    moderate: pd.DataFrame
    high: pd.DataFrame
    cheap95: dict
    cheap95_high: dict
    week: pd.DataFrame


def collect_firming_results(weather=None) -> FirmResults:
    moderate = F.lcoss_vs_reliability(weather=weather)
    high = F.lcoss_vs_reliability(weather=weather, params=F.HIGH_RESOURCE)
    cheap95 = F.cheapest_firm(weather=weather, reliability_target=0.95)
    cheap95_high = F.cheapest_firm(weather=weather, params=F.HIGH_RESOURCE,
                                   reliability_target=0.95)
    week = F.representative_week(cheap95["overbuild"], cheap95["storage_hours"],
                                 weather=weather)
    return FirmResults(moderate=moderate, high=high, cheap95=cheap95,
                       cheap95_high=cheap95_high, week=week)


def render_firming_figures(r: FirmResults, outdir: Path) -> list[Path]:
    figdir = outdir / "figures"
    refs = {"gas": F.NEW_GAS_USD_MWH, "coal": F.NEW_COAL_USD_MWH,
            "unfirmed": F.UNFIRMED_SOLAR_USD_MWH}
    return [figs.fig20_dispatch(r.week, figdir),
            figs.fig21_firm_cost(r.moderate, r.high, refs, figdir)]


def build_firming_report(r: FirmResults, outdir: Path = DEFAULT_OUTDIR) -> Path:
    c = r.cheap95
    ch = r.cheap95_high
    mod = r.moderate.set_index("reliability")
    lcoss_90 = mod.loc[0.90, "lcoss_usd_mwh"]
    lcoss_99 = mod.loc[0.99, "lcoss_usd_mwh"]
    tail_mult = lcoss_99 / lcoss_90

    tbl = _md_table(
        r.high[r.high["reliability"].isin([0.85, 0.90, 0.95, 0.99])],
        ["reliability", "lcoss_usd_mwh", "overbuild", "storage_hours"],
        ["Reliability", "Firm LCOE ($/MWh)", "Overbuild", "Storage (h)"],
        [lambda v: f"{v*100:.0f}%", lambda v: f"${v:.0f}",
         lambda v: f"{v:.1f}x", lambda v: f"{v:.0f}"])

    text = f"""# Firming the Sun: The Real Cost of 24/7 Solar

*Part VIII — the first answer to the value wall. If solar's problem is that it
arrives at the wrong time (Part VII), the obvious fix is to **move it in time**:
store the midday flood and release it after dark. This part simulates an hourly
solar+battery plant serving a flat, round-the-clock load and computes the true
cost of **firm** solar — the metric that should replace LCOE for a solar-dominated
grid.*

---

## 1. How firming works

Every hour, surplus solar charges a battery; deficits discharge it. Watch a
ten-day stretch of a plant sized to meet a constant load:

![Solar + battery dispatch](figures/fig20_dispatch.png)

The battery breathes daily — filling at midday (when Part VII showed power is
nearly worthless) and emptying through the evening and night (when it is most
valuable). Storage is, in effect, a machine for *buying low and selling high* in
time. Some midday solar still overflows the full battery and is curtailed; that
spilled energy is the feedstock for Part IX.

## 2. The cost of firmness

Sizing the cheapest overbuild × storage mix to hit each reliability target gives
the levelized cost of solar+storage (LCOSS). At a high-resource site:

{tbl}

![The cost of firm solar vs fossils](figures/fig21_firm_cost.png)

Two results matter. **First, firm solar already wins.** At a sunny site, 90-95%
reliable round-the-clock solar costs **${ch['lcoss_usd_mwh']:.0f}/MWh** — inside
IRENA's 2026 range of $54-82 and below new gas ($100) and coal ($80). Dispatchable
solar is no longer a future promise; it is cheaper than burning things, today.

**Second, the last mile is a cliff.** Going from 90% to 99% reliability on a
moderate site roughly **{tail_mult:.1f}×** the cost (${lcoss_90:.0f} →
${lcoss_99:.0f}/MWh), because covering rare multi-day cloudy lulls needs enormous,
rarely-used storage and overbuild. **Chasing 100% solar-only is the most expensive
energy you can buy.** The rational system firms the bulk with storage and handles
the final few percent another way — long-duration storage, a little firm backup,
or by *not needing it*, which is the demand-side inversion of Part IX.

## 3. Why this reframes "how we use solar"

Firming converts solar from a variable nuisance into a dispatchable commodity, but
it also reveals the limit of brute force: storage is cheap for hours, ruinous for
weeks. The lesson is not "store everything." It is "store the easy 80-90%, and
make the rest of the system *flexible* so it leans into solar's rhythm instead of
fighting it." That flexibility — demand that follows the sun — is the next part.

## 4. Assumptions and limitations

- Flat 24/7 load is the *hardest* target; a demand-shaped or partly-flexible load
  is cheaper to serve. Solar-only (no wind hybrid, which IRENA includes) is also
  conservative — real round-the-clock portfolios mix the two.
- Single battery (one round-trip efficiency, no degradation/augmentation), one
  site's hourly profile, perfect foresight-free greedy dispatch. LCOSS uses a
  capital-recovery factor (discount {int(F.FirmParams().discount_rate*100)}%,
  {F.FirmParams().lifetime_years}-yr life).
- Battery $180/kWh (moderate) / $130/kWh (high-resource), solar $0.85 / $0.65 per
  W — 2026 utility benchmarks; both are falling fast.

## 5. References

- IRENA, *24/7 renewables: the economics of firm solar and wind* (May 2026):
  firm solar+storage $54-82/MWh.
- NREL, *Levelized Cost of Solar-plus-Storage (LCOSS)*; storage cost benchmarks.
- Denholm et al. / NREL on the rising marginal cost of the last increment of
  renewable reliability (the "overbuild and curtail" literature).
"""
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / "REPORT_FIRMING.md"
    path.write_text(text, encoding="utf-8")
    return path


def generate_firming(outdir: Path = DEFAULT_OUTDIR, weather=None) -> Path:
    results = collect_firming_results(weather=weather)
    render_firming_figures(results, outdir)
    return build_firming_report(results, outdir)
