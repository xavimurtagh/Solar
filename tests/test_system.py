"""Tests for the pvlib rooftop simulation."""


def test_weather_is_a_full_year(weather):
    data, meta = weather
    assert len(data) == 8760
    ghi_kwh = data["ghi"].sum() / 1000.0
    assert 1250 <= ghi_kwh <= 1750            # Greensboro ~1500 kWh/m^2


def test_reference_system_sane(base_sim):
    assert 1100 <= base_sim.specific_yield <= 1600   # kWh/kWp
    assert 0.70 <= base_sim.pr <= 0.88               # performance ratio
    assert base_sim.e_ac_kwh < base_sim.e_dc_kwh     # inverter + losses
    assert base_sim.eta_system < base_sim.scenario.module_eff


def test_monthly_consistency(base_sim):
    m = base_sim.monthly
    assert len(m) == 12
    assert abs(m["e_ac_kwh"].sum() - base_sim.e_ac_kwh) < 0.01 * base_sim.e_ac_kwh
    assert m.loc[6, "poa_kwh_m2"] > m.loc[12, "poa_kwh_m2"]   # summer > winter


def test_temperature_loss_in_range(base_sim):
    m = base_sim.monthly
    # Annual average temperature loss should be a few percent, larger in summer.
    annual_temp_loss = (m["temp_loss_pct"] * m["poa_kwh_m2"]).sum() / m["poa_kwh_m2"].sum()
    assert 1.0 <= annual_temp_loss <= 8.0
    assert m.loc[7, "temp_loss_pct"] > m.loc[1, "temp_loss_pct"]   # July hotter than Jan


def test_attribution_monotonic(base_sim):
    energies = base_sim.attribution["energy_kwh"].values
    assert all(b < a for a, b in zip(energies, energies[1:]))   # strictly decreasing
    assert abs(base_sim.attribution.iloc[-1]["energy_kwh"] - base_sim.e_ac_kwh) < 1.0
