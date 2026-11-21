"""SQLite storage for soil reports (the self-growing database, feature F3).

Only location and soil values are stored: no names or phone numbers.
All queries are parameterised (no string-built SQL).
"""

import hashlib
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path

import pandas as pd

from engine import validate_soil

DEFAULT_DB = Path(__file__).resolve().parent / "data" / "soilsense.db"
SOIL_FIELDS = ("n", "p", "k", "oc", "ph", "ec", "zn")

SCHEMA = """
CREATE TABLE IF NOT EXISTS soil_reports (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    district    TEXT NOT NULL,
    village     TEXT NOT NULL,
    sample_date TEXT NOT NULL,
    n REAL NOT NULL, p REAL NOT NULL, k REAL NOT NULL,
    oc REAL NOT NULL, ph REAL NOT NULL, ec REAL NOT NULL,
    zn REAL,
    source      TEXT NOT NULL,          -- 'manual', 'demo', later 'official' / 'ocr'
    fingerprint TEXT NOT NULL UNIQUE,   -- blocks the same report being saved twice
    created_at  TEXT NOT NULL
)
"""


def _connect(db_path):
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(db_path)


def init_db(db_path=DEFAULT_DB):
    with closing(_connect(db_path)) as conn:
        with conn:
            conn.execute(SCHEMA)


def _clean_name(text):
    return " ".join(text.split()).title()


def _fingerprint(district, village, sample_date, soil):
    values = "|".join(f"{soil.get(f)}" if soil.get(f) is None else f"{soil[f]:.2f}" for f in SOIL_FIELDS)
    raw = f"{district}|{village}|{sample_date}|{values}"
    return hashlib.sha256(raw.encode()).hexdigest()


def save_report(soil, district, village, sample_date, source="manual", db_path=DEFAULT_DB):
    """Validate and save one report. Returns (status, message); status is saved/duplicate/invalid."""
    district, village = _clean_name(district), _clean_name(village)
    if not district or not village:
        return "invalid", "District and village are required to save a report."
    errors = validate_soil(soil)
    if errors:
        return "invalid", "Not saved: " + " ".join(errors)

    row = (district, village, sample_date, *(soil.get(f) for f in SOIL_FIELDS), source,
           _fingerprint(district, village, sample_date, soil), datetime.now().isoformat(timespec="seconds"))
    try:
        with closing(_connect(db_path)) as conn:
            with conn:
                conn.execute(
                    "INSERT INTO soil_reports (district, village, sample_date, n, p, k, oc, ph, ec, zn, "
                    "source, fingerprint, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    row,
                )
    except sqlite3.IntegrityError:
        return "duplicate", "This report is already in the database, so it was not added again."
    return "saved", f"Report saved to the database for {village}, {district}. Thank you!"


def load_reports(db_path=DEFAULT_DB):
    with closing(_connect(db_path)) as conn:
        return pd.read_sql_query(
            "SELECT id, district, village, sample_date, n, p, k, oc, ph, ec, zn, source, created_at "
            "FROM soil_reports ORDER BY id DESC", conn)


def get_locations(db_path=DEFAULT_DB):
    """{district: [villages]} for the location dropdowns."""
    with closing(_connect(db_path)) as conn:
        rows = conn.execute(
            "SELECT DISTINCT district, village FROM soil_reports ORDER BY district, village").fetchall()
    locations = {}
    for district, village in rows:
        locations.setdefault(district, []).append(village)
    return locations


def estimate_soil(district, village, min_village_reports=5, db_path=DEFAULT_DB):
    """Location fallback (F2): median of nearby reports, with a confidence label.

    Uses the village if it has enough reports, otherwise the whole district.
    Returns None if there is no data for the district.
    """
    with closing(_connect(db_path)) as conn:
        df = pd.read_sql_query(
            "SELECT village, n, p, k, oc, ph, ec, zn FROM soil_reports WHERE district = ?",
            conn, params=(district,))
    if df.empty:
        return None

    in_village = df[df["village"] == village]
    if len(in_village) >= min_village_reports:
        subset, basis = in_village, village
        confidence = "medium" if len(in_village) >= 10 else "low to medium"
    else:
        subset, basis, confidence = df, f"{district} (district-wide)", "low"

    soil = {f: round(float(subset[f].median()), 2) for f in ("n", "p", "k", "oc", "ph", "ec")}
    zn_values = subset["zn"].dropna()
    soil["zn"] = round(float(zn_values.median()), 2) if len(zn_values) >= 3 else None
    return {"soil": soil, "basis": basis, "count": len(subset), "confidence": confidence}
