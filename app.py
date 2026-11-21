"""SoilSense: an AI soil health assistant (prototype).

Run with:  streamlit run app.py
"""

from datetime import date

import pandas as pd
import streamlit as st

import db
from engine import (
    CROPS, NUTRIENT_LIMITS, analyze_report, fertilizer_plan, get_crop, make_brief, rate_soil,
    recommend_crops, restoration_advice, soil_amendments, to_elemental_k, to_elemental_p, validate_soil,
)

MODE_REPORT = "Yes, I'll enter my report values"
MODE_AREA = "No, estimate my soil from my area"

ICONS = {
    "Low": "🔴", "Medium": "🟡", "High": "🟢",
    "Strongly acidic": "🔴", "Acidic": "🟡", "Neutral": "🟢", "Alkaline": "🟡", "Strongly alkaline": "🔴",
    "Normal": "🟢", "Caution": "🟡", "Harmful": "🔴",
}
PARAMETERS = [("ph", "pH", ""), ("ec", "EC", "dS/m")] + [
    (key, label.split(" (")[0], unit) for key, (label, unit, _, _) in NUTRIENT_LIMITS.items()
]

st.set_page_config(page_title="SoilSense", page_icon="🌱", layout="wide")
db.init_db()


def fmt(value):
    return f"{value:,.2f}".rstrip("0").rstrip(".")


# ---------------------------------------------------------------- input screens

def manual_entry_form():
    with st.form("manual_entry"):
        st.subheader("Enter the values from your soil report")
        c1, c2, c3 = st.columns(3)
        ph = c1.number_input("pH", 3.0, 11.0, 6.5, 0.1)
        ec = c1.number_input("EC (dS/m)", 0.0, 20.0, 0.3, 0.05)
        oc = c1.number_input("Organic carbon (%)", 0.0, 5.0, 0.50, 0.01)
        n = c2.number_input("Available nitrogen, N (kg/ha)", 0.0, 2000.0, 250.0, 5.0)
        zn = c2.number_input("Zinc (ppm), optional", min_value=0.0, max_value=50.0, value=None,
                             step=0.1, placeholder="Leave blank if not tested")
        p = c3.number_input("Available phosphorus (kg/ha)", 0.0, 1200.0, 15.0, 1.0)
        p_unit = c3.radio("Phosphorus is reported as", ["P", "P2O5"], horizontal=True)
        k = c3.number_input("Available potassium (kg/ha)", 0.0, 3600.0, 150.0, 5.0)
        k_unit = c3.radio("Potassium is reported as", ["K", "K2O"], horizontal=True)

        st.markdown("**Where is this field?** (needed only if you want to save the report)")
        c4, c5, c6 = st.columns(3)
        district = c4.text_input("District")
        village = c5.text_input("Village")
        sample_date = c6.date_input("Sample date", value=date.today(), max_value=date.today())
        consent = st.checkbox("Add these soil values (never my name or phone) to the SoilSense database "
                              "to improve estimates for nearby farmers")
        submitted = st.form_submit_button("Analyse my soil", type="primary")

    if not submitted:
        return
    soil = {"ph": ph, "ec": ec, "oc": oc, "n": n, "zn": zn,
            "p": to_elemental_p(p, p_unit), "k": to_elemental_k(k, k_unit)}
    errors = validate_soil(soil)
    if errors:
        for error in errors:
            st.error(error)
        return
    st.session_state.update(soil=soil, estimate=None, mode=MODE_REPORT)

    if consent:
        if district.strip() and village.strip():
            status, message = db.save_report(soil, district, village, sample_date.isoformat(), source="manual")
            (st.success if status == "saved" else st.info)(message)
        else:
            st.warning("Add a district and village if you want the report saved.")


def location_estimate_form():
    locations = db.get_locations()
    if not locations:
        st.warning("The database is empty. Run `python make_demo_data.py` once, then refresh this page.")
        return
    st.subheader("Pick your location")
    c1, c2 = st.columns(2)
    district = c1.selectbox("District", sorted(locations))
    village = c2.selectbox("Village", locations[district])
    if st.button("Estimate my soil", type="primary"):
        estimate = db.estimate_soil(district, village)
        if estimate is None:
            st.error("No reports found for this district yet.")
            return
        st.session_state.update(soil=estimate["soil"], estimate=estimate, mode=MODE_AREA)


# ---------------------------------------------------------------- results

def show_results(soil, estimate, season, area_acres):
    st.divider()
    if estimate:
        st.warning(f"⚠️ **Estimated, not tested.** Based on {estimate['count']} reports from "
                   f"{estimate['basis']} ({estimate['confidence']} confidence). "
                   "Get a proper soil test for exact advice.")

    ratings = rate_soil(soil)

    st.header("1. Soil health brief")
    st.info(make_brief(soil, ratings))
    cols = st.columns(len(PARAMETERS))
    for col, (key, label, unit) in zip(cols, PARAMETERS):
        col.metric(label, f"{fmt(soil[key])} {unit}".strip())
        col.markdown(f"{ICONS[ratings[key]]} {ratings[key]}")
    if soil.get("zn") is not None:
        st.caption(f"Zinc: {fmt(soil['zn'])} ppm")

    st.header("2. Crops that suit your soil")
    ranked, excluded = recommend_crops(soil, ratings, season)
    if ranked:
        st.dataframe(pd.DataFrame([{
            "Crop": r["crop"]["name"],
            "Season": ", ".join(r["crop"]["seasons"]),
            "Sowing": r["crop"]["sowing"],
            "Harvest": r["crop"]["harvest"],
            "Duration": r["crop"]["duration"],
            "Match score": r["score"],
            "Why": "; ".join(r["reasons"]),
        } for r in ranked]), hide_index=True)
    else:
        st.error("No crop in our table suits this soil and season without reclaiming the soil first.")
    if excluded:
        with st.expander(f"Crops ruled out for this soil ({len(excluded)})"):
            for e in excluded:
                st.markdown(f"- **{e['crop']['name']}**: {e['reason']}")

    st.header("3. Fertilizer plan")
    names = [c["name"] for c in CROPS]
    default = names.index(ranked[0]["crop"]["name"]) if ranked else 0
    crop_name = st.selectbox("Show the fertilizer plan for", names, index=default)
    if crop_name not in {r["crop"]["name"] for r in ranked}:
        st.warning(f"{crop_name} is not among the best matches for this soil and season.")
    plan = fertilizer_plan(get_crop(crop_name), ratings, area_acres)
    dose = plan["dose_per_ha"]
    st.caption(f"Nutrient dose after soil-test adjustment: N {dose['N']:.0f} : P2O5 {dose['P2O5']:.0f} : "
               f"K2O {dose['K2O']:.0f} kg/ha, for {fmt(area_acres)} acre(s)")
    st.dataframe(pd.DataFrame([{
        "Fertilizer": p["name"],
        "Total for your field": p["amount_text"],
        "Bag size": f"{p['bag_kg']} kg",
    } for p in plan["products"]]), hide_index=True)
    st.markdown("**When to apply**")
    for step in plan["schedule"]:
        st.markdown(f"- **{step['stage']}:** " + "; ".join(step["items"]))
    for note in plan["notes"]:
        st.caption(f"💡 {note}")

    amendments = soil_amendments(soil, ratings, area_acres)
    if amendments:
        st.subheader("Soil amendments")
        for title, text in amendments:
            st.markdown(f"**{title}:** {text}")

    st.header("4. Rebuild your soil")
    for title, text in restoration_advice(ratings):
        st.markdown(f"🌿 **{title}:** {text}")

    result = analyze_report(soil, season, area_acres, crop_name=crop_name, estimate=estimate)
    st.download_button("⬇️ Download prescription", result["text"],
                       file_name="soilsense_prescription.txt", mime="text/plain")
    st.caption("SoilSense is a student prototype. Confirm doses with your local KVK or soil testing lab.")


# ---------------------------------------------------------------- page layout

st.title("🌱 SoilSense")
st.markdown("Your soil report, explained: what's wrong, what to grow, and which fertilizer to use.")

with st.sidebar:
    st.header("Your field")
    season_choice = st.selectbox("Season", ["Any", "Kharif", "Rabi", "Zaid"])
    area = st.number_input("Field size (acres)", min_value=0.1, max_value=100.0, value=1.0, step=0.5)
    st.caption("1 acre = 0.405 hectare")
season = None if season_choice == "Any" else season_choice

tab_analyse, tab_database = st.tabs(["Analyse soil", "Soil database"])

with tab_analyse:
    mode = st.radio("Do you have a soil test report?", [MODE_REPORT, MODE_AREA], horizontal=True)
    if mode == MODE_REPORT:
        manual_entry_form()
    else:
        location_estimate_form()
    if st.session_state.get("soil") and st.session_state.get("mode") == mode:
        show_results(st.session_state["soil"], st.session_state["estimate"], season, area)

with tab_database:
    reports = db.load_reports()
    c1, c2 = st.columns(2)
    c1.metric("Reports in database", len(reports))
    c2.metric("Added by farmers", int((reports["source"] == "manual").sum()) if not reports.empty else 0)
    st.caption("Every confirmed report is validated, checked for duplicates, tagged with its source and "
               "added here. Records tagged 'demo' are synthetic data for the prototype.")
    if not reports.empty:
        st.dataframe(reports, hide_index=True)
