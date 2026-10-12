"""Stage 4: build the burning-activity calendar view for an AOI.

Columns, daily/weekly: climatology (median + percentile bands), anomaly
(robust p10-p90 spread vs climatology), and annual peak-season detection.

Year conventions: the weekly tables (climatology, anomaly, peak season) are
grouped by ISO year-week so that the weeks belonging to one season stay
together, while the heatmap grid uses calendar years. For these AOIs the fire
seasons sit safely inside a single calendar year, so the two conventions
agree; the ISO grouping only matters if a future region's season crosses the
Dec/Jan boundary.
"""
import numpy as np
import pandas as pd

YEAR_VS = [2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010,
           2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020,
           2021, 2022, 2023, 2024, 2025, 2026]


def _weekly(srs: pd.Series) -> pd.DataFrame:
    """Bin a daily series to ISO year-week.

    Returns columns ``sum`` (the week's total, used for annual totals),
    ``days`` (how many days actually contributed) and ``rate``
    (sum/days, i.e. a genuine cells-per-day figure). Week 1 and week 53 are
    often partial because of the ISO year boundary, so a raw sum is not
    comparable across weeks -- everything user-facing uses ``rate``.
    """
    df = srs.reset_index().copy()
    df.columns = ["date", "value"]
    iso = df["date"].dt.isocalendar()
    df["ywoy"] = iso.week
    df["year"] = iso.year
    g = df.groupby(["year", "ywoy"])["value"].agg(["sum", "count"])
    g["rate"] = g["sum"] / g["count"]
    return g


def climatology(daily: pd.DataFrame, metric: str = "unique_cells_harmonized",
                by: str = "week") -> pd.DataFrame:
    """Climatological daily rate per week-of-year: median & 10th/50th/90th."""
    srs = daily.set_index("acq_date")[metric].dropna()
    if by == "week":
        wk = _weekly(srs).reset_index()
        tbl = wk.groupby("ywoy")["rate"].describe(percentiles=[0.1, 0.5, 0.9])
        tbl = tbl.rename(columns={"10%": "p10", "50%": "median", "90%": "p90"})
        tbl = tbl[["p10", "median", "p90"]]
        tbl.index.name = "week"
    else:  # by day-of-year
        srs = srs.copy()
        srs.index = pd.Series(srs.index).dt.dayofyear.values
        tbl = srs.groupby(level=0).describe(percentiles=[0.1, 0.5, 0.9])
        tbl = tbl.rename(columns={"10%": "p10", "50%": "median", "90%": "p90"})
        tbl = tbl[["p10", "median", "p90"]]
        tbl.index.name = "doy"
    return tbl


def anomalies(daily: pd.DataFrame, metric: str = "unique_cells_harmonized",
              by: str = "week") -> pd.DataFrame:
    """Period anomaly: (value - climatology median) / (p90 - p10).

    Both terms are daily rates, so the score is dimensionless and unaffected
    by the switch from weekly sums to weekly rates. A week whose climatology
    has zero spread (p10 == p90 == median, e.g. winter weeks that almost never
    burn) has no meaningful reference band, so its anomaly is NaN rather than a
    numerically exploded ratio.
    """
    srs = daily.set_index("acq_date")[metric].dropna()
    cl = climatology(daily, by=by)
    wk = _weekly(srs).reset_index().rename(columns={"rate": "value"})
    joined = wk.set_index("ywoy").join(cl).reset_index()
    spread = joined["p90"] - joined["p10"]
    joined["anomaly"] = np.where(
        spread > 0,
        (joined["value"] - joined["median"]) / spread,
        np.nan,
    )
    return joined


def peak_season(daily: pd.DataFrame, metric: str = "unique_cells_harmonized") -> pd.DataFrame:
    """Per-year peak detection using cumulative-activity method:
    start = when cumulative reaches 20% of annual total, peak = max week,
    end = 90%. The season window is then expanded to guarantee it contains the
    busiest week, so a sharply tail-loaded season (2009 NSW: one huge December
    week after the 90% crossing) or a front-loaded one (2014 NSW: peak before
    the 20% crossing) still yields a coherent start <= peak <= end bar."""
    srs = daily.set_index("acq_date")[metric].dropna()
    wk = _weekly(srs).reset_index()
    rows = []
    for yr, g in wk.groupby("year"):
        tot = g["sum"].sum()
        if tot <= 0:
            rows.append({"year": yr, "start_week": np.nan, "peak_week": np.nan,
                         "end_week": np.nan, "annual_total": 0.0, "days": int(g["count"].sum())})
            continue
        cum = g["sum"].cumsum() / tot
        start = g.loc[cum >= 0.2, "ywoy"].min()
        end = g.loc[cum >= 0.9, "ywoy"].min()
        peak = g.loc[g["sum"].idxmax(), "ywoy"]
        rows.append({"year": yr,
                     "start_week": int(min(start, peak)),
                     "peak_week": int(peak),
                     "end_week": int(max(end, peak)),
                     "annual_total": float(tot),
                     "days": int(g["count"].sum())})
    return pd.DataFrame(rows)


# Column layout for the heatmap: a fixed 366-day year so that every row lines
# up. Using dt.dayofyear directly would shift leap years by one day after
# 29 Feb, so 2004-03-01 would not sit above 2005-03-01.
_LEAP_COL = {(t.month, t.day): t.dayofyear
             for t in pd.date_range("2024-01-01", "2024-12-31", freq="D")}


def calendar_grid(daily: pd.DataFrame, metric: str = "unique_cells_harmonized"):
    """Year x day-of-year matrix for the heatmap, on a leap-year column layout."""
    srs = daily.set_index("acq_date")[metric].dropna()
    idx = pd.Series(srs.index)
    col = [_LEAP_COL[(ts.month, ts.day)] for ts in idx]
    yr = idx.dt.year.values
    grid = pd.DataFrame(0.0, index=YEAR_VS, columns=range(1, 367))
    for (y, c), v in zip(zip(yr, col), srs.values):
        if y in YEAR_VS:
            grid.at[y, c] = float(v)
    return grid
