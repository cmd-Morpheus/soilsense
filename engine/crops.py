"""Crop table and rule-based crop suitability scoring.

ALL NUMBERS ARE ILLUSTRATIVE. Before the demo, check pH ranges, doses and
sowing months against your state agricultural university's package of practices.
dose = recommended N : P2O5 : K2O in kg/ha.
urea_splits = (growth stage, fraction of the urea applied then).
"""

MAX_EC = {"sensitive": 1.0, "moderate": 2.0, "tolerant": 4.0}  # soil-test EC, dS/m

CROPS = [
    {"name": "Rice (paddy)", "seasons": ["Kharif"], "sowing": "Jun–Jul (transplant Jul)",
     "harvest": "Oct–Nov", "duration": "120–140 days", "ph_range": (5.0, 7.5),
     "salt_tolerance": "moderate", "dose": (80, 40, 40), "legume": False,
     "urea_splits": [("At transplanting", 0.50),
                     ("Active tillering (~3 weeks after transplanting)", 0.25),
                     ("Panicle initiation (~6 weeks after transplanting)", 0.25)]},
    {"name": "Wheat", "seasons": ["Rabi"], "sowing": "Nov", "harvest": "Mar–Apr",
     "duration": "110–130 days", "ph_range": (6.0, 7.5), "salt_tolerance": "tolerant",
     "dose": (100, 50, 50), "legume": False,
     "urea_splits": [("At sowing", 0.50), ("First irrigation, crown-root stage (~3 weeks)", 0.50)]},
    {"name": "Potato", "seasons": ["Rabi"], "sowing": "Nov", "harvest": "Feb–Mar",
     "duration": "90–110 days", "ph_range": (5.0, 6.5), "salt_tolerance": "sensitive",
     "dose": (150, 100, 100), "legume": False,
     "urea_splits": [("At planting", 0.50), ("At earthing up (~4 weeks)", 0.50)]},
    {"name": "Mustard", "seasons": ["Rabi"], "sowing": "Oct–Nov", "harvest": "Feb",
     "duration": "100–120 days", "ph_range": (6.0, 7.5), "salt_tolerance": "tolerant",
     "dose": (80, 40, 40), "legume": False,
     "urea_splits": [("At sowing", 0.50), ("First irrigation (~3–4 weeks)", 0.50)]},
    {"name": "Lentil (masoor)", "seasons": ["Rabi"], "sowing": "Oct–Nov", "harvest": "Feb–Mar",
     "duration": "110–120 days", "ph_range": (6.0, 7.5), "salt_tolerance": "sensitive",
     "dose": (20, 40, 20), "legume": True, "urea_splits": [("At sowing", 1.0)]},
    {"name": "Green gram (moong)", "seasons": ["Zaid", "Kharif"], "sowing": "Mar–Apr (Zaid) / Jul (Kharif)",
     "harvest": "May–Jun / Sep", "duration": "60–70 days", "ph_range": (6.2, 7.2),
     "salt_tolerance": "sensitive", "dose": (20, 40, 20), "legume": True,
     "urea_splits": [("At sowing", 1.0)]},
    {"name": "Maize", "seasons": ["Kharif", "Rabi"], "sowing": "Jun–Jul / Oct–Nov",
     "harvest": "Sep–Oct / Feb–Mar", "duration": "90–120 days", "ph_range": (5.5, 7.5),
     "salt_tolerance": "moderate", "dose": (120, 60, 60), "legume": False,
     "urea_splits": [("At sowing", 1 / 3), ("Knee-high stage (~4 weeks)", 1 / 3),
                     ("Before tasselling (~7 weeks)", 1 / 3)]},
    {"name": "Groundnut", "seasons": ["Kharif", "Zaid"], "sowing": "Jun–Jul / Jan–Feb",
     "harvest": "Oct / May", "duration": "100–120 days", "ph_range": (6.0, 7.0),
     "salt_tolerance": "moderate", "dose": (20, 40, 40), "legume": True,
     "urea_splits": [("At sowing", 1.0)]},
    {"name": "Jute", "seasons": ["Zaid"], "sowing": "Mar–May (pre-kharif)", "harvest": "Jul–Aug",
     "duration": "110–120 days", "ph_range": (5.5, 7.5), "salt_tolerance": "moderate",
     "dose": (40, 20, 20), "legume": False,
     "urea_splits": [("At sowing", 0.50), ("~4 weeks after sowing, after weeding", 0.50)]},
]


def get_crop(name):
    for crop in CROPS:
        if crop["name"] == name:
            return crop
    raise KeyError(f"Unknown crop: {name}")


def score_crop(crop, soil, ratings):
    """Return (score, reasons) or (None, reason_excluded) if the crop clashes with the soil."""
    ph, ec = soil["ph"], soil["ec"]
    ph_min, ph_max = crop["ph_range"]
    max_ec = MAX_EC[crop["salt_tolerance"]]

    if ec > max_ec:
        return None, f"too salty (EC {ec:g} > {max_ec:g} dS/m limit for a salt-{crop['salt_tolerance']} crop)"
    if ph < ph_min - 0.5 or ph > ph_max + 0.5:
        return None, f"pH {ph:g} is far outside its range ({ph_min}–{ph_max})"

    score, reasons = 100, []
    if ph_min <= ph <= ph_max:
        reasons.append("pH suits it")
    else:
        score -= 25
        reasons.append("pH slightly outside its ideal range")
    if ec > 0.75 * max_ec:
        score -= 10
        reasons.append("salinity close to its tolerance limit")

    n_dose, p_dose, k_dose = crop["dose"]
    if ratings["n"] == "Low":
        if crop["legume"]:
            score += 15
            reasons.append("legume, fixes its own nitrogen")
        elif n_dose >= 100:
            score -= 15
            reasons.append("needs a lot of nitrogen, which is low")
    if ratings["oc"] == "Low" and crop["legume"]:
        score += 5
    if ratings["p"] == "Low" and p_dose >= 60:
        score -= 10
        reasons.append("heavy phosphorus need, which is low")
    if ratings["k"] == "Low" and k_dose >= 60:
        score -= 10
        reasons.append("heavy potassium need, which is low")
    return score, reasons


def recommend_crops(soil, ratings, season=None, top_n=5):
    """Return (ranked, excluded). ranked: best first, each {'crop', 'score', 'reasons'}."""
    ranked, excluded = [], []
    for crop in CROPS:
        if season and season not in crop["seasons"]:
            continue
        score, info = score_crop(crop, soil, ratings)
        if score is None:
            excluded.append({"crop": crop, "reason": info})
        else:
            ranked.append({"crop": crop, "score": score, "reasons": info})
    ranked.sort(key=lambda r: (-r["score"], r["crop"]["name"]))
    return ranked[:top_n], excluded
