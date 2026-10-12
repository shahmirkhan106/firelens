"""Integrity invariants on the built processed artifacts (real data).

These are cheap structural checks (no recomputation) and catch exactly the
class of corruption the ".ok" repair addressed: truncated years, junk output
files, wrong shapes, and leaked indices leaking into CSVs.

Run with `pytest tests/test_artifacts.py` from the repo root, after a build.
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
PROC = ROOT / "data" / "processed"
AOIS = ["california", "north-india", "amazon", "australia-nsw", "east-siberia"]


def test_every_aoi_has_full_artifact_set():
    for aoi in AOIS:
        d = PROC / aoi
        assert d.is_dir(), f"missing {aoi}"
        for name in ("calendar_grid.csv", "peak_season.csv", "climatology.csv",
                     "anomalies.csv", "calibration.csv", "merged.parquet",
                     "meta.json"):
            assert (d / name).exists(), f"{aoi}: missing {name}"


def test_calendar_grid_is_26x366_leap_aligned():
    for aoi in AOIS:
        g = pd.read_csv(PROC / aoi / "calendar_grid.csv", index_col=0)
        assert g.shape == (26, 366), aoi
        assert list(g.index) == list(range(2001, 2027)), aoi
        assert (g.notna().all().all()) and (g >= 0).all().all(), aoi
        # Leap-fixed layout: column 60 is Feb 29 in leap years and must carry a
        # value for 2024 (pandas labels non-numeric headers as strings).
        assert pd.notna(g.at[2024, "60"]), aoi


def test_peak_season_has_no_index_leak():
    for aoi in AOIS:
        ps = pd.read_csv(PROC / aoi / "peak_season.csv")
        want = {"year", "start_week", "peak_week", "end_week", "annual_total", "days"}
        assert want <= set(ps.columns), aoi
        assert "index" not in ps.columns, aoi
        assert ps["year"].is_monotonic_increasing, aoi
        # The season window is expanded to always contain the busiest week, so
        # start <= peak <= end holds even for sharply tail/front-loaded years.
        assert (ps["start_week"] <= ps["peak_week"]).all(), aoi
        assert (ps["peak_week"] <= ps["end_week"]).all(), aoi
        assert (ps["start_week"] <= ps["end_week"]).all(), aoi
        assert (ps["days"] > 0).all(), aoi


def test_climatology_and_anomalies_columns():
    for aoi in AOIS:
        cl = pd.read_csv(PROC / aoi / "climatology.csv")
        assert set(cl.columns) >= {"p10", "median", "p90"}, aoi
        assert 52 <= len(cl) <= 53, aoi
        an = pd.read_csv(PROC / aoi / "anomalies.csv", index_col=0)
        assert {"year", "ywoy", "value", "p10", "median", "p90",
                "anomaly"} <= set(an.columns), aoi
        anom = an["anomaly"].dropna()
        # Zero-spread weeks (climatology never burns) carry NaN, never an
        # exploded ratio that would dwarf every real anomaly.
        assert anom.abs().max() < 100, (aoi, anom.abs().max())


def test_merged_harmonized_is_materialized():
    for aoi in AOIS:
        m = pd.read_parquet(PROC / aoi / "merged.parquet")
        need = {"acq_date", "unique_cells_modis", "unique_cells_viirs",
                "unique_cells_harmonized"}
        assert need <= set(m.columns), (aoi, set(m.columns))
        assert not m[["acq_date"]].isna().any().any(), aoi
        # Wherever either sensor detected fire, the harmonized metric must carry
        # a finite number (not NaN); NaN is reserved for days with no fire.
        any_sensor = (m["unique_cells_modis"] > 0) | (m["unique_cells_viirs"] > 0)
        assert m.loc[any_sensor, "unique_cells_harmonized"].notna().all(), aoi


def test_calibration_sane():
    for aoi in AOIS:
        c = pd.read_csv(PROC / aoi / "calibration.csv")
        assert {"slope", "r2"} <= set(c.columns), aoi
        assert (c["slope"] > 0).all(), aoi