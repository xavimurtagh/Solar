"""Seven decades of certified efficiency records — loading and analysis.

Answers *"what has been done?"*  The data lives in cited CSVs under ``data/``;
this module loads them, validates that every row carries a real source, and
derives the trends the report needs (improvement rate per technology, and the
gap between laboratory records and the commercial fleet).
"""

from __future__ import annotations

from importlib.resources import files

import numpy as np
import pandas as pd


def _read(name: str) -> pd.DataFrame:
    with files("solarlab.data").joinpath(name).open("r", encoding="utf-8") as fh:
        return pd.read_csv(fh)


def load_milestones() -> pd.DataFrame:
    df = _read("milestones.csv")
    validate_milestones(df)
    return df


def load_module_market() -> pd.DataFrame:
    return _read("module_market.csv")


def load_technologies() -> pd.DataFrame:
    return _read("technologies.csv")


def validate_milestones(df: pd.DataFrame) -> None:
    """Raise ``ValueError`` if the milestones table is malformed or uncited."""
    required = {"year", "technology", "efficiency_pct", "kind",
                "organization", "source", "note"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"milestones.csv missing columns: {sorted(missing)}")
    if not df["year"].between(1950, 2026).all():
        raise ValueError("milestones.csv has a year outside 1950-2026")
    if not df["efficiency_pct"].between(0, 50).all():
        raise ValueError("milestones.csv has an efficiency outside 0-50%")
    if not df["kind"].isin({"cell", "module"}).all():
        raise ValueError("milestones.csv 'kind' must be cell or module")
    short = df["source"].astype(str).str.len() < 15
    if short.any():
        raise ValueError(f"{int(short.sum())} milestone row(s) have no real citation")


def improvement_stats(df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Per-technology improvement rate (percentage points per decade).

    Fits a straight line to each technology's *cell* records over time.  Single
    -record technologies report a NaN slope (no trend to fit).
    """
    if df is None:
        df = load_milestones()
    cells = df[df["kind"] == "cell"]
    rows = []
    for tech, g in cells.groupby("technology"):
        g = g.sort_values("year")
        first, last = g.iloc[0], g.iloc[-1]
        if len(g) >= 2 and g["year"].nunique() >= 2:
            slope = np.polyfit(g["year"], g["efficiency_pct"], 1)[0]
        else:
            slope = np.nan
        rows.append({
            "technology": tech,
            "first_year": int(first["year"]),
            "first_pct": float(first["efficiency_pct"]),
            "latest_year": int(last["year"]),
            "latest_pct": float(last["efficiency_pct"]),
            "pp_per_decade": slope * 10 if slope == slope else np.nan,
        })
    return pd.DataFrame(rows).sort_values("latest_pct", ascending=False).reset_index(drop=True)


def lab_to_market_gap(milestones: pd.DataFrame | None = None,
                      market: pd.DataFrame | None = None) -> dict:
    """Quantify the gap between the best lab cell and the commercial fleet.

    Returns the latest record silicon *cell*, the latest average commercial
    *module*, their difference in percentage points, and an estimate of the
    lag: how many years it took the commercial average to reach the efficiency
    a record silicon cell had already demonstrated decades earlier.
    """
    if milestones is None:
        milestones = load_milestones()
    if market is None:
        market = load_module_market()

    si = milestones[(milestones["technology"] == "Silicon")
                    & (milestones["kind"] == "cell")].sort_values("year")
    best_cell = si.iloc[-1]
    latest_market = market.sort_values("year").iloc[-1]
    gap_pp = float(best_cell["efficiency_pct"] - latest_market["avg_module_eff_pct"])

    # Lag: find the earliest year a record cell reached today's fleet efficiency.
    target = latest_market["avg_module_eff_pct"]
    reached = si[si["efficiency_pct"] >= target]
    lag_years = (int(latest_market["year"] - reached.iloc[0]["year"])
                 if not reached.empty else None)

    return {
        "best_cell_pct": float(best_cell["efficiency_pct"]),
        "best_cell_year": int(best_cell["year"]),
        "market_pct": float(latest_market["avg_module_eff_pct"]),
        "market_year": int(latest_market["year"]),
        "gap_pp": gap_pp,
        "lab_to_market_lag_years": lag_years,
    }
