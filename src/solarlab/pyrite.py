"""Part XIV — cracking pyrite: a quantified voltage roadmap.

Part VI diagnosed why iron pyrite (FeS2) fails: a catastrophic voltage deficit, its
external radiative efficiency (ERE) stuck near 1e-9. The natural next question — the
one the user asked — is *how* you would fix it, and how much each fix buys.

This module maps the real, physically-motivated interventions researchers pursue
onto ERE improvements, and runs each through the same detailed-balance model (Part
I/VI) to turn a vague "cure the voltage" into a numerical target ladder. The toolkit
cannot passivate a crystal in a lab — but it can say exactly how good each step must
get for pyrite to become a real solar cell.
"""

from __future__ import annotations

import pandas as pd

from .constants import PYRITE_EG_EV
from .spectrum import SpectrumIntegrals, load_am15g
from .sq import sq_cell

# Each rung is a cumulative intervention and the ERE it would plausibly unlock.
# The steps reflect the actual failure modes of pyrite and the levers that tamed
# silicon and perovskites; the ERE values are illustrative targets, not promises.
INTERVENTIONS = [
    ("Today's pyrite cell", 1e-9,
     "A sulfur-poor, metallic-like surface layer pins the Fermi level and shorts the voltage."),
    ("+ Surface passivation", 1e-7,
     "Restore surface stoichiometry / cap with a passivating layer to unpin the surface."),
    ("+ Bulk sulfur-vacancy control", 1e-5,
     "Sulfur-rich growth and annealing to remove the deep traps inside the crystal."),
    ("+ Phase-pure films", 1e-4,
     "Eliminate marcasite / pyrrhotite secondary phases that leak current."),
    ("+ Carrier-selective contacts", 1e-2,
     "Add electron- and hole-selective transport layers (the heterojunction / perovskite lesson) so the junction no longer relies on pyrite's own surface."),
]


def voltage_roadmap() -> pd.DataFrame:
    """Efficiency and Voc at each rung of the pyrite voltage-repair ladder."""
    spec = SpectrumIntegrals(load_am15g())
    rows = []
    for name, ere, mechanism in INTERVENTIONS:
        cell = sq_cell(PYRITE_EG_EV, spec, ere=ere)
        rows.append({
            "stage": name, "ere": ere, "voc_v": cell.voc_v, "eta": cell.eta,
            "mechanism": mechanism,
        })
    return pd.DataFrame(rows)


def roadmap_summary() -> dict:
    df = voltage_roadmap()
    return {
        "today_eta": float(df.iloc[0]["eta"]),
        "today_voc": float(df.iloc[0]["voc_v"]),
        "final_eta": float(df.iloc[-1]["eta"]),
        "final_voc": float(df.iloc[-1]["voc_v"]),
        "n_steps": len(df),
    }
