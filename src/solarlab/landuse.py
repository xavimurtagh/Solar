"""Optimising for space: land-use efficiency, dual-use, and grid-value siting.

Module efficiency (Parts I-III) is energy per *module* area. But the binding
"space" constraint is usually energy per *land* area — and land can often do two
jobs at once. This module evaluates deployment archetypes that rethink space:

- **Conventional ground-mount** — the baseline (rows spaced by a ground-cover
  ratio, GCR).
- **Agrivoltaics** — elevated, widely-spaced panels with crops/grazing beneath;
  scored by the **Land Equivalent Ratio (LER)**: energy-yield-fraction +
  crop-yield-fraction, where LER > 1 means the dual-use beats doing each
  separately.
- **Vertical bifacial (east-west)** — panels stood on edge; lower annual yield
  but generation shifted to morning and evening, exactly when the midday solar
  glut makes power most valuable, and the land between rows stays farmable.
- **Floating PV** — on water: no land at all, and evaporative cooling lifts yield.

Annual yields come from :func:`solarlab.system.simulate`; the vertical-east-west
diurnal profile uses the hourly AC series it now exposes.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import constants as C
from .system import Scenario, reference_weather, simulate


@dataclass
class LandArchetype:
    name: str
    gcr: float                       # ground-cover ratio (module area / land area)
    crop_fraction: float             # retained crop yield vs open field (0 if none)
    uses_land: bool                  # False for floating (water)
    note: str
    source: str
    # scenario overrides
    tilt_deg: float = C.SITE_LATITUDE
    racking: str = "open_rack_glass_glass"
    vertical_ew: bool = False
    cooling_gain: float = 0.0        # extra yield fraction (floating evaporative cooling)


ARCHETYPES = [
    LandArchetype(
        "Ground-mount (reference)", gcr=0.40, crop_fraction=0.0, uses_land=True,
        note="conventional fixed-tilt rows", source="NREL land-use literature (~0.4 GCR)"),
    LandArchetype(
        "Agrivoltaics", gcr=0.28, crop_fraction=0.85, uses_land=True,
        note="elevated, widely spaced; crops/grazing beneath",
        source="Dupraz 2011 / Weselek 2019 LER 1.2-1.7; crop fraction ~0.85"),
    LandArchetype(
        "Vertical bifacial E-W", gcr=0.38, crop_fraction=0.90, uses_land=True,
        note="panels on edge; morning/evening peaks; land between rows farmed",
        source="Next2Sun vertical bifacial field data", vertical_ew=True),
    LandArchetype(
        "Floating PV", gcr=0.40, crop_fraction=0.0, uses_land=False,
        note="on water; no land; evaporative cooling lifts yield",
        source="World Bank/SERIS floating PV; cooling ~+3%", cooling_gain=0.03),
]

MODULE_EFF = 0.207                    # reference module efficiency (PERC class)
BIFACIALITY = 0.8                     # rear-face response of a bifacial module


def _yield_for(arch: LandArchetype, weather):
    """Annual specific yield (kWh/kWp) and hourly AC for an archetype."""
    if arch.vertical_ew:
        # One bifacial module stood vertical: the east face is the "front", the
        # west face is the "rear" responding at BIFACIALITY. Per single nameplate.
        east = simulate(Scenario(name="v-east", tilt_deg=90, azimuth_deg=90,
                                 racking=arch.racking, module_eff=MODULE_EFF),
                        weather=weather)
        west = simulate(Scenario(name="v-west", tilt_deg=90, azimuth_deg=270,
                                 racking=arch.racking, module_eff=MODULE_EFF),
                        weather=weather)
        sy = east.specific_yield + BIFACIALITY * west.specific_yield
        hourly = east.hourly_ac_w + BIFACIALITY * west.hourly_ac_w
        return sy, hourly
    sim = simulate(Scenario(name=arch.name, tilt_deg=arch.tilt_deg,
                            racking=arch.racking, module_eff=MODULE_EFF),
                   weather=weather)
    sy = sim.specific_yield * (1.0 + arch.cooling_gain)
    return sy, sim.hourly_ac_w * (1.0 + arch.cooling_gain)


def land_metrics(weather=None) -> pd.DataFrame:
    """Per-archetype land-use efficiency and Land Equivalent Ratio.

    - energy_per_module_m2 = specific_yield * module_eff
    - energy_per_land_m2   = energy_per_module_m2 * GCR
    - LER = energy_yield_fraction + crop_fraction (vs the ground-mount baseline)
    """
    if weather is None:
        weather = reference_weather()
    rows = []
    for arch in ARCHETYPES:
        sy, _ = _yield_for(arch, weather)
        e_mod = sy * MODULE_EFF                       # kWh/m^2 of module / yr
        e_land = e_mod * arch.gcr                     # kWh/m^2 of land / yr
        rows.append({
            "archetype": arch.name, "gcr": arch.gcr,
            "specific_yield": sy,
            "energy_per_module_m2": e_mod,
            "energy_per_land_m2": e_land,
            "crop_fraction": arch.crop_fraction,
            "uses_land": arch.uses_land,
            "note": arch.note, "source": arch.source,
        })
    df = pd.DataFrame(rows)

    # LER: energy fraction is land-energy relative to the densest solar-only
    # baseline (the ground-mount reference); add retained crop fraction.
    ref_land = df.loc[df["archetype"] == "Ground-mount (reference)",
                      "energy_per_land_m2"].iloc[0]
    df["energy_fraction"] = df["energy_per_land_m2"] / ref_land
    df["ler"] = df["energy_fraction"] + df["crop_fraction"]
    return df


def average_day_profile(weather=None) -> pd.DataFrame:
    """Average-day hourly AC for fixed-optimal vs vertical east-west.

    Demonstrates the grid-value shift: vertical east-west generation peaks in the
    morning and evening rather than at midday.
    """
    if weather is None:
        weather = reference_weather()
    fixed = simulate(Scenario(name="fixed", tilt_deg=C.SITE_LATITUDE,
                              racking="open_rack_glass_glass", module_eff=MODULE_EFF),
                     weather=weather)
    vert_arch = next(a for a in ARCHETYPES if a.vertical_ew)
    _, vert_hourly = _yield_for(vert_arch, weather)

    def by_hour(series):
        g = series.groupby(series.index.hour).mean()
        return g.reindex(range(24)).fillna(0.0)

    # Normalise each to its own peak so the *shape* (timing) is comparable.
    f = by_hour(fixed.hourly_ac_w)
    v = by_hour(vert_hourly)
    return pd.DataFrame({
        "hour": range(24),
        "fixed_optimal": (f / f.max()).values,
        "vertical_ew": (v / v.max()).values,
    })
