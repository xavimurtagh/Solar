"""Material intensity, abundance, and the terawatt ceiling.

This is the part of the analysis that conventional efficiency-and-cost framing
misses. To decarbonise, the world must build solar at the scale of **tens of
terawatts**, sustained at a few TW per year. At that scale the binding
constraint is not efficiency, and often not even dollars — it is **how many
grams of a scarce element each watt requires**, set against how many tonnes of
that element the Earth yields per year.

A technology's "ceiling" is the most generating capacity (GW per year) that
global supply of its scarcest ingredient could support:

    GW_per_year = (annual_production_tonnes * supply_share) / intensity_g_per_kW

The same arithmetic that condemns tellurium-limited CdTe to a few GW/year shows
why replacing silver with electroplated copper lifts silicon PV's ceiling from
~1 TW/year to effectively unlimited.
"""

from __future__ import annotations

from importlib.resources import files

import pandas as pd

# Reference: cumulative PV needed for deep decarbonisation is ~60-75 TW by 2050,
# implying a sustained build rate of very roughly 1-3 TW/year (IEA Net Zero /
# IRENA scenarios). Used only as an annotation line, not in any calculation.
NET_ZERO_TW_PER_YEAR = 2.0


def load_materials() -> pd.DataFrame:
    with files("solarlab.data").joinpath("materials.csv").open("r", encoding="utf-8") as fh:
        return pd.read_csv(fh)


def load_bom() -> pd.DataFrame:
    with files("solarlab.data").joinpath("bom.csv").open("r", encoding="utf-8") as fh:
        return pd.read_csv(fh)


def _materials_indexed() -> pd.DataFrame:
    return load_materials().set_index("element")


def technology_bom(technology: str, swaps: dict | None = None) -> pd.DataFrame:
    """Bill of materials for ``technology`` (g/kW per element), summed over roles.

    ``swaps`` maps an element to a replacement (e.g. ``{"Silver": "Copper"}``).
    The replacement inherits the same g/kW intensity — a deliberately
    conservative assumption for metallization, where copper deposits at a
    comparable thickness to the silver it replaces; the dramatic effect comes
    from copper's price and abundance, not from using less of it. Indium->Zinc
    represents swapping an ITO transparent conductor for aluminium-doped ZnO.
    """
    bom = load_bom()
    sub = bom[bom["technology"] == technology].copy()
    if sub.empty:
        raise ValueError(f"unknown technology: {technology}")
    if swaps:
        sub["element"] = sub["element"].replace(swaps)
    return (sub.groupby("element", as_index=False)["intensity_g_per_kw"]
            .sum().sort_values("intensity_g_per_kw", ascending=False))


def material_cost_per_w(technology: str, swaps: dict | None = None) -> float:
    """Raw-material cost ($/W) of a technology's bill of materials."""
    mats = _materials_indexed()
    bom = technology_bom(technology, swaps)
    total = 0.0
    for _, row in bom.iterrows():
        price = mats.loc[row["element"], "price_usd_per_kg"]
        # g/kW * $/kg / 1e6 = $/W   (g->kg /1000, kW->W /1000)
        total += row["intensity_g_per_kw"] * price / 1e6
    return float(total)


def scarce_elements() -> set[str]:
    """Elements whose annual production is small enough to bind PV scale-up."""
    mats = load_materials()
    return set(mats[mats["annual_production_tonnes"] < 50000]["element"])


def deployment_ceiling(technology: str, supply_share: float = 0.5,
                       swaps: dict | None = None) -> dict:
    """Max annual deployment (GW/yr) global supply could support, and the
    element that limits it.

    ``supply_share`` is the fraction of each element's world production that PV
    could plausibly claim (default 50%).
    """
    mats = _materials_indexed()
    bom = technology_bom(technology, swaps)
    limits = []
    for _, row in bom.iterrows():
        el = row["element"]
        intensity = row["intensity_g_per_kw"]
        if intensity <= 0:
            continue
        production = mats.loc[el, "annual_production_tonnes"]
        gw_per_year = production * supply_share / intensity
        limits.append((el, gw_per_year, intensity))
    binding_el, gw, intensity = min(limits, key=lambda t: t[1])
    return {
        "technology": technology,
        "binding_element": binding_el,
        "gw_per_year": gw_per_year_round(gw),
        "tw_per_year": gw / 1000.0,
        "binding_intensity_g_per_kw": intensity,
        "binding_is_scarce": binding_el in scarce_elements(),
        "supply_share": supply_share,
    }


def gw_per_year_round(x: float) -> float:
    return round(x, 2)


def ceiling_table(technologies: list[str], supply_share: float = 0.5) -> pd.DataFrame:
    """Deployment ceilings for several technologies, sorted ascending (tightest
    constraint first)."""
    rows = [deployment_ceiling(t, supply_share) for t in technologies]
    df = pd.DataFrame(rows)
    return df.sort_values("tw_per_year").reset_index(drop=True)


# The headline substitutions: scarce element -> abundant replacement.
SILVER_TO_COPPER = {"Silver": "Copper"}
INDIUM_TO_ZINC = {"Indium": "Zinc"}          # ITO -> aluminium-doped ZnO (AZO)
LEAD_TO_TIN = {"Lead": "Tin"}                # lead-free (tin) perovskite
ABUNDANT_SWAP = {**SILVER_TO_COPPER, **INDIUM_TO_ZINC, **LEAD_TO_TIN}


def substitution_effect(technology: str, swaps: dict,
                        supply_share: float = 0.5) -> dict:
    """Cost and ceiling impact of a material substitution.

    Returns before/after material cost ($/W) and deployment ceiling (TW/yr), plus
    the multiplicative change in the ceiling — the number that matters most for
    scaling.
    """
    base_cost = material_cost_per_w(technology)
    new_cost = material_cost_per_w(technology, swaps)
    base_ceiling = deployment_ceiling(technology, supply_share)
    new_ceiling = deployment_ceiling(technology, supply_share, swaps)
    return {
        "technology": technology,
        "swaps": swaps,
        "material_cost_before": base_cost,
        "material_cost_after": new_cost,
        "material_cost_delta_per_w": new_cost - base_cost,
        "tw_per_year_before": base_ceiling["tw_per_year"],
        "tw_per_year_after": new_ceiling["tw_per_year"],
        "ceiling_multiplier": (new_ceiling["tw_per_year"] / base_ceiling["tw_per_year"]
                               if base_ceiling["tw_per_year"] > 0 else float("inf")),
        "binding_before": base_ceiling["binding_element"],
        "binding_after": new_ceiling["binding_element"],
    }
