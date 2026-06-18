"""How to actually improve a real system — quantified, ranked levers.

Each lever changes exactly one thing about the reference rooftop and is scored
by the change in annual AC energy it produces, simulated with the same pvlib
chain.  Technology swaps are compared on a **fixed roof area** (the honest basis
for a homeowner with a finite roof): a more efficient module simply fits more
nameplate watts onto the same square metres.

The result is the actionable answer to the user's third question — a ranked list
from "biggest win" to "smallest", with a cited rationale for each.
"""

from __future__ import annotations

import pandas as pd

from .history import load_technologies
from .system import Scenario, simulate

# The reference system: an "average installed" PERC rooftop (~20% module).
BASE = Scenario()


def _tech_scenario(name: str, eff: float, gamma: float, note_status: str,
                   source: str) -> tuple[Scenario, str, str]:
    """A technology swap on the *same roof area* as BASE.

    Holding area fixed, nameplate scales with efficiency: a better module packs
    more watts onto the roof, which is the real-world efficiency win.
    """
    pdc0 = BASE.area_m2 * 1000.0 * eff
    sc = Scenario(name=f"{name} module", module_eff=eff, gamma_pdc=gamma,
                  pdc0_w=pdc0)
    note = f"{note_status}; same roof area, nameplate {pdc0/1000:.2f} kW"
    return sc, note, source


def lever_scenarios() -> list[tuple[Scenario, str, str]]:
    """All one-change-at-a-time scenarios as (scenario, note, source)."""
    techs = load_technologies().set_index("technology")
    out: list[tuple[Scenario, str, str]] = []

    # 1-3. Cell/module technology swaps (fixed roof area).
    for tech in ("TOPCon", "HJT", "Perovskite-Si tandem"):
        row = techs.loc[tech]
        out.append(_tech_scenario(
            tech, float(row["module_eff_frac"]), float(row["gamma_pdc_per_c"]),
            f"{row['status']} cell technology", str(row["source"])))

    # 4. Single-axis tracking (ground-mount framing).
    out.append((
        Scenario(name="Single-axis tracking", tracking=True),
        "ground-mount single-axis horizontal tracker, backtracking",
        "Energy gain typical +15-25% (NREL PVWatts / literature)"))

    # 5. Bifacial modules (rear-side collection).
    out.append((
        Scenario(name="Bifacial (+8% rear gain)", bifacial_gain=0.08),
        "rear-side irradiance gain, mid-range albedo",
        "Bifacial gain 5-15% (Fraunhofer ISE / literature)"))

    # 6. Better-ventilated racking (a citable proxy for active cooling).
    out.append((
        Scenario(name="Ventilated / cooled mounting", racking="open_rack_glass_polymer"),
        "open-rack airflow lowers cell temperature vs close roof mount",
        "Sandia SAPM thermal coefficient sets (King et al. 2004)"))

    # 7. Anti-soiling (coatings / cleaning).
    out.append((
        Scenario(name="Anti-soiling (2%->0.5%)", soiling_frac=0.005),
        "hydrophobic coating / cleaning reduces soiling loss",
        "Soiling loss typical 2% baseline (Dobos 2014 PVWatts)"))

    # 8. Premium high-efficiency inverter.
    out.append((
        Scenario(name="Premium inverter (96%->98.5%)", eta_inv_nom=0.985),
        "higher nominal inverter efficiency",
        "Modern string inverter CEC efficiency ~98.5%"))

    # 9. DC optimizers / microinverters (cut mismatch).
    out.append((
        Scenario(name="DC optimizers (mismatch 2%->0.3%)", mismatch_pct=0.3),
        "module-level power electronics cut array mismatch",
        "Mismatch reduction with MLPE (literature)"))

    return out


def run_levers(weather=None) -> pd.DataFrame:
    """Simulate every lever and rank by annual-energy improvement over BASE."""
    base = simulate(BASE, weather=weather)
    rows = []
    for sc, note, source in lever_scenarios():
        sim = simulate(sc, weather=weather)
        delta = 100.0 * (sim.e_ac_kwh - base.e_ac_kwh) / base.e_ac_kwh
        rows.append({
            "lever": sc.name,
            "e_ac_kwh": sim.e_ac_kwh,
            "delta_pct": delta,
            "note": note,
            "source": source,
        })
    df = pd.DataFrame(rows).sort_values("delta_pct", ascending=False)
    return df.reset_index(drop=True)
