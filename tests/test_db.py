"""Tests for saving reports and the location fallback (uses a temporary database)."""

import db

SOIL = {"ph": 6.5, "ec": 0.3, "oc": 0.5, "n": 250, "p": 12, "k": 150, "zn": None}


def test_save_and_reject_duplicate(tmp_path):
    path = tmp_path / "test.db"
    db.init_db(path)
    assert db.save_report(SOIL, "Test District", "Test Village", "2025-01-01", db_path=path)[0] == "saved"
    assert db.save_report(SOIL, "test district", "test  village", "2025-01-01", db_path=path)[0] == "duplicate"
    assert len(db.load_reports(path)) == 1


def test_invalid_report_not_saved(tmp_path):
    path = tmp_path / "test.db"
    db.init_db(path)
    status, _ = db.save_report(dict(SOIL, ph=20), "D", "V", "2025-01-01", db_path=path)
    assert status == "invalid"
    assert db.load_reports(path).empty


def test_estimate_falls_back_to_district(tmp_path):
    path = tmp_path / "test.db"
    db.init_db(path)
    for i in range(6):
        db.save_report(dict(SOIL, n=200 + i), "D", "Big Village", f"2025-01-0{i + 1}", db_path=path)
    db.save_report(dict(SOIL, n=300), "D", "Small Village", "2025-02-01", db_path=path)

    village_est = db.estimate_soil("D", "Big Village", db_path=path)
    assert village_est["basis"] == "Big Village" and village_est["count"] == 6

    district_est = db.estimate_soil("D", "Small Village", db_path=path)
    assert district_est["confidence"] == "low" and district_est["count"] == 7
    assert db.estimate_soil("Unknown", "X", db_path=path) is None
