"""Stage 3: harmonize MODIS and VIIRS records into one MODIS-equivalent series.

Method
------
1. Grid to ~1 km H3 cells -> per-day unique fire cells & FRP sum (prevents the
   pixel-size inflation artifact).
2. Overlap calibration (2012 -> present): fit a regression MODIS ~ g(VIIRS) per
   AOI so the VIIRS-era years are expressed in MODIS-equivalent units.
3. Apply the fitted model to all VIIRS-only and future years.

The result is one consistent "burning activity" series, 2001 -> present.
"""
from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class Calibration:
    a: float            # intercept
    b: float            # slope
    metric: str         # 'unique_cells' | 'frp_mw'
    r2: float


def _fit(x: np.ndarray, y: np.ndarray) -> tuple[float, float, float]:
    """OLS y ~ a + b x with R^2."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    A = np.vstack([np.ones_like(x), x]).T
    (a, b), *_ = np.linalg.lstsq(A, y, rcond=None)
    yhat = a + b * x
    ss_res = float(np.sum((y - yhat) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    return a, b, r2


def fit_overlap(modis: pd.DataFrame, viirs: pd.DataFrame,
                overlap_start: str = "2012-01-01", viirs_shift: int = 0,
                metric: str = "unique_cells") -> Calibration:
    """Fit VIIRS->MODIS mapping on the overlap period.

    viirs_shift: apply a+b*x to VIIRS shifted by N days (MODIS Aqua/Terra have
    morning+afternoon overpasses vs VIIRS afternoon-only; per-metric this is
    small, kept configurable).
    """
    m = modis[modis["acq_date"] >= overlap_start].set_index("acq_date")[metric]
    v = viirs.set_index("acq_date")[metric]
    if viirs_shift:
        v = v.shift(viirs_shift)
    joined = pd.concat({"m": m, "v": v}, axis=1).dropna()
    if len(joined) < 30:
        raise ValueError("not enough overlap days to calibrate")
    a, b, r2 = _fit(joined["v"].values, joined["m"].values)
    return Calibration(a=a, b=b, metric=metric, r2=r2)


def apply_calibration(srs: pd.Series, cal: Calibration) -> pd.Series:
    """Express a series in MODIS-equivalent units."""
    pred = cal.a + cal.b * np.asarray(srs, dtype=float)
    return pd.Series(np.maximum(pred, 0.0), index=srs.index, name=srs.name)


def harmonize_series(daily: dict[str, pd.DataFrame], aoi: str,
                     metric: str = "unique_cells") -> tuple[pd.DataFrame, dict]:
    """Merge MODIS + VIIRS daily series into one harmonized calendar frame.

    Returns (merged_with_harmonized_col, calibration_report).
    """
    modis = daily.get("MODIS_SP")
    viirs = daily.get("VIIRS_SNPP_SP")
    if modis is None:
        raise ValueError("MODIS_SP daily data required as the reference sensor")
    if viirs is None:
        raise ValueError("VIIRS_SNPP_SP daily data required to calibrate the overlap")

    cal = fit_overlap(modis, viirs, metric=metric)

    # Full calendar = union of MODIS and VIIRS dates, MODIS-equivalent units
    start = min(modis["acq_date"].min(), viirs["acq_date"].min())
    end = max(modis["acq_date"].max(), viirs["acq_date"].max())
    full = pd.date_range(start=start, end=end, freq="D")
    merged = pd.DataFrame({"acq_date": full})

    modis_srs = modis.set_index("acq_date")[metric]
    viirs_srs = viirs.set_index("acq_date")[metric]
    merged[f"{metric}_modis"] = modis_srs.reindex(full).values
    merged[f"{metric}_viirs"] = viirs_srs.reindex(full).values
    harmonized = apply_calibration(viirs_srs, cal)
    merged["calibrated"] = harmonized.reindex(full).values

    # Naive splice: MODIS raw where it exists, raw VIIRS otherwise, unscaled.
    # This is the uncorrected record, so it is only comparable to
    # *_harmonized up to the moment the sensors are spliced together.
    merged[f"{metric}_naive"] = merged[f"{metric}_modis"].copy()
    has_modis = merged[f"{metric}_modis"].notna()
    merged.loc[~has_modis, f"{metric}_naive"] = merged.loc[~has_modis, f"{metric}_viirs"]

    # MODIS years keep their raw value; VIIRS-only periods use calibrated
    merged[f"{metric}_harmonized"] = merged[f"{metric}_modis"].copy()
    merged.loc[~has_modis, f"{metric}_harmonized"] = merged.loc[~has_modis, "calibrated"]

    report = {
        "aoi": aoi,
        "metric": metric,
        "calibration": cal,
        "overlap_start": "2012-01-01",
        "viirs_shift_days": 0,
    }
    return merged.reset_index(), report


def build_report(report: dict) -> pd.DataFrame:
    cal = report["calibration"]
    return pd.DataFrame([{
        "aoi": report["aoi"],
        "metric": cal.metric,
        "intercept": round(cal.a, 4),
        "slope": round(cal.b, 4),
        "r2": round(cal.r2, 4),
        "overlap_start": report["overlap_start"],
        "viirs_shift_days": report["viirs_shift_days"],
    }])