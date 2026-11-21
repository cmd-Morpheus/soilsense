# 🌱 SoilSense

An AI soil health assistant that turns a soil test report into clear farming advice:
a fertility brief, suitable crops with sowing seasons, a fertilizer plan in bags with timing,
soil amendments, and soil-restoring crops. Farmers without a report get an estimate from
nearby reports in the database.

Course project for **Soil Technology**. This is a working prototype, not a deployed product.

## Run it

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1          # Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
python make_demo_data.py            # first time only: fills the demo database
streamlit run app.py                # opens http://localhost:8501
pytest                              # runs the unit tests
```

## How it works

| Step | File |
|---|---|
| Rate each parameter Low / Medium / High | `engine/ratings.py` |
| Reject impossible values (e.g. pH 15) | `engine/validation.py` |
| Score and rank crops (pH, salinity, nutrient fit, season) | `engine/crops.py` |
| Adjust nutrient dose by soil test, convert to DAP / urea / MOP bags, split by growth stage | `engine/fertilizer.py` |
| Lime, gypsum, organic matter, zinc; legumes and green manure | `engine/soil_care.py` |
| Plain-language brief and downloadable prescription | `engine/brief.py`, `engine/report.py` |
| SQLite database: validation, duplicate check, source tag, location estimate | `db.py` |
| User interface | `app.py` |

Design principle: **agronomy by rules.** Every recommendation comes from published soil-test
guidelines encoded as rules, so each piece of advice can be explained and checked.

## Important limitations

- **Demo data:** the location fallback runs on synthetic records from `make_demo_data.py`
  (tagged `demo`). They are not real soil tests and must be replaced with Soil Health Card data.
- **Thresholds and doses:** rating limits, crop pH ranges, doses and sowing months are typical
  values. Verify them against the state soil testing lab and the state agricultural university's
  package of practices.
- **Dose adjustment:** uses the simple ±25 % rule; STCR equations would be more precise.
- No OCR, ML soil estimation, accounts, multilingual output or deployment yet (see future scope in the report).
