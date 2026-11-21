"""Soil test ratings: turns raw values into Low / Medium / High.

Thresholds are commonly used Indian soil-test rating limits.
CONFIRM them against your state soil testing lab before the final demo.
P and K are handled internally as elemental P and K (kg/ha).
"""

P2O5_PER_P = 2.29  # 1 kg P  = 2.29 kg P2O5
K2O_PER_K = 1.20   # 1 kg K  = 1.20 kg K2O

# key: (label, unit, low if below this, high if above this)
NUTRIENT_LIMITS = {
    "oc": ("Organic carbon", "%", 0.50, 0.75),
    "n": ("Available nitrogen (N)", "kg/ha", 280, 560),
    "p": ("Available phosphorus (P)", "kg/ha", 10, 25),
    "k": ("Available potassium (K)", "kg/ha", 110, 280),
}


def rate_nutrient(value, low_below, high_above):
    if value < low_below:
        return "Low"
    if value <= high_above:
        return "Medium"
    return "High"


def rate_ph(ph):
    if ph < 5.5:
        return "Strongly acidic"
    if ph < 6.5:
        return "Acidic"
    if ph <= 7.5:
        return "Neutral"
    if ph <= 8.5:
        return "Alkaline"
    return "Strongly alkaline"


def rate_ec(ec):
    if ec < 1.0:
        return "Normal"
    if ec <= 3.0:
        return "Caution"
    return "Harmful"


def rate_soil(soil):
    """soil: dict with keys n, p, k, oc, ph, ec (P and K as elemental kg/ha)."""
    ratings = {
        key: rate_nutrient(soil[key], low, high)
        for key, (_, _, low, high) in NUTRIENT_LIMITS.items()
    }
    ratings["ph"] = rate_ph(soil["ph"])
    ratings["ec"] = rate_ec(soil["ec"])
    return ratings


def to_elemental_p(value, unit):
    """Convert P2O5 to P if the report gives phosphorus as P2O5."""
    return value / P2O5_PER_P if unit == "P2O5" else value


def to_elemental_k(value, unit):
    """Convert K2O to K if the report gives potassium as K2O."""
    return value / K2O_PER_K if unit == "K2O" else value
