"""Unit tests for the recommendation engine. Run with:  pytest"""

import pytest

from engine import analyze_report, rate_soil, recommend_crops, to_elemental_k, to_elemental_p, validate_soil
from engine.fertilizer import fertilizer_plan
from engine.ratings import rate_ec, rate_nutrient, rate_ph

GOOD_SOIL = {"ph": 6.8, "ec": 0.3, "oc": 0.6, "n": 300, "p": 15, "k": 150, "zn": None}


def test_nitrogen_rating_boundaries():
    assert rate_nutrient(279, 280, 560) == "Low"
    assert rate_nutrient(280, 280, 560) == "Medium"
    assert rate_nutrient(560, 280, 560) == "Medium"
    assert rate_nutrient(561, 280, 560) == "High"


@pytest.mark.parametrize("ph, expected", [
    (5.0, "Strongly acidic"), (6.0, "Acidic"), (7.0, "Neutral"), (8.0, "Alkaline"), (9.0, "Strongly alkaline"),
])
def test_ph_ratings(ph, expected):
    assert rate_ph(ph) == expected


def test_ec_ratings():
    assert rate_ec(0.5) == "Normal"
    assert rate_ec(2.0) == "Caution"
    assert rate_ec(3.5) == "Harmful"


def test_unit_conversion():
    assert to_elemental_p(22.9, "P2O5") == pytest.approx(10.0)
    assert to_elemental_p(10, "P") == 10
    assert to_elemental_k(120, "K2O") == pytest.approx(100.0)


def test_worked_example_from_project_plan():
    """Rice 100:50:50, N low / P medium / K high, 1 acre -> ~1 bag DAP, 2 bags urea, half bag MOP."""
    crop = {"name": "Test rice", "dose": (100, 50, 50), "legume": False,
            "urea_splits": [("Basal", 0.5), ("Tillering", 0.25), ("Panicle initiation", 0.25)]}
    plan = fertilizer_plan(crop, {"n": "Low", "p": "Medium", "k": "High"}, area_acres=1)
    assert plan["dose_per_ha"] == {"N": 125, "P2O5": 50, "K2O": 37.5}
    per_ha = {p["name"]: p["kg_per_ha"] for p in plan["products"]}
    assert per_ha["DAP"] == pytest.approx(108.7, abs=0.1)
    assert per_ha["Urea"] == pytest.approx(229.2, abs=0.2)
    assert per_ha["MOP"] == pytest.approx(62.5, abs=0.1)
    bags = {p["name"]: p["bags"] for p in plan["products"]}
    assert bags == {"DAP": 1.0, "Urea": 2.0, "MOP": 0.5}
    assert "DAP" in plan["schedule"][0]["items"][0]  # DAP goes in at the first stage


def test_no_urea_when_dap_covers_nitrogen():
    crop = {"name": "Test legume", "dose": (15, 50, 20), "legume": True, "urea_splits": [("At sowing", 1.0)]}
    plan = fertilizer_plan(crop, {"n": "Medium", "p": "Medium", "k": "Medium"}, area_acres=1)
    urea = next(p for p in plan["products"] if p["name"] == "Urea")
    assert urea["kg_field"] == 0


def test_saline_soil_rules_out_sensitive_crops():
    soil = dict(GOOD_SOIL, ec=1.5)
    ranked, excluded = recommend_crops(soil, rate_soil(soil))
    ranked_names = {r["crop"]["name"] for r in ranked}
    excluded_names = {e["crop"]["name"] for e in excluded}
    assert "Potato" in excluded_names and "Potato" not in ranked_names
    assert "Wheat" not in excluded_names


def test_low_nitrogen_favours_legumes():
    soil = dict(GOOD_SOIL, n=200)
    ranked, _ = recommend_crops(soil, rate_soil(soil), season="Rabi")
    assert ranked[0]["crop"]["legume"]


def test_season_filter():
    ranked, _ = recommend_crops(GOOD_SOIL, rate_soil(GOOD_SOIL), season="Kharif")
    assert all("Kharif" in r["crop"]["seasons"] for r in ranked)


def test_validation_catches_impossible_values():
    assert validate_soil(GOOD_SOIL) == []
    errors = validate_soil(dict(GOOD_SOIL, ph=15))
    assert len(errors) == 1 and "pH" in errors[0]


def test_full_pipeline_runs():
    result = analyze_report(GOOD_SOIL, season="Rabi", area_acres=2)
    assert result["plan"] is not None
    assert "SOILSENSE SOIL PRESCRIPTION" in result["text"]
