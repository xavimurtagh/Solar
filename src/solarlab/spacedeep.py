"""Part XV — space solar, seriously: the climate, the beam, and the scale.

Part X showed space-based solar (SBSP) is a launch-cost bet. This part takes the
harder, fairer questions seriously and answers them with numbers:

- **Climate cost of launch** — rockets burn fuel; what is the carbon payback?
- **Getting the energy down** — the DC -> microwave -> atmosphere -> rectenna ->
  DC chain, end to end.
- **Scalability** — could SBSP actually power the world, or only a slice of it?

(End-of-life, debris and maintenance are quantified where possible and discussed
in the report.) The verdict it computes: launch carbon is *not* the obstacle
(payback is months); the obstacle is sheer **mass to orbit** — SBSP is a credible
premium, firm-power *complement*, not a replacement for terrestrial solar.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# Launch emissions. Kerosene (RP-1) rockets ~ this per kg to LEO; methalox is
# similar-to-lower on CO2 but adds stratospheric soot/water (flagged in report).
LAUNCH_CO2_PER_KG = 20.0           # kg CO2 per kg payload to orbit
STARSHIP_PAYLOAD_T = 150.0         # tonnes to LEO per launch (target)
WORLD_POWER_TW = 20.0              # rough fully-electrified world primary power

# Beaming chain stage efficiencies (DC in space -> DC on the ground).
BEAM_CHAIN = [
    ("DC -> microwave (transmitter)", 0.85),
    ("Beam through atmosphere (5.8 GHz)", 0.97),
    ("Rectenna capture (pointing/spillover)", 0.85),
    ("Microwave -> DC (rectifier)", 0.85),
]


def beaming_chain() -> pd.DataFrame:
    """Stage and cumulative efficiency of getting the energy from orbit to grid."""
    rows = []
    cum = 1.0
    for stage, eff in BEAM_CHAIN:
        cum *= eff
        rows.append({"stage": stage, "stage_eff": eff, "cumulative_eff": cum})
    return pd.DataFrame(rows)


def launch_carbon(specific_mass_kg_per_kw: float = 20.0,
                  mfg_co2_per_kw: float = 500.0, capacity_factor: float = 0.95,
                  lifetime_years: int = 20,
                  grid_intensity_g_per_kwh: float = 400.0,
                  launch_co2_per_kg: float = LAUNCH_CO2_PER_KG) -> dict:
    """Embodied carbon, lifetime CO2 intensity, and carbon payback of SBSP."""
    launch_co2_per_kw = specific_mass_kg_per_kw * launch_co2_per_kg   # kg CO2/kW
    embodied_kg = launch_co2_per_kw + mfg_co2_per_kw                  # kg CO2/kW
    annual_kwh = 8760.0 * capacity_factor
    lifetime_kwh = annual_kwh * lifetime_years
    intensity_g_kwh = embodied_kg * 1000.0 / lifetime_kwh
    # Payback: embodied carbon / annual carbon displaced from the grid.
    payback_years = embodied_kg * 1000.0 / (annual_kwh * grid_intensity_g_per_kwh)
    return {
        "launch_co2_per_kw": launch_co2_per_kw,
        "embodied_co2_per_kw": embodied_kg,
        "co2_intensity_g_per_kwh": intensity_g_kwh,
        "carbon_payback_years": payback_years,
    }


def rectenna_area_km2(power_gw: float, avg_density_w_m2: float = 150.0) -> float:
    """Ground-antenna area for a given delivered power (safety-limited density)."""
    return power_gw * 1e9 / avg_density_w_m2 / 1e6


def scalability(target_tw: float, specific_mass_kg_per_kw: float = 20.0,
                build_years: int = 30) -> dict:
    """Mass to orbit, launches and cadence to build ``target_tw`` of SBSP."""
    mass_t = target_tw * 1e9 * specific_mass_kg_per_kw / 1000.0       # tonnes
    launches = mass_t / STARSHIP_PAYLOAD_T
    launches_per_day = launches / (build_years * 365.0)
    return {
        "target_tw": target_tw,
        "mass_to_orbit_mt": mass_t / 1e6,            # million tonnes
        "launches": launches,
        "launches_per_day": launches_per_day,
        "rectenna_area_km2": rectenna_area_km2(target_tw * 1000.0),
    }


def scalability_curve(targets_tw=None) -> pd.DataFrame:
    if targets_tw is None:
        targets_tw = [0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0]
    return pd.DataFrame([scalability(t) for t in targets_tw])
