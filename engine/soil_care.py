"""Soil amendments (lime, gypsum, organic matter, zinc) and soil-restoring crops."""

from .fertilizer import HA_PER_ACRE

ZN_CRITICAL_PPM = 0.6  # DTPA-extractable zinc; below this is usually rated deficient


def soil_amendments(soil, ratings, area_acres):
    area_ha = area_acres * HA_PER_ACRE
    advice = []
    if ratings["ph"] == "Strongly acidic":
        advice.append(("Lime for acidic soil",
                       "Apply agricultural lime in furrows 2–3 weeks before sowing. The exact amount "
                       "depends on a lime requirement test, so ask your soil testing lab for it."))
    if ratings["ph"] == "Strongly alkaline":
        advice.append(("Gypsum for alkaline / sodic soil",
                       "pH above 8.5 suggests possible sodicity. Apply gypsum based on a gypsum "
                       "requirement test and improve drainage."))
    if ratings["oc"] in ("Low", "Medium"):
        low_t, high_t = 5 * area_ha, 10 * area_ha
        advice.append(("Organic matter",
                       f"Add well-rotted farmyard manure or compost: about {low_t:.1f}–{high_t:.1f} tonnes "
                       "for your field (5–10 t/ha), mixed in before sowing. It improves soil health and "
                       "can let you cut chemical fertilizer slightly."))
    zn = soil.get("zn")
    if zn is not None and zn < ZN_CRITICAL_PPM:
        advice.append(("Zinc deficiency",
                       f"Zinc is low ({zn:g} ppm). Apply zinc sulphate at about 25 kg/ha "
                       f"(~{25 * area_ha:.0f} kg for your field) at sowing. Do not mix it with DAP."))
    if ratings["ec"] in ("Caution", "Harmful"):
        advice.append(("Salinity",
                       "Salt levels are raised. Improve drainage, irrigate with good-quality water, and "
                       "avoid salt-sensitive crops like potato, lentil and moong."))
    return advice


def restoration_advice(ratings):
    advice = []
    if ratings["n"] == "Low":
        advice.append(("Grow a legume",
                       "Moong, urad, cowpea, lentil or chickpea fix nitrogen from the air and leave "
                       "some in the soil for the next crop."))
    if ratings["oc"] == "Low":
        advice.append(("Green manure",
                       "Grow dhaincha or sunhemp for about 45 days and plough it in before flowering. "
                       "Keep crop residue in the field instead of burning it."))
    if ratings["p"] == "Low":
        advice.append(("Phosphorus helpers",
                       "Use phosphate-solubilising bacteria (PSB) biofertilizer with compost to make "
                       "soil phosphorus more available."))
    if ratings["k"] == "Low":
        advice.append(("Return crop residue",
                       "Straw and stalks hold a lot of potassium; incorporating them rebuilds soil K over time."))
    advice.append(("Rotate crops",
                   "Avoid growing cereals season after season. A cereal–legume or cereal–oilseed "
                   "rotation balances nutrient use and breaks pest cycles."))
    return advice
