"""FireLens API — serves harmonized burning-activity calendar artifacts."""
import json
from functools import lru_cache
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

DATA = Path(__file__).resolve().parent.parent / "data" / "processed"
DAILY = Path(__file__).resolve().parent.parent / "data" / "daily"

app = FastAPI(title="FireLens API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _aoi_dir(aoi: str) -> Path:
    d = DATA / aoi
    if not d.exists():
        raise HTTPException(404, f"AOI '{aoi}' not processed. Have: {_available_aois()}")
    return d


def _available_aois() -> list[str]:
    return sorted(p.name for p in DATA.iterdir() if p.is_dir())


def _stamp(*paths: Path) -> float:
    """Newest mtime across the given files (0.0 if none exist).

    Folded into every cache key, so re-running the pipeline produces a different
    key and stale data is served never — no restart required.
    """
    newest = 0.0
    for p in paths:
        try:
            newest = max(newest, p.stat().st_mtime)
        except OSError:
            continue
    return newest


def _aoi_stamp(aoi: str) -> float:
    """Newest mtime of any artifact backing this AOI (processed + daily)."""
    return max(
        _stamp(*sorted((DATA / aoi).glob("*"))) if (DATA / aoi).is_dir() else 0.0,
        _stamp(*sorted((DAILY / aoi).glob("*"))) if (DAILY / aoi).is_dir() else 0.0,
    )


def _load(aoi: str, name: str, index_col=None, parse_dates=None) -> pd.DataFrame:
    return _load_cached(aoi, name, index_col, parse_dates, _aoi_stamp(aoi)).copy()


@lru_cache(maxsize=128)
def _load_cached(aoi: str, name: str, index_col, parse_dates, _stamp_key: float) -> pd.DataFrame:
    d = _aoi_dir(aoi)
    fp = d / name
    if not fp.exists():
        raise HTTPException(404, f"{name} missing for {aoi}")
    if fp.suffix == ".parquet":
        return pd.read_parquet(fp)
    return pd.read_csv(fp, index_col=index_col, parse_dates=parse_dates)


@app.get("/aois")
def aois():
    return {"aois": _available_aois()}


@app.get("/aoi/{aoi}/meta")
def aoi_meta(aoi: str):
    d = _aoi_dir(aoi)
    meta = json.loads((d / "meta.json").read_text()) if (d / "meta.json").exists() else {}
    return {"aoi": aoi, **meta}


@app.get("/aoi/{aoi}/calendar")
def calendar(aoi: str):
    return _calendar_cached(aoi, _aoi_stamp(aoi))


@lru_cache(maxsize=16)
def _calendar_cached(aoi: str, _stamp_key: float) -> dict:
    grid = _load(aoi, "calendar_grid.csv", index_col=0)
    grid = grid.astype(float)
    merged = _load(aoi, "merged.parquet")
    last_date = pd.to_datetime(merged["acq_date"]).max()
    last_year = int(last_date.year)
    # A year is "partial" when it does not reach the end of its own December,
    # so e.g. 2026 is rendered distinctly instead of looking like a quiet year.
    year_end = pd.Timestamp(year=last_year, month=12, day=28)
    return {
        "years": [int(y) for y in grid.index],
        "day_of_year": list(range(1, 367)),
        "grid": grid.values.tolist(),
        "last_observed_date": last_date.strftime("%Y-%m-%d"),
        "partial_last_year": bool(last_date < year_end),
    }


@app.get("/aoi/{aoi}/climatology")
def climatology(aoi: str):
    return _climatology_cached(aoi, _aoi_stamp(aoi))


@lru_cache(maxsize=16)
def _climatology_cached(aoi: str, _stamp_key: float) -> dict:
    cl = _load(aoi, "climatology.csv", index_col=0)
    return {"weeks": [int(i) for i in cl.index],
            "p10": cl["p10"].round(2).tolist(),
            "median": cl["median"].round(2).tolist(),
            "p90": cl["p90"].round(2).tolist()}


@app.get("/aoi/{aoi}/peak-season")
def peak_season(aoi: str):
    return _peak_cached(aoi, _aoi_stamp(aoi))


@lru_cache(maxsize=16)
def _peak_cached(aoi: str, _stamp_key: float) -> list:
    df = _load(aoi, "peak_season.csv", index_col=0)
    df = df.dropna(subset=["start_week", "peak_week", "end_week"])
    # drop=True: the CSV index is already consumed by index_col=0, so a plain
    # reset_index() would inject a junk "index" column into every record.
    return df.reset_index(drop=True).to_dict(orient="records")


@app.get("/aoi/{aoi}/timeseries")
def timeseries(aoi: str, sensor: str = "harmonized"):
    return _timeseries_cached(aoi, sensor, _aoi_stamp(aoi))


@lru_cache(maxsize=32)
def _timeseries_cached(aoi: str, sensor: str, _stamp_key: float) -> dict:
    df = _load(aoi, "merged.parquet")
    df["acq_date"] = pd.to_datetime(df["acq_date"])
    col = "unique_cells_harmonized" if sensor == "harmonized" else "unique_cells_naive"
    out = df[["acq_date", col]].copy()
    out.columns = ["date", "value"]
    out = out.dropna(subset=["value"])
    return {"dates": out["date"].dt.strftime("%Y-%m-%d").tolist(),
            "values": out["value"].round(1).tolist()}


@app.get("/aoi/{aoi}/comparison")
def comparison(aoi: str):
    """Both sensors plus the harmonized output, aligned on one date axis."""
    return _comparison_cached(aoi, _aoi_stamp(aoi))


@lru_cache(maxsize=16)
def _comparison_cached(aoi: str, _stamp_key: float) -> dict:
    df = _load(aoi, "merged.parquet")
    df["acq_date"] = pd.to_datetime(df["acq_date"])
    cols = ["unique_cells_modis", "unique_cells_viirs", "unique_cells_harmonized"]
    out = df[["acq_date"] + cols].copy()
    out = out.dropna(subset=cols, how="all")
    def _safe(s):
        vals = []
        for v in s:
            if pd.isna(v):
                vals.append(None)
                continue
            try:
                f = float(v)
                if f != f or f == float("inf") or f == float("-inf"):
                    vals.append(None)
                else:
                    vals.append(round(f, 1))
            except Exception:
                vals.append(None)
        return vals

    return {
        "dates": out["acq_date"].dt.strftime("%Y-%m-%d").tolist(),
        "modis": _safe(out[cols[0]]),
        "viirs": _safe(out[cols[1]]),
        "harmonized": _safe(out[cols[2]]),
    }


@app.get("/aoi/{aoi}/summary")
def summary(aoi: str):
    """Headline numbers shown above the charts."""
    return _summary_cached(aoi, _aoi_stamp(aoi))


@lru_cache(maxsize=16)
def _summary_cached(aoi: str, _stamp_key: float) -> dict:
    df = _load(aoi, "merged.parquet")
    df["acq_date"] = pd.to_datetime(df["acq_date"])
    calib = calibration(aoi)
    clim = _load(aoi, "climatology.csv", index_col=0)
    peaks = _load(aoi, "peak_season.csv", index_col=0).dropna(
        subset=["start_week", "peak_week", "end_week"]
    )

    overlap = _overlap_facts(aoi, _aoi_stamp(aoi))

    peak_week = int(clim["median"].idxmax())
    srs = df.set_index("acq_date")["unique_cells_harmonized"]
    total_by_year = srs.groupby(srs.index.year).sum()
    days_by_year = srs.notna().groupby(srs.index.year).sum()

    # 2001 and 2026 are both partial (the record starts 2 Jan 2001 and ends
    # mid-2026), so a raw year-over-year percentage would mostly measure how
    # much of the year we happen to have. Compare mean daily rate instead.
    #
    # Completeness must be judged *relative to this region*, not against a fixed
    # day count: a boreal AOI like east-siberia legitimately has no detections
    # in deep winter (~250 observed days/yr), so a flat "300 days" bar would
    # flag every healthy year. Only years far below the region's own typical
    # coverage indicate a real hole in the archive.
    typical_days = float(days_by_year.median())
    gap_cutoff = max(60.0, typical_days * 0.6)
    last_year = int(df["acq_date"].dt.year.max())
    full_years = days_by_year[days_by_year >= gap_cutoff]
    rate_by_year = (total_by_year / days_by_year).reindex(full_years.index).dropna()
    busiest_year = int(total_by_year.idxmax())
    if len(rate_by_year) >= 2:
        first_rate = float(rate_by_year.iloc[0])
        busiest_rate_year = int(rate_by_year.idxmax())
        change_pct = (
            round((rate_by_year.max() / first_rate - 1) * 100, 1) if first_rate else None
        )
    else:
        busiest_rate_year, change_pct = None, None

    return {
        "aoi": aoi,
        "years": [int(y) for y in (df["acq_date"].dt.year.min(), df["acq_date"].dt.year.max())],
        "days": int(df["unique_cells_harmonized"].notna().sum()),
        "cell_days": int(df["unique_cells_harmonized"].fillna(0).sum()),
        "busiest_year": busiest_year,
        "busiest_year_partial": bool(days_by_year.get(busiest_year, 0) < gap_cutoff),
        "busiest_rate_year": busiest_rate_year,
        "busiest_vs_first_pct": change_pct,
        "full_years": int(len(full_years)),
        "typical_days_per_year": round(typical_days, 1),
        # Years whose observed-day count falls far below this region's own norm
        # are archive holes (failed downloads), not quiet fire seasons. Exclude
        # the final year: it is legitimately mid-season.
        "gap_years": {
            str(int(y)): int(d) for y, d in days_by_year.items()
            if d < gap_cutoff and int(y) != last_year
        },
        "peak_week": peak_week,
        "peak_week_activity": round(float(clim["median"].max()), 1),
        "peak_week_activity_note": "median cells/day in that week, across all years",
        "seasons": int(len(peaks)),
        "calibration": {
            "slope": calib.get("slope"),
            "r2": calib.get("r2"),
            "overlap_start": calib.get("overlap_start"),
        },
        "overlap": overlap,
    }


@lru_cache(maxsize=16)
def _overlap_facts(aoi: str, _stamp_key: float) -> dict:
    """Directly measured MODIS-vs-VIIRS disagreement on days both sensors observed.

    This is the core problem FireLens solves: on identical days and identical
    ground, VIIRS (375 m) reports far more distinct fire cells than MODIS (1 km).
    """
    daily = DAILY / aoi
    mp, vp = daily / "MODIS_SP.parquet", daily / "VIIRS_SNPP_SP.parquet"
    if not (mp.exists() and vp.exists()):
        return {}
    m = pd.read_parquet(mp).set_index("acq_date")
    v = pd.read_parquet(vp).set_index("acq_date")
    j = m.join(v, lsuffix="_m", rsuffix="_v", how="inner")
    if j.empty:
        return {}
    ratio = (j["unique_cells_v"] / j["unique_cells_m"].replace(0, pd.NA)).median()
    return {
        "days": int(len(j)),
        "from": str(j.index.min().date()),
        "to": str(j.index.max().date()),
        "cell_inflation": round(float(ratio), 2),
        "frp_ratio": round(float(j["frp_mw_v"].sum() / j["frp_mw_m"].sum()), 2),
        "modis_cells": int(j["unique_cells_m"].sum()),
        "viirs_cells": int(j["unique_cells_v"].sum()),
    }


@app.get("/aoi/{aoi}/anomalies")
def anomalies(aoi: str):
    return _anomalies_cached(aoi, _aoi_stamp(aoi))


@lru_cache(maxsize=16)
def _anomalies_cached(aoi: str, _stamp_key: float) -> list:
    # index_col=0 drops the CSV's unnamed index column, which would otherwise
    # be serialised into every record as a junk "Unnamed: 0" key.
    df = _load(aoi, "anomalies.csv", index_col=0)
    recs = df.round(4).to_dict(orient="records")
    for rec in recs:  # NaN (zero-spread weeks) must become JSON null, not break encoding
        for k, v in rec.items():
            if isinstance(v, float) and pd.isna(v):
                rec[k] = None
    return recs


@app.get("/aoi/{aoi}/calibration")
def calibration(aoi: str):
    df = _load(aoi, "calibration.csv", index_col=0)
    return df.iloc[0].to_dict()


@app.on_event("startup")
def warm_cache():
    """Pre-load every artifact so the first page view is instant."""
    for aoi in _available_aois():
        try:
            warm_aoi(aoi)
        except Exception as e:  # keep serving even if one region is incomplete
            print(f"[warm] {aoi} skipped: {e}")


def warm_aoi(aoi: str) -> None:
    st = _aoi_stamp(aoi)
    _calendar_cached(aoi, st)
    _climatology_cached(aoi, st)
    _peak_cached(aoi, st)
    _timeseries_cached(aoi, "harmonized", st)
    _timeseries_cached(aoi, "raw", st)
    _comparison_cached(aoi, st)
    _anomalies_cached(aoi, st)
    _summary_cached(aoi, st)
    print(f"[warm] {aoi} cached")


# Every cached function, for explicit invalidation.
_CACHED = (
    _load_cached,
    _calendar_cached,
    _climatology_cached,
    _peak_cached,
    _timeseries_cached,
    _comparison_cached,
    _anomalies_cached,
    _summary_cached,
    _overlap_facts,
)


@app.post("/cache/clear")
def cache_clear(aoi: str | None = None, rewarm: bool = True):
    """Drop cached artifacts.

    Not normally needed — cache keys embed each AOI's newest file mtime, so a
    pipeline re-run invalidates automatically. Use this to force a reload or to
    reclaim memory.

        curl -X POST 'localhost:8000/cache/clear'
        curl -X POST 'localhost:8000/cache/clear?aoi=california'
    """
    for fn in _CACHED:
        fn.cache_clear()
    if rewarm:
        targets = [aoi] if aoi else _available_aois()
        for a in targets:
            try:
                warm_aoi(a)
            except Exception as e:
                print(f"[rewarm] {a} skipped: {e}")
    return {"cleared": True, "rewarmed": rewarm, "aoi": aoi or "all"}


@app.get("/cache/status")
def cache_status():
    return {
        "aois": {a: _aoi_stamp(a) for a in _available_aois()},
        "entries": {fn.__name__: fn.cache_info()._asdict() for fn in _CACHED},
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)