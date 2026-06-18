"""Tests for material intensity, the terawatt ceiling, and substitutions."""

import pytest

from solarlab import materials as M


def test_material_data_cited_and_complete():
    mats = M.load_materials()
    required = {"element", "price_usd_per_kg", "annual_production_tonnes",
                "reserves_tonnes", "crustal_abundance_ppm", "source"}
    assert required <= set(mats.columns)
    assert (mats["source"].astype(str).str.len() >= 10).all()
    assert (mats["annual_production_tonnes"] > 0).all()


def test_bom_cited_and_positive():
    bom = M.load_bom()
    assert (bom["intensity_g_per_kw"] > 0).all()
    assert (bom["source"].astype(str).str.len() >= 8).all()


def test_silver_is_the_silicon_pv_constraint():
    # Today's mainstream silicon cells are silver-limited.
    for tech in ("PERC", "TOPCon"):
        c = M.deployment_ceiling(tech)
        assert c["binding_element"] == "Silver"
        assert 0.5 <= c["tw_per_year"] <= 2.0       # ~1 TW/yr ceiling
        assert c["binding_is_scarce"]


def test_cdte_is_tellurium_limited_and_tiny():
    c = M.deployment_ceiling("CdTe")
    assert c["binding_element"] == "Tellurium"
    assert c["tw_per_year"] < 0.05                  # a few GW/yr only


def test_abundant_absorbers_scale_further():
    # Pyrite (iron + sulfur) and kesterite (CZTS) beat scarce-element cells.
    pyrite = M.deployment_ceiling("Pyrite")["tw_per_year"]
    czts = M.deployment_ceiling("CZTS")["tw_per_year"]
    cdte = M.deployment_ceiling("CdTe")["tw_per_year"]
    assert pyrite > czts > cdte
    assert pyrite > 1.0


def test_silver_to_copper_lifts_ceiling():
    eff = M.substitution_effect("TOPCon", M.SILVER_TO_COPPER)
    assert eff["binding_before"] == "Silver"
    assert eff["binding_after"] != "Silver"          # silver no longer binds
    assert eff["tw_per_year_after"] > eff["tw_per_year_before"]
    assert eff["material_cost_after"] < eff["material_cost_before"]   # copper is cheaper


def test_indium_substitution_helps_heterojunction():
    eff = M.substitution_effect("HJT", M.INDIUM_TO_ZINC)
    assert eff["binding_before"] == "Indium"
    assert eff["ceiling_multiplier"] > 5             # AZO removes the indium wall


def test_material_cost_in_reasonable_range():
    # Silicon cells carry ~10-15 cents/W of raw materials; pyrite far less.
    assert 0.08 <= M.material_cost_per_w("PERC") <= 0.20
    assert M.material_cost_per_w("Pyrite") < M.material_cost_per_w("PERC")
