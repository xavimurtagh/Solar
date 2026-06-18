"""Part VII — the value of time: why cheap solar is not the same as valuable solar.

LCOE (Parts I-II) treats every kilowatt-hour as equal. The grid does not. A
kilowatt-hour at the evening peak is worth many times one during the midday solar
glut — and as solar penetration rises, solar floods exactly the hours it depresses
the price of. This module quantifies that **value deflation** from first
principles on the hourly engine:

- a stylised but realistic hourly demand profile (evening-peaking, mild seasonal),
- a merit-order price that rises with residual (net) load and goes negative when
  solar oversupplies,
- the **value factor** (solar-weighted price / average price), **capture price**,
  and **curtailment** as functions of solar penetration.

The result reproduces what is already happening (Germany's capture rate fell from
73% to 48% in three years): solar's *cost* keeps falling while its *value* falls
faster. Cheap is not valuable.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .system import Scenario, reference_weather, simulate

# Merit-order price curve parameters ($/MWh). The value factor is a ratio, so the
# absolute scale is immaterial; the shape (price rising with net load, negative on
# oversupply) is what matters.
P_FLOOR = 45.0
P_PEAK = 170.0
P_NEGATIVE = -5.0          # negative pricing during pure oversupply hours
PRICE_GAMMA = 1.1          # convexity of the merit-order curve

# Stylised relative demand by hour of day (evening-peaking; classic load shape).
_HOUR_WEIGHTS = np.array([
    0.72, 0.68, 0.66, 0.66, 0.70, 0.78,   # 0-5 overnight trough
    0.88, 0.98, 1.02, 1.03, 1.04, 1.05,   # 6-11 morning ramp / midday
    1.05, 1.04, 1.02, 1.02, 1.06, 1.18,   # 12-17 afternoon into ramp
    1.30, 1.28, 1.18, 1.02, 0.90, 0.80,   # 18-23 evening peak, decline
])
# Mild seasonal multiplier by month (summer cooling + winter heating peaks).
_MONTH_WEIGHTS = np.array([
    1.08, 1.05, 0.95, 0.88, 0.90, 1.02,
    1.12, 1.12, 0.98, 0.88, 0.95, 1.07,
])


def solar_shape(weather=None) -> pd.Series:
    """Normalised hourly solar generation (mean = 1) over the reference year."""
    if weather is None:
        weather = reference_weather()
    # Grid-scale solar uses single-axis tracking, giving a broader midday plateau
    # than fixed tilt — the right shape for a penetration/value analysis.
    sim = simulate(Scenario(name="value-ref", tracking=True), weather=weather)
    s = sim.hourly_ac_w.astype(float)
    return s / s.mean()


def demand_profile(index: pd.DatetimeIndex) -> pd.Series:
    """Normalised hourly demand (mean = 1): evening-peaking with a mild season."""
    hours = index.hour.to_numpy()
    months = index.month.to_numpy()
    d = _HOUR_WEIGHTS[hours] * _MONTH_WEIGHTS[months - 1]
    s = pd.Series(d, index=index)
    return s / s.mean()


def _price(residual: np.ndarray, r_max: float) -> np.ndarray:
    """Merit-order price ($/MWh) as a function of residual (net) load."""
    out = np.empty_like(residual)
    over = residual <= 0
    pos = ~over
    out[over] = P_NEGATIVE
    frac = np.clip(residual[pos] / r_max, 0.0, 1.0)
    out[pos] = P_FLOOR + (P_PEAK - P_FLOOR) * frac**PRICE_GAMMA
    return out


def value_metrics(penetration: float, solar: pd.Series,
                  demand: pd.Series) -> dict:
    """Value factor, capture price, mean price, and curtailment at one penetration.

    ``penetration`` is the share of annual demand energy met by solar generation
    (both series are mean-normalised, so solar contributes ``penetration * solar``
    in units of mean demand).
    """
    d = demand.to_numpy()
    s = solar.to_numpy()
    residual = d - penetration * s
    r_max = float(d.max())                       # peak demand sets the price ceiling
    price = _price(residual, r_max)

    mean_price = float(price.mean())
    # Capture price: revenue-weighted by solar generation.
    capture = float(np.sum(price * s) / np.sum(s))
    value_factor = capture / mean_price if mean_price else float("nan")

    # Curtailment: solar above instantaneous demand is spilled (no storage here).
    spilled = np.maximum(penetration * s - d, 0.0)
    curtailment = float(spilled.sum() / (penetration * s.sum())) if penetration > 0 else 0.0

    return {
        "penetration": penetration,
        "value_factor": value_factor,
        "capture_price": capture,
        "mean_price": mean_price,
        "curtailment": curtailment,
    }


def value_curve(weather=None, penetrations=None) -> pd.DataFrame:
    """Value factor / capture price / curtailment across solar penetration."""
    if penetrations is None:
        penetrations = np.linspace(0.0, 0.6, 25)
    solar = solar_shape(weather)
    demand = demand_profile(solar.index)
    rows = [value_metrics(float(p), solar, demand) for p in penetrations]
    return pd.DataFrame(rows)


def average_day_price(penetration: float, weather=None) -> pd.DataFrame:
    """Average-day demand, solar, and price at a given penetration (for plotting)."""
    solar = solar_shape(weather)
    demand = demand_profile(solar.index)
    residual = demand.to_numpy() - penetration * solar.to_numpy()
    price = _price(residual, float(demand.to_numpy().max()))
    df = pd.DataFrame({
        "hour": solar.index.hour,
        "demand": demand.to_numpy(),
        "solar": penetration * solar.to_numpy(),
        "price": price,
    })
    return df.groupby("hour").mean().reset_index()
