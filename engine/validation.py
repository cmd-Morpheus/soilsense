"""Range checks so impossible values never reach the engine or the database."""

VALID_RANGES = {
    "ph": ("pH", 3.0, 11.0),
    "ec": ("EC", 0.0, 20.0),
    "oc": ("Organic carbon", 0.0, 5.0),
    "n": ("Nitrogen", 0.0, 2000.0),
    "p": ("Phosphorus (as P)", 0.0, 500.0),
    "k": ("Potassium (as K)", 0.0, 3000.0),
    "zn": ("Zinc", 0.0, 50.0),
}
OPTIONAL = {"zn"}


def validate_soil(soil):
    """Return a list of error messages; an empty list means the values are valid."""
    errors = []
    for key, (label, low, high) in VALID_RANGES.items():
        value = soil.get(key)
        if value is None:
            if key not in OPTIONAL:
                errors.append(f"{label} is missing.")
            continue
        if not low <= value <= high:
            errors.append(f"{label} = {value:g} is outside the realistic range {low:g}–{high:g}.")
    return errors
