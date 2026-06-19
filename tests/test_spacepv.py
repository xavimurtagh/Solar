"""Tests for the space-based solar power model (Part X)."""

import numpy as np

from solarlab import spacepv as SP


def test_lcoe_falls_with_launch_cost():
    hi = SP.sbsp_lcoe(2700.0)
    lo = SP.sbsp_lcoe(100.0)
    assert lo < hi
    assert SP.sbsp_curve()["lcoe_usd_mwh"].is_monotonic_increasing


def test_competitive_at_starship_prices():
    # At Starship's $100/kg target SBSP should be in the firm-solar range.
    for params in SP.SCENARIOS.values():
        lcoe = SP.sbsp_lcoe(SP.LAUNCH_STARSHIP_TARGET, params)
        assert 30 <= lcoe <= 130          # Caltech-class $0.03-0.13/kWh


def test_hopeless_at_falcon9_prices():
    # At today's launch costs SBSP is far above terrestrial.
    assert SP.sbsp_lcoe(SP.LAUNCH_FALCON9) > SP.FIRM_TERRESTRIAL_MODERATE


def test_crossover_in_plausible_range():
    # Launch cost to beat high-resource firm solar should be ~$50-500/kg.
    for params in SP.SCENARIOS.values():
        c = SP.crossover_launch_cost(SP.FIRM_TERRESTRIAL_HIGH, params)
        assert 40 <= c <= 1000


def test_lighter_satellite_beats_higher_launch_cost():
    light = SP.SCENARIOS["Optimistic (10 kg/kW)"]
    heavy = SP.SCENARIOS["Conservative (50 kg/kW)"]
    # A lighter satellite tolerates a higher launch price for the same LCOE.
    assert (SP.crossover_launch_cost(SP.FIRM_TERRESTRIAL_HIGH, light)
            > SP.crossover_launch_cost(SP.FIRM_TERRESTRIAL_HIGH, heavy))


def test_capacity_factor_advantage():
    # SBSP's ~95% capacity factor is its structural edge over ~20% terrestrial.
    assert SP.SBSPParams().capacity_factor > 0.9
