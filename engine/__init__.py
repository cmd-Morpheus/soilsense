"""SoilSense recommendation engine: pure Python rules, no UI code."""

from .brief import make_brief
from .crops import CROPS, get_crop, recommend_crops
from .fertilizer import fertilizer_plan
from .ratings import NUTRIENT_LIMITS, rate_soil, to_elemental_k, to_elemental_p
from .report import build_prescription_text
from .soil_care import restoration_advice, soil_amendments
from .validation import validate_soil


def analyze_report(soil, season=None, area_acres=1.0, crop_name=None, estimate=None):
    """Run the full pipeline. If crop_name is None, the plan is for the top-ranked crop."""
    ratings = rate_soil(soil)
    ranked, excluded = recommend_crops(soil, ratings, season)
    if crop_name:
        crop = get_crop(crop_name)
    else:
        crop = ranked[0]["crop"] if ranked else None
    result = {
        "soil": soil,
        "estimate": estimate,
        "ratings": ratings,
        "brief": make_brief(soil, ratings),
        "ranked": ranked,
        "excluded": excluded,
        "plan": fertilizer_plan(crop, ratings, area_acres) if crop else None,
        "amendments": soil_amendments(soil, ratings, area_acres),
        "restoration": restoration_advice(ratings),
    }
    result["text"] = build_prescription_text(result)
    return result


__all__ = [
    "CROPS", "NUTRIENT_LIMITS", "analyze_report", "build_prescription_text", "fertilizer_plan",
    "get_crop", "make_brief", "rate_soil", "recommend_crops", "restoration_advice",
    "soil_amendments", "to_elemental_k", "to_elemental_p", "validate_soil",
]
