"""Part XIII — can solar be *truly* renewable?

Part III showed recycling turns the material ceiling into a moving target. But two
honest questions remain. First: is the recovered metal actually usable in new
panels, or does it degrade? Second: if solar leans on finite metals, don't we
eventually run out — and then what?

This module answers both with numbers. Metals are the good news: unlike plastics or
glass (which "downcycle"), silver, copper, aluminium and silicon can be refined
back to original purity and reused **indefinitely** — the only loss is what we fail
to collect and recover each cycle. So the real questions become quantitative: how
tight is the loop, how long is the runway, and what makes solar *materially
self-sustaining* rather than just *long-lasting*.

The verdict it computes: solar can be truly renewable, but only on two conditions —
a **tightly closed recycling loop** and a shift to **abundant** metals. On scarce
silver alone, even with recycling, the runway is finite; on copper it is effectively
endless.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .materials import _materials_indexed

# Per-cycle recovery chain (each step a fraction that survives).
DEFAULT_COLLECTION = 0.90        # share of retired panels actually collected
DEFAULT_RECOVERY = 0.95         # share of the metal recovered from collected panels
DEFAULT_REFINING = 0.99         # share surviving refining back to cell-grade purity


def closed_loop_fraction(collection: float = DEFAULT_COLLECTION,
                         recovery: float = DEFAULT_RECOVERY,
                         refining: float = DEFAULT_REFINING) -> float:
    """Fraction of a panel's metal that re-enters new panels each ~30-yr cycle."""
    return collection * recovery * refining


@dataclass
class SteadyState:
    element: str
    intensity_t_per_gw: float
    throughput_t_yr: float       # metal cycled through the fleet each year
    virgin_t_yr: float           # new (mined) metal needed each year
    closed_loop: float
    annual_production_t: float
    reserves_t: float
    virgin_share_of_production: float
    runway_years: float          # reserves / virgin demand (inf if huge)


def steady_state(element: str, intensity_t_per_gw: float,
                 fleet_tw: float = 50.0, lifetime_years: float = 30.0,
                 closed_loop: float | None = None) -> SteadyState:
    """Material flows for a *mature* (non-growing) solar fleet of ``fleet_tw``.

    At steady state the fleet retires and rebuilds ``fleet/lifetime`` TW each year;
    only the un-recovered fraction must be mined fresh.
    """
    if closed_loop is None:
        closed_loop = closed_loop_fraction()
    mats = _materials_indexed()
    production = float(mats.loc[element, "annual_production_tonnes"])
    reserves = float(mats.loc[element, "reserves_tonnes"])

    throughput = (fleet_tw / lifetime_years) * 1000.0 * intensity_t_per_gw  # t/yr
    virgin = (1.0 - closed_loop) * throughput
    runway = reserves / virgin if virgin > 0 else float("inf")
    return SteadyState(
        element=element, intensity_t_per_gw=intensity_t_per_gw,
        throughput_t_yr=throughput, virgin_t_yr=virgin, closed_loop=closed_loop,
        annual_production_t=production, reserves_t=reserves,
        virgin_share_of_production=virgin / production if production else float("inf"),
        runway_years=runway)


def runway_scenarios(fleet_tw: float = 50.0) -> pd.DataFrame:
    """Material runway under different metals and loop tightness."""
    tight = closed_loop_fraction()                       # ~0.85
    leaky = closed_loop_fraction(collection=0.5)          # poorly collected
    rows = []
    cases = [
        ("Silver, no recycling", "Silver", 13.0, 0.0),
        ("Silver, leaky loop", "Silver", 13.0, leaky),
        ("Silver, tight loop", "Silver", 13.0, tight),
        ("Copper, tight loop", "Copper", 15.0, tight),
    ]
    for label, el, intensity, cl in cases:
        ss = steady_state(el, intensity, fleet_tw=fleet_tw, closed_loop=cl)
        rows.append({
            "scenario": label, "element": el, "closed_loop": cl,
            "virgin_t_yr": ss.virgin_t_yr,
            "virgin_share_of_production": ss.virgin_share_of_production,
            "runway_years": ss.runway_years,
        })
    return pd.DataFrame(rows)


def renewability_verdict(fleet_tw: float = 50.0) -> dict:
    """Summarise whether each path is materially self-sustaining.

    A path is "sustainable" if annual virgin demand stays well within annual world
    production (so it never draws down reserves faster than supply allows).
    """
    df = runway_scenarios(fleet_tw)
    silver_tight = df[df["scenario"] == "Silver, tight loop"].iloc[0]
    silver_none = df[df["scenario"] == "Silver, no recycling"].iloc[0]
    copper = df[df["scenario"] == "Copper, tight loop"].iloc[0]
    return {
        "silver_no_recycle_runway": silver_none["runway_years"],
        "silver_tight_runway": silver_tight["runway_years"],
        "silver_tight_share": silver_tight["virgin_share_of_production"],
        "copper_runway": copper["runway_years"],
        "copper_share": copper["virgin_share_of_production"],
        "closed_loop": closed_loop_fraction(),
    }
