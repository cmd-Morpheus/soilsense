"""Plain-language fertility brief."""

NAMES = {"oc": "organic carbon", "n": "nitrogen", "p": "phosphorus", "k": "potassium"}

EC_SENTENCES = {
    "Normal": "Salt levels are normal.",
    "Caution": "Salt levels are slightly high, so avoid salt-sensitive crops.",
    "Harmful": "Salt levels are high enough to harm most crops; the soil needs reclaiming first.",
}


def join_words(words):
    if len(words) == 1:
        return words[0]
    return ", ".join(words[:-1]) + " and " + words[-1]


def make_brief(soil, ratings):
    groups = {"Low": [], "Medium": [], "High": []}
    for key in ("n", "oc", "p", "k"):
        groups[ratings[key]].append(NAMES[key])
    parts = [f"{level.lower()} in {join_words(names)}" for level, names in groups.items() if names]
    if len(parts) > 1:
        nutrients = ", ".join(parts[:-1]) + ", and " + parts[-1]
    else:
        nutrients = parts[0]

    sentences = [
        f"Your soil is {nutrients}.",
        f"It is {ratings['ph'].lower()} (pH {soil['ph']:g}).",
        EC_SENTENCES[ratings["ec"]],
    ]
    tips = []
    if ratings["n"] == "Low" or ratings["oc"] == "Low":
        tips.append("adding organic matter and growing a legume this season will help")
    if ratings["ph"] == "Strongly acidic":
        tips.append("liming will make nutrients more available")
    if ratings["ph"] == "Strongly alkaline":
        tips.append("gypsum and better drainage are needed")
    if tips:
        sentences.append(join_words(tips).capitalize() + ".")
    return " ".join(sentences)
