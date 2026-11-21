"""Fill the database with SYNTHETIC demo reports so the location fallback can be demonstrated.

These are NOT real soil tests. Every record is tagged source='demo'.
Replace them with real Soil Health Card data when you have it.
Run once:  python make_demo_data.py   (running again adds nothing new)
"""

import random
from datetime import date, timedelta

import db

# Typical value per district: (pH, EC, OC %, N, P, K). Rename districts/villages freely.
DISTRICTS = {
    "Demo District A": (5.6, 0.25, 0.45, 230, 12, 140),   # acidic, low N and OC
    "Demo District B": (6.4, 0.35, 0.55, 270, 18, 190),
    "Demo District C": (7.2, 0.60, 0.62, 300, 24, 240),
    "Demo District D": (8.0, 1.40, 0.40, 210, 9, 300),    # alkaline, slightly saline
}
VILLAGES_PER_DISTRICT = 5
REPORTS_PER_VILLAGE = 12


def clip(value, low, high):
    return max(low, min(high, value))


def make_report(rng, base, village_shift):
    ph, ec, oc, n, p, k = base
    return {
        "ph": round(clip(rng.gauss(ph + village_shift * 0.3, 0.35), 4.0, 9.5), 1),
        "ec": round(clip(rng.gauss(ec, ec * 0.3), 0.05, 6.0), 2),
        "oc": round(clip(rng.gauss(oc + village_shift * 0.05, 0.10), 0.1, 2.0), 2),
        "n": round(clip(rng.gauss(n + village_shift * 25, 40), 80, 700)),
        "p": round(clip(rng.gauss(p + village_shift * 3, 5), 2, 80), 1),
        "k": round(clip(rng.gauss(k + village_shift * 20, 45), 50, 600)),
        "zn": round(clip(rng.gauss(0.8, 0.35), 0.1, 3.0), 2) if rng.random() < 0.6 else None,
    }


def main():
    rng = random.Random(42)  # fixed seed: same data every run
    db.init_db()
    saved = 0
    for district, base in DISTRICTS.items():
        for v in range(1, VILLAGES_PER_DISTRICT + 1):
            village, shift = f"Village {district[-1]}{v}", rng.uniform(-1, 1)
            for _ in range(REPORTS_PER_VILLAGE):
                sample_date = (date(2024, 1, 1) + timedelta(days=rng.randint(0, 700))).isoformat()
                status, _ = db.save_report(make_report(rng, base, shift), district, village,
                                           sample_date, source="demo")
                saved += status == "saved"
    print(f"Added {saved} synthetic demo reports. Database now has {len(db.load_reports())} reports.")


if __name__ == "__main__":
    main()
