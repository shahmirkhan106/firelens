"""API smoke tests via FastAPI TestClient against the real processed data.

Every success shape the frontend depends on is pinned here so a schema drift
(or a truncated-artifact regression) fails loudly. Run with
`pytest tests/test_api.py` from the repo root.
"""
import math

import starlette.testclient

from backend.app import app as fastapi_app

client = starlette.testclient.TestClient(fastapi_app)
AOIS = ["california", "north-india", "amazon", "australia-nsw", "east-siberia"]


def test_summary_shape_for_every_aoi():
    for aoi in AOIS:
        r = client.get(f"/aoi/{aoi}/summary")
        assert r.status_code == 200, aoi
        j = r.json()
        for k in ("years", "days", "cell_days", "full_years", "gap_years",
                  "typical_days_per_year", "seasons", "calibration", "overlap"):
            assert k in j, (aoi, k)
        # gap detection must not need re-downloads post-repair
        assert not j["gap_years"], (aoi, j["gap_years"])
        assert j["full_years"] >= 25, aoi
        assert j["days"] > 3000, (aoi, j["days"])


def test_timeseries_aligned():
    for aoi in AOIS:
        r = client.get(f"/aoi/{aoi}/timeseries")
        assert r.status_code == 200, aoi
        d, v = r.json()["dates"], r.json()["values"]
        assert len(d) == len(v) > 7000, (aoi, len(d))
        assert v[0] is not None, aoi


def test_comparison_series_harmonized():
    for aoi in AOIS:
        j = client.get(f"/aoi/{aoi}/comparison").json()
        n = len(j["dates"])
        assert n > 7000, (aoi, n)
        for k in ("modis", "viirs", "harmonized"):
            assert len(j[k]) == n, (aoi, k)
        # harmonized must be filled wherever either sensor saw fire
        for m, v, h in zip(j["modis"], j["viirs"], j["harmonized"]):
            if m is not None or v is not None:
                assert h is not None, aoi


def test_climatology_weeks():
    for aoi in AOIS:
        j = client.get(f"/aoi/{aoi}/climatology").json()
        assert {"weeks", "p10", "median", "p90"} <= set(j), aoi
        n = len(j["median"])
        assert 52 <= n <= 53, (aoi, n)
        assert all(a <= b <= c for a, b, c in
                   zip(j["p10"], j["median"], j["p90"])), aoi


def test_anomalies_units_are_spreads_and_clean():
    for aoi in AOIS:
        recs = client.get(f"/aoi/{aoi}/anomalies").json()
        assert len(recs) > 1000, (aoi, len(recs))
        keys = {"year", "ywoy", "value", "p10", "median", "p90", "anomaly"}
        for rec in recs:
            assert keys <= set(rec), (aoi, rec)
            a = rec["anomaly"]
            assert a is None or math.isfinite(a), (aoi, rec)
            if a is not None:
                assert abs(a) < 100, (aoi, a)
            assert not any(k.startswith("Unnamed") or k == "index"
                           for k in rec), (aoi, rec.keys())


def test_peak_season_clean_records():
    for aoi in AOIS:
        recs = client.get(f"/aoi/{aoi}/peak-season").json()
        assert len(recs) >= 20, (aoi, len(recs))
        for r in recs:
            assert {"year", "start_week", "peak_week", "end_week",
                    "annual_total", "days"} <= set(r), (aoi, r)
            assert r["start_week"] <= r["peak_week"] <= r["end_week"], (aoi, r)
            assert r["annual_total"] > 0 and r["days"] > 0, (aoi, r)
            assert "index" not in r, (aoi, r)


def test_calendar_partial_year_flag():
    for aoi in AOIS:
        j = client.get(f"/aoi/{aoi}/calendar").json()
        assert list(j["day_of_year"]) == list(range(1, 367)), aoi
        assert len(j["years"]) == len(j["grid"]) == 26, aoi
        assert len(j["grid"][0]) == 366, aoi
        assert j["last_observed_date"], aoi
        assert j["partial_last_year"] is True, aoi  # 2026 is in progress


def test_unknown_aoi_404():
    assert client.get("/aoi/nowhere/summary").status_code == 404
    assert client.get("/aoi/nowhere/calendar").status_code == 404
    assert client.get("/aois").status_code == 200