"""Builds the downloadable one-page text prescription."""

from datetime import date

from .ratings import NUTRIENT_LIMITS

DISCLAIMER = ("SoilSense is a student prototype. Advice follows general soil-test guidelines; "
              "confirm doses with your local KVK or soil testing lab.")


def build_prescription_text(result):
    soil, ratings, plan = result["soil"], result["ratings"], result["plan"]
    lines = ["SOILSENSE SOIL PRESCRIPTION", f"Date: {date.today():%d %b %Y}", ""]
    if result.get("estimate"):
        est = result["estimate"]
        lines += [f"ESTIMATED, NOT TESTED: based on {est['count']} reports from {est['basis']} "
                  f"({est['confidence']} confidence). Please get a soil test.", ""]

    lines += ["1. SOIL HEALTH", result["brief"], ""]
    lines.append(f"   pH: {soil['ph']:g} ({ratings['ph']})")
    lines.append(f"   EC: {soil['ec']:g} dS/m ({ratings['ec']})")
    for key, (label, unit, _, _) in NUTRIENT_LIMITS.items():
        value = f"{soil[key]:.2f}" if key == "oc" else f"{soil[key]:.0f}"
        lines.append(f"   {label}: {value} {unit} ({ratings[key]})")
    lines.append("")

    lines.append("2. RECOMMENDED CROPS")
    if result["ranked"]:
        for i, r in enumerate(result["ranked"], 1):
            c = r["crop"]
            lines.append(f"   {i}. {c['name']}: sow {c['sowing']}, harvest {c['harvest']} "
                         f"({'; '.join(r['reasons'])})")
    else:
        lines.append("   No crop in our table suits this soil and season without reclamation.")
    lines.append("")

    if plan:
        lines.append(f"3. FERTILIZER PLAN for {plan['crop']}, {plan['area_acres']:g} acre(s)")
        for step in plan["schedule"]:
            lines.append(f"   {step['stage']}: " + "; ".join(step["items"]))
        for note in plan["notes"]:
            lines.append(f"   Note: {note}")
        lines.append("")

    if result["amendments"]:
        lines.append("4. SOIL AMENDMENTS")
        for title, text in result["amendments"]:
            lines.append(f"   {title}: {text}")
        lines.append("")

    lines.append("5. REBUILD YOUR SOIL")
    for title, text in result["restoration"]:
        lines.append(f"   {title}: {text}")
    lines += ["", DISCLAIMER]
    return "\n".join(lines)
