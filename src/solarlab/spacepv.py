"""Part X — solar off-world: escaping intermittency by leaving the planet.

The third answer to the value wall (Part VII). Firming (VIII) and power-to-X (IX)
work *around* the night and the weather. Space-based solar power (SBSP) abolishes
them: in geostationary orbit the sun never sets and no atmosphere dims it, so a
solar satellite runs at ~95% capacity factor and ~1361 W/m^2 — then beams the
power to a ground rectenna by microwave.

The economics are dominated by one number: the cost of launching mass to orbit.
This module computes SBSP's levelized cost as a function of launch cost, and finds
the launch-cost threshold at which it undercuts *firm* terrestrial solar — the
correct comparison, because both deliver round-the-clock power.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

# Launch-cost reference points ($/kg to LEO).
LAUNCH_FALCON9 = 2700.0
LAUNCH_STARSHIP_TARGET = 100.0
LAUNCH_STARSHIP_EARLY = 1000.0

# Terrestrial benchmarks for comparison ($/MWh). SBSP is ~24/7, so the honest
# comparison is FIRM terrestrial solar (Part VIII), not raw daytime solar.
FIRM_TERRESTRIAL_HIGH = 72.0      # high-resource solar+storage, 95% (Part VIII)
FIRM_TERRESTRIAL_MODERATE = 130.0  # moderate-site solar+storage, 95% (Part VIII)
RAW_TERRESTRIAL = 30.0            # unfirmed daytime solar


@dataclass
class SBSPParams:
    """All masses/costs are per kW of *ground-delivered* power (beam and DC-RF-DC
    conversion losses are folded into the specific mass and hardware cost)."""

    specific_mass_kg_per_kw: float = 20.0   # satellite system mass per kW ground
    hardware_cost_per_kw: float = 2000.0    # satellite electronics + ground rectenna
    capacity_factor: float = 0.95
    discount_rate: float = 0.08
    lifetime_years: int = 20
    opex_per_kw_yr: float = 40.0


# Three technology scenarios spanning the credible design space.
SCENARIOS = {
    "Optimistic (10 kg/kW)": SBSPParams(specific_mass_kg_per_kw=10.0,
                                        hardware_cost_per_kw=1500.0),
    "Nominal (20 kg/kW)": SBSPParams(specific_mass_kg_per_kw=20.0),
    "Conservative (50 kg/kW)": SBSPParams(specific_mass_kg_per_kw=50.0,
                                          hardware_cost_per_kw=3000.0),
}


def sbsp_lcoe(launch_cost_per_kg: float, params: SBSPParams | None = None) -> float:
    """Levelized cost of space-based solar ($/MWh) at a given launch cost."""
    p = params or SBSPParams()
    crf = (p.discount_rate * (1 + p.discount_rate) ** p.lifetime_years
           / ((1 + p.discount_rate) ** p.lifetime_years - 1))
    launch_capex = p.specific_mass_kg_per_kw * launch_cost_per_kg
    capex = launch_capex + p.hardware_cost_per_kw
    annual_cost = crf * capex + p.opex_per_kw_yr
    delivered_kwh = 8760.0 * p.capacity_factor
    return annual_cost / delivered_kwh * 1000.0    # $/kWh -> $/MWh


def sbsp_curve(launch_costs=None, params: SBSPParams | None = None) -> pd.DataFrame:
    """SBSP LCOE across a range of launch costs."""
    if launch_costs is None:
        launch_costs = np.logspace(np.log10(50), np.log10(5000), 40)
    return pd.DataFrame({
        "launch_cost_per_kg": launch_costs,
        "lcoe_usd_mwh": [sbsp_lcoe(float(c), params) for c in launch_costs],
    })


def crossover_launch_cost(target_usd_mwh: float,
                          params: SBSPParams | None = None) -> float:
    """Launch cost ($/kg) at which SBSP LCOE equals ``target_usd_mwh``.

    Solving the linear LCOE expression for launch cost. Returns +inf if the
    fixed (hardware) cost alone already exceeds the target.
    """
    p = params or SBSPParams()
    crf = (p.discount_rate * (1 + p.discount_rate) ** p.lifetime_years
           / ((1 + p.discount_rate) ** p.lifetime_years - 1))
    delivered_kwh = 8760.0 * p.capacity_factor
    # target = (crf*(mass*launch + hardware) + opex) / delivered * 1000
    allowed_annual = target_usd_mwh / 1000.0 * delivered_kwh
    allowed_capex = (allowed_annual - p.opex_per_kw_yr) / crf
    launch_capex = allowed_capex - p.hardware_cost_per_kw
    if launch_capex <= 0:
        return float("-inf")
    return launch_capex / p.specific_mass_kg_per_kw
