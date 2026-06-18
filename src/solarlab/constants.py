"""Physical constants, cited loss budgets, and reference efficiency limits.

Every empirical number in the toolkit that is *not* computed from first
principles lives here with a one-line source, so the report's assumptions are
auditable in a single file.
"""

from __future__ import annotations

import scipy.constants as _sc

# --- Fundamental physical constants (SI) -----------------------------------
Q = _sc.elementary_charge          # C
K_B = _sc.Boltzmann                # J/K
H = _sc.Planck                     # J*s
C = _sc.speed_of_light             # m/s

# Photon energy <-> wavelength conversion factor: E[eV] = EV_NM / lambda[nm].
# EV_NM = h*c/q expressed in eV*nm.  (CODATA: 1239.841984 eV*nm)
EV_NM = H * C / Q * 1e9            # ~1239.84198 eV*nm

# --- Reference operating conditions ----------------------------------------
T_CELL = 300.0                     # K, detailed-balance reference cell temperature
STC_IRRADIANCE = 1000.0            # W/m^2, standard test condition irradiance
STC_TEMP_C = 25.0                  # deg C, STC cell temperature

# --- Material bandgaps (eV) ------------------------------------------------
# Source: S. M. Sze, "Physics of Semiconductor Devices", and Green et al.
SI_EG_EV = 1.12                    # crystalline silicon (300 K)
GAAS_EG_EV = 1.42                  # gallium arsenide
CDTE_EG_EV = 1.50                  # cadmium telluride
PEROVSKITE_EG_EV = 1.55            # typical methylammonium lead halide perovskite
PYRITE_EG_EV = 0.95                # iron pyrite FeS2 ("fool's gold")

# External radiative efficiency (ERE / external luminescence yield): the fraction
# of recombination that is radiative. ERE = 1 is the ideal Shockley-Queisser
# cell; lower ERE means non-radiative recombination steals voltage via
# qVoc = qVoc_radiative + kT*ln(ERE).
# Sources: Green 2012 (Prog. Photovolt.) for the ERE framework; GaAs record cells
# reach ERE ~0.2-0.3; silicon ~1e-3; iron pyrite is notoriously ~1e-6-1e-8 due to
# surface states / sulfur vacancies / Fermi-level pinning.
ERE_GAAS_RECORD = 0.23
ERE_SILICON = 1e-3
PYRITE_ERE_TODAY = 1e-9            # observed pyrite cells: Voc collapses to ~0.2 V
PYRITE_ERE_PASSIVATED = 1e-2       # hypothetical: surface defects largely cured

# --- Reference efficiency limits & records (percent) -----------------------
# Practical single-junction silicon limit including intrinsic Auger
# recombination.  Source: Richter, Hermle & Glunz, "Reassessment of the
# Limiting Efficiency for Crystalline Silicon Solar Cells", IEEE J.
# Photovoltaics 3(4), 2013, doi:10.1109/JPHOTOV.2013.2270351.
RICHTER_SI_LIMIT_PCT = 29.4

# Best laboratory silicon cell. Source: NREL Best Research-Cell Efficiency
# Chart (LONGi HIBC, 2025), https://www.nrel.gov/pv/cell-efficiency.html
SI_LAB_RECORD_PCT = 27.81

# Best mainstream commercial silicon cell in volume production (TOPCon class),
# Source: ITRPV 2024 / manufacturer datasheets, ~24% cell.
SI_COMMERCIAL_CELL_PCT = 24.0

# Cell-to-module silicon module at STC for the reference rooftop panel
# (PERC class, e.g. LONGi Hi-MO 5 datasheet).  Used as the module STC rung.
SI_MODULE_STC_PCT = 20.7

# Data currency note surfaced in the report (records move; ranges are tested,
# not exact values).
DATA_AS_OF = "2026-06"

# --- System DC loss budget (PVWatts v5 defaults) ---------------------------
# Source: A. P. Dobos, "PVWatts Version 5 Manual", NREL/TP-6A20-62641, 2014.
# These are the percent losses applied multiplicatively to DC energy.
# `soiling` is set to 0.0 here because the simulation applies soiling directly
# to plane-of-array irradiance upstream (so it correctly interacts with the
# temperature model); `shading`/`snow` are 0 for an unshaded reference roof.
PVWATTS_LOSSES = dict(
    soiling=0.0,
    shading=0.0,
    snow=0.0,
    mismatch=2.0,
    wiring=2.0,
    connections=0.5,
    lid=1.5,
    nameplate_rating=0.0,
    age=0.0,
    availability=3.0,
)

# Soiling applied to plane-of-array irradiance (annual-average), separate from
# the DC budget above.  Source: typical value, Dobos 2014.
SOILING_FRAC = 0.02

# --- Reference site (for the offline-reproducible simulation) --------------
# Greensboro, NC TMY3 ships with pvlib (USAF 723170).  Tilt defaults to the
# site latitude, the standard rule of thumb for maximising annual yield.
SITE_NAME = "Greensboro, NC (TMY3 723170)"
SITE_LATITUDE = 36.1
SITE_LONGITUDE = -79.95
SITE_ALTITUDE = 277.0
SITE_TZ = "Etc/GMT+5"

# --- End-of-life / circularity parameters ----------------------------------
# Module mass per unit capacity, used to convert retired GW into recoverable
# tonnage for validation against IRENA's ~78 Mt-by-2050 projection.
# A framed c-Si module is ~12 kg/m^2 and ~5-6 m^2/kW -> ~65 kg/kW = 65 t/MW.
# Source: IRENA/IEA-PVPS "End-of-Life Management: Solar PV Panels" (2016).
MODULE_MASS_T_PER_GW = 65000.0

# Weibull module-survival parameters S(a) = exp(-(a/scale)^shape).
# "regular loss" (no early failures) vs "early loss" (infant + mid-life
# failures).  Both assume a ~30-year nominal lifetime.
# Source: IRENA/IEA-PVPS (2016), End-of-Life Management: Solar PV Panels.
PV_LIFETIME_WEIBULL = {
    "regular": (5.3759, 30.0),   # (shape, scale)
    "early": (2.4928, 30.0),
}

