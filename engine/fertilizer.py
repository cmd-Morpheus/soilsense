"""Fertilizer plan: what, how much (in bags), and when.

Method (from the project plan, F7):
1. Start from the crop's recommended N : P2O5 : K2O dose (kg/ha).
2. Adjust by soil test rating: Low +25 %, Medium unchanged, High -25 %.
   (Replace with STCR equations if your state has them for the crop.)
3. Convert nutrients to products: DAP for P2O5 (its N is counted),
   urea for the remaining N, MOP for K2O.
4. Scale to the field size and split urea across growth stages.
"""

HA_PER_ACRE = 0.4047
ADJUSTMENT = {"Low": 1.25, "Medium": 1.0, "High": 0.75}

FERTILIZERS = {
    "DAP": {"N": 0.18, "P2O5": 0.46, "K2O": 0.0, "bag_kg": 50},
    "Urea": {"N": 0.46, "P2O5": 0.0, "K2O": 0.0, "bag_kg": 45},
    "MOP": {"N": 0.0, "P2O5": 0.0, "K2O": 0.60, "bag_kg": 50},
}


def adjusted_dose(crop, ratings):
    n, p2o5, k2o = crop["dose"]
    return {
        "N": n * ADJUSTMENT[ratings["n"]],
        "P2O5": p2o5 * ADJUSTMENT[ratings["p"]],
        "K2O": k2o * ADJUSTMENT[ratings["k"]],
    }


def products_per_ha(dose):
    """kg of each fertilizer product per hectare."""
    dap = dose["P2O5"] / FERTILIZERS["DAP"]["P2O5"]
    n_from_dap = dap * FERTILIZERS["DAP"]["N"]
    urea = max(dose["N"] - n_from_dap, 0.0) / FERTILIZERS["Urea"]["N"]
    mop = dose["K2O"] / FERTILIZERS["MOP"]["K2O"]
    return {"DAP": dap, "Urea": urea, "MOP": mop}, n_from_dap


def round_to_half(x):
    return round(x * 2) / 2


def describe_amount(kg, bag_kg):
    """'2 bags (92 kg)' style text a farmer can act on."""
    if kg < 0.5:
        return "none needed"
    if kg / bag_kg < 0.4:
        return f"about {kg:.0f} kg (less than half a bag)"
    bags = round_to_half(kg / bag_kg)
    bag_word = "bag" if bags <= 1 else "bags"
    return f"{bags:g} {bag_word} ({kg:.0f} kg)"


def fertilizer_plan(crop, ratings, area_acres):
    dose = adjusted_dose(crop, ratings)
    per_ha, n_from_dap = products_per_ha(dose)
    area_ha = area_acres * HA_PER_ACRE

    products = []
    for name, kg_ha in per_ha.items():
        kg_field = kg_ha * area_ha
        bag_kg = FERTILIZERS[name]["bag_kg"]
        products.append({
            "name": name, "kg_per_ha": kg_ha, "kg_field": kg_field,
            "bags": round_to_half(kg_field / bag_kg), "bag_kg": bag_kg,
            "amount_text": describe_amount(kg_field, bag_kg),
        })
    kg = {p["name"]: p["kg_field"] for p in products}

    schedule = []
    for i, (stage, fraction) in enumerate(crop["urea_splits"]):
        items = []
        if i == 0:
            for name in ("DAP", "MOP"):
                if kg[name] >= 0.5:
                    items.append(f"{name}: {describe_amount(kg[name], FERTILIZERS[name]['bag_kg'])}")
        urea_now = kg["Urea"] * fraction
        if urea_now >= 0.5:
            items.append(f"Urea: {describe_amount(urea_now, FERTILIZERS['Urea']['bag_kg'])}")
        if items:
            schedule.append({"stage": stage, "items": items})

    notes = []
    if dose["N"] > 0 and kg["Urea"] < 0.5:
        notes.append("DAP alone supplies all the nitrogen this crop needs, so no urea is required.")
    if crop["legume"]:
        notes.append("Treat seed with Rhizobium culture before sowing to boost nitrogen fixation.")
    notes.append("Apply urea when the soil is moist, not just before heavy rain, so less nitrogen is lost.")

    return {
        "crop": crop["name"], "area_acres": area_acres, "dose_per_ha": dose,
        "n_from_dap_per_ha": n_from_dap, "products": products,
        "schedule": schedule, "notes": notes,
    }
