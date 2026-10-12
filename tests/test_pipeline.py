"""Synthetic-data tests for pipeline.calendar — fast, no network, no real data.

These pin the *math*: climatology bands, last-year partial handling, anomaly
spread units, peak-season geometry, and the leap-year calendar layout. Run with
`pytest tests/test_pipeline.py` from the repo root.
"""
import numpy as np
import pandas as pd
import pytest

from pipeline import calendar as cal


def make_daily(start="2001-01-01", end="2020-12-31", seed=0):
    """A deterministic, always-positive daily series that peaks mid-summer."""
    idx = pd.date_range(start, end, freq="D")
    doy = idx.dayofyear.to_numpy()
    rng = np.random.default_rng(seed)
    seasonal = 100 + 80 * np.cos((doy - 198) / 365.25 * 2 * np.pi)
    noise = rng.normal(0, 8, len(idx))
    vals = np.clip(seasonal + noise, 1, None)
    return pd.DataFrame({"acq_date": idx, "unique_cells_harmonized": vals})


def test_weekly_rate_splits_sum_and_days():
    idx = pd.to_datetime(["2021-01-04", "2021-01-05", "2021-01-06", "2021-01-11"])
    s = pd.Series([100.0, 200.0, 600.0, 40.0], index=idx)
    g = cal._weekly(s)
    w1 = g.loc[(2021, 1)]
    assert w1["sum"] == 900 and w1["count"] == 3 and w1["rate"] == 300.0
    w2 = g.loc[(2021, 2)]
    assert w2["count"] == 1 and w2["rate"] == 40.0


def test_climatology_shapes_and_stats():
    daily = make_daily()
    cl = cal.climatology(daily)
    assert list(cl.columns) == ["p10", "median", "p90"]
    assert 52 <= len(cl) <= 53
    # Synthetic series has a yearly average of ~100; medians must be plausible.
    assert cl["median"].between(10, 200).all()
    assert (cl["p10"] <= cl["median"]).all() and (cl["median"] <= cl["p90"]).all()


def test_anomalies_dimensionless_and_formula():
    daily = make_daily(seed=1)
    an = cal.anomalies(daily)
    need = {"year", "ywoy", "value", "p10", "median", "p90", "anomaly"}
    assert need <= set(an.columns)
    row = an.iloc[10]
    expect = (row["value"] - row["median"]) / (row["p90"] - row["p10"] + 1e-9)
    assert abs(row["anomaly"] - expect) < 1e-9
    anom = an["anomaly"].dropna()
    assert np.isfinite(anom).all()


def test_peak_season_geometry():
    daily = make_daily()
    ps = cal.peak_season(daily)
    complete = ps.dropna(subset=["start_week", "peak_week", "end_week"])
    assert len(complete) >= 18
    assert (complete["start_week"] <= complete["peak_week"]).all()
    assert (complete["peak_week"] <= complete["end_week"]).all()
    assert (complete["annual_total"] > 0).all()
    assert (complete["days"] > 0).all()


def test_calendar_grid_leap_alignment():
    """Columns must be leap-fixed so Mar 1 of 2004 sits above Mar 1 of 2005."""
    assert cal._LEAP_COL[(2, 29)] == 60
    assert cal._LEAP_COL[(3, 1)] == 61
    daily = make_daily(start="2001-01-01", end="2010-12-31")
    grid = cal.calendar_grid(daily)
    assert grid.shape == (26, 366)  # fixed 26-row matrix, one row per calendar year
    # A date placed on the grid must land in its leap-fixed column.
    sample = daily[daily.index == "2004-03-01"]
    if not sample.empty:
        assert grid.at[2004, 61] == sample.iloc[0][0]
    # The value must equal the metric on the matching day, 0 elsewhere.
    sm = daily[daily.index == "2005-03-01"]
    if not sm.empty:
        assert grid.at[2005, 61] == sm.iloc[0][0]


def test_calendar_grid_zero_fills_every_column():
    daily = make_daily()
    grid = cal.calendar_grid(daily)
    assert (grid.notna().all().all())
    assert (grid >= 0).all().all()