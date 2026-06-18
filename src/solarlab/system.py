"""A real rooftop system, hour by hour, with pvlib.

The detailed-balance limit explains the *cell*.  A deployed *system* loses more:
the sun moves, the module heats up, dust accumulates, wiring and the inverter
take their cut.  This module simulates one full year (8760 hours) of a
reference rooftop array and attributes the gap between nameplate and delivered
AC energy to each named mechanism.

The model chain is written out explicitly (rather than via pvlib's
``ModelChain``) so each physical step is visible and documented.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
import pvlib
from pvlib.location import Location
from pvlib.temperature import TEMPERATURE_MODEL_PARAMETERS

from . import constants as C


@dataclass
class Scenario:
    """One rooftop configuration.  Defaults describe an "average installed"
    PERC system — the ~20%-efficient panel the user is asking about."""

    name: str = "PERC rooftop (reference)"
    module_eff: float = 0.207          # STC module efficiency (LONGi Hi-MO 5 class)
    gamma_pdc: float = -0.0034         # 1/degC, power temperature coefficient
    pdc0_w: float = 5000.0             # 5 kW DC nameplate
    tilt_deg: float = C.SITE_LATITUDE  # tilt = latitude (annual-yield rule of thumb)
    azimuth_deg: float = 180.0         # due south
    tracking: bool = False             # single-axis horizontal N-S, backtracking
    gcr: float = 0.35
    racking: str = "close_mount_glass_glass"   # rooftop (poorly ventilated)
    bifacial_gain: float = 0.0         # extra energy fraction from rear-side light
    soiling_frac: float = C.SOILING_FRAC
    dc_ac_ratio: float = 1.2
    eta_inv_nom: float = 0.96
    # DC array losses (percent) — defaults from constants.PVWATTS_LOSSES.
    mismatch_pct: float = 2.0
    wiring_pct: float = 2.0
    connections_pct: float = 0.5
    lid_pct: float = 1.5
    availability_pct: float = 3.0

    @property
    def area_m2(self) -> float:
        """Active module area implied by nameplate and STC efficiency."""
        return self.pdc0_w / (C.STC_IRRADIANCE * self.module_eff)


@dataclass
class SimResult:
    scenario: Scenario
    ghi_kwh_m2: float
    poa_kwh_m2: float
    e_dc_kwh: float
    e_ac_kwh: float
    pr: float                 # performance ratio (POA basis)
    eta_system: float         # delivered AC / incident POA energy
    specific_yield: float     # kWh per kWp
    monthly: pd.DataFrame
    attribution: pd.DataFrame
    hourly_ac_w: pd.Series | None = None   # 8760-hour AC power (for diurnal profiles)


def reference_weather():
    """Load the bundled Greensboro NC TMY3 (8760 hours), offline-reproducible.

    Returns ``(data, meta)`` with columns ``ghi/dni/dhi/temp_air/wind_speed``.
    """
    data_path = Path(pvlib.__file__).parent / "data" / "723170TYA.CSV"
    try:
        data, meta = pvlib.iotools.read_tmy3(
            data_path, coerce_year=2023, map_variables=True)
    except UnicodeDecodeError:  # pragma: no cover - encoding safety net
        data, meta = pvlib.iotools.read_tmy3(
            data_path, coerce_year=2023, map_variables=True, encoding="iso-8859-1")
    # TMY3 records midnight as the previous day's "hour 24", so coerce_year
    # leaves the final sample stamped 1 Jan of the *next* year. Force every
    # timestamp into a single calendar year so the result is a clean 8760-hour
    # year that resamples to exactly 12 months.
    data.index = data.index.map(lambda t: t.replace(year=2023))
    data = data.sort_index()
    data = data[~data.index.duplicated(keep="first")]
    return data, meta


def _surface_orientation(sc: Scenario, solpos: pd.DataFrame):
    """Return (surface_tilt, surface_azimuth) series for fixed or tracked arrays."""
    if not sc.tracking:
        tilt = pd.Series(sc.tilt_deg, index=solpos.index)
        azim = pd.Series(sc.azimuth_deg, index=solpos.index)
        return tilt, azim
    tracker = pvlib.tracking.singleaxis(
        solpos["apparent_zenith"], solpos["azimuth"],
        axis_tilt=0, axis_azimuth=sc.azimuth_deg, max_angle=60,
        backtrack=True, gcr=sc.gcr)
    # At night the tracker angle is undefined; flatten the panel.
    tilt = tracker["surface_tilt"].fillna(0.0)
    azim = tracker["surface_azimuth"].fillna(sc.azimuth_deg)
    return tilt, azim


def simulate(sc: Scenario, weather=None) -> SimResult:
    """Run the year-long model chain for scenario ``sc``."""
    if weather is None:
        weather = reference_weather()
    data, meta = weather
    times = data.index
    loc = Location(meta["latitude"], meta["longitude"],
                  altitude=meta.get("altitude", 0))

    # 1. Solar position. Irradiance is hour-averaged and TMY3 stamps the hour
    #    end, so evaluate the sun at the interval midpoint for accuracy.
    solpos = loc.get_solarposition(times - pd.Timedelta("30min"))
    solpos.index = times

    # 2. Array orientation (fixed tilt or single-axis tracker).
    surface_tilt, surface_azimuth = _surface_orientation(sc, solpos)

    # 3. Transpose GHI/DNI/DHI onto the plane of array (Hay-Davies model).
    dni_extra = pvlib.irradiance.get_extra_radiation(times)
    poa = pvlib.irradiance.get_total_irradiance(
        surface_tilt, surface_azimuth,
        solpos["apparent_zenith"], solpos["azimuth"],
        dni=data["dni"], ghi=data["ghi"], dhi=data["dhi"],
        dni_extra=dni_extra, model="haydavies")
    poa_global = poa["poa_global"].fillna(0.0)

    # 4. Soiling: an optical loss applied to plane-of-array irradiance.
    effective_poa = poa_global * (1.0 - sc.soiling_frac)

    # 5. Cell temperature (Sandia thermal model for the chosen racking).
    therm = TEMPERATURE_MODEL_PARAMETERS["sapm"][sc.racking]
    temp_cell = pvlib.temperature.sapm_cell(
        effective_poa, data["temp_air"], data["wind_speed"], **therm)

    # 6. DC power (PVWatts). The counterfactual at a fixed 25 degC isolates the
    #    temperature loss.
    pdc = pvlib.pvsystem.pvwatts_dc(
        effective_poa, temp_cell, pdc0=sc.pdc0_w, gamma_pdc=sc.gamma_pdc)
    pdc_no_temp = pvlib.pvsystem.pvwatts_dc(
        effective_poa, pd.Series(C.STC_TEMP_C, index=times),
        pdc0=sc.pdc0_w, gamma_pdc=sc.gamma_pdc)

    # 7. DC array losses (mismatch, wiring, connections, LID). Cited PVWatts v5.
    dc_loss_pct = pvlib.pvsystem.pvwatts_losses(
        soiling=0, shading=0, snow=0,
        mismatch=sc.mismatch_pct, wiring=sc.wiring_pct,
        connections=sc.connections_pct, lid=sc.lid_pct,
        nameplate_rating=0, age=0, availability=0)
    pdc_net = pdc * (1.0 - dc_loss_pct / 100.0)

    # 8. Inverter (PVWatts model); DC/AC ratio sets the inverter rating.
    pac = pvlib.inverter.pvwatts(
        pdc_net, pdc0=sc.pdc0_w / sc.dc_ac_ratio, eta_inv_nom=sc.eta_inv_nom)

    # 9. Availability and bifacial gain (constant multipliers).
    pac = pac * (1.0 - sc.availability_pct / 100.0) * (1.0 + sc.bifacial_gain)

    # --- Energy bookkeeping (hourly samples => 1 h each; Wh -> kWh) ----------
    def kwh(series):
        return float(np.nansum(series)) / 1000.0

    ghi_kwh_m2 = kwh(data["ghi"])
    poa_kwh_m2 = kwh(effective_poa)
    e_dc_no_temp = kwh(pdc_no_temp)
    e_dc = kwh(pdc)
    e_dc_net = kwh(pdc_net)
    e_ac = kwh(pac)

    pr = e_ac / (sc.pdc0_w / 1000.0 * poa_kwh_m2)
    eta_system = e_ac / (poa_kwh_m2 * sc.area_m2) if poa_kwh_m2 > 0 else 0.0
    specific_yield = e_ac / (sc.pdc0_w / 1000.0)

    # Loss attribution: energy remaining after each stage (percent of POA-ideal).
    e_poa_ideal = sc.pdc0_w / 1000.0 * poa_kwh_m2   # DC if always at STC efficiency
    attribution = pd.DataFrame([
        {"stage": "POA irradiance (module-plane, soiled)", "energy_kwh": e_poa_ideal,
         "loss_label": "reference: nameplate x insolation"},
        {"stage": "DC after temperature", "energy_kwh": e_dc,
         "loss_label": f"thermal: {100*(e_dc_no_temp-e_dc)/e_dc_no_temp:.1f}% (cell > 25C)"},
        {"stage": "DC after array losses", "energy_kwh": e_dc_net,
         "loss_label": f"mismatch+wiring+LID: {dc_loss_pct:.1f}%"},
        {"stage": "AC after inverter + availability", "energy_kwh": e_ac,
         "loss_label": "inverter + availability"},
    ])
    attribution["pct_of_poa_ideal"] = 100.0 * attribution["energy_kwh"] / e_poa_ideal

    # Monthly profile.
    df = pd.DataFrame({
        "pac": pac, "poa": effective_poa,
        "temp_cell": temp_cell, "temp_air": data["temp_air"],
        "pdc": pdc, "pdc_no_temp": pdc_no_temp,
    })
    monthly = pd.DataFrame({
        "e_ac_kwh": df["pac"].resample("ME").sum() / 1000.0,
        "poa_kwh_m2": df["poa"].resample("ME").sum() / 1000.0,
        "mean_temp_cell_c": df["temp_cell"].resample("ME").mean(),
        "mean_temp_air_c": df["temp_air"].resample("ME").mean(),
    })
    monthly["temp_loss_pct"] = 100.0 * (
        1.0 - df["pdc"].resample("ME").sum() / df["pdc_no_temp"].resample("ME").sum())
    monthly.index = monthly.index.month

    return SimResult(
        scenario=sc, ghi_kwh_m2=ghi_kwh_m2, poa_kwh_m2=poa_kwh_m2,
        e_dc_kwh=e_dc, e_ac_kwh=e_ac, pr=pr, eta_system=eta_system,
        specific_yield=specific_yield, monthly=monthly, attribution=attribution,
        hourly_ac_w=pac,
    )
