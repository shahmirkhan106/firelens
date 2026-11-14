"""Run the full harmonization pipeline for an AOI -> calendar artifacts."""
import argparse
import json
import shutil
from pathlib import Path

import pandas as pd

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline import calendar as cal  # noqa: E402
from pipeline import harmonize  # noqa: E402
from pipeline import prepare  # noqa: E402

AOI_ALIASES = {"california": "california", "north-india": "north-india",
               "amazon": "amazon", "australia-nsw": "australia-nsw",
               "east-siberia": "east-siberia"}
PRODUCTS = ["MODIS_SP", "VIIRS_SNPP_SP"]


ROOT = Path(__file__).resolve().parent.parent

def process(aoi: str, raw=ROOT / "data" / "raw", out=ROOT / "data" / "processed",
            rebuild: bool = True):
    out_dir = out / aoi
    out_dir.mkdir(parents=True, exist_ok=True)

    # Stages 1-2
    daily_dir = ROOT / "data" / "daily" / aoi
    daily_dir.mkdir(parents=True, exist_ok=True)
    daily = {}
    chunk = "Y" if aoi in ("amazon", "east-siberia") else None
    for product in PRODUCTS:
        cached = daily_dir / f"{product}.parquet"
        if cached.exists() and not rebuild:
            daily[product] = pd.read_parquet(cached)
            print(f"{product}: cached daily ({len(daily[product]):,} days)")
        else:
            df = prepare.load_raw(aoi, product, raw)
            cl = prepare.clean(df)
            d = prepare.daily_cells(cl, chunk_days=chunk)
            d["product"] = product
            d.to_parquet(cached, index=False)
            daily[product] = d
            print(f"{aoi} / {product}: {len(df):,} raw -> {len(cl):,} clean -> {d.unique_cells.sum():,} cells")

    # Stage 3
    merged, report = harmonize.harmonize_series(daily, aoi)
    report_df = harmonize.build_report(report)
    report_df.to_csv(out_dir / "calibration.csv", index=False)
    print(f"\n[harmonize] {aoi}: {report_df.iloc[0].to_dict()}")

    # Stage 4
    metric = "unique_cells_harmonized"
    cl = cal.climatology(merged)
    cl.to_csv(out_dir / "climatology.csv")
    peaks = cal.peak_season(merged)
    peaks.to_csv(out_dir / "peak_season.csv")
    anom = cal.anomalies(merged)
    anom.to_csv(out_dir / "anomalies.csv")
    grid = cal.calendar_grid(merged)
    grid.to_csv(out_dir / "calendar_grid.csv")

    merged.to_parquet(out_dir / "merged.parquet", index=False)
    overlap = harmonize.overlap_facts(daily["MODIS_SP"], daily["VIIRS_SNPP_SP"])
    (out_dir / "overlap.json").write_text(json.dumps(overlap, indent=2))
    validation = harmonize.validate_calibration(merged)
    (out_dir / "validation.json").write_text(json.dumps(validation, indent=2))
    save_artifacts_meta(aoi, out, merged)
    print(f"[calendar] {aoi}: climatology {len(cl)} weeks, peaks {len(peaks)} years")


def save_artifacts_meta(aoi: str, out: Path, merged: pd.DataFrame):
    dates = pd.to_datetime(merged["acq_date"])
    meta = {
        "aoi": aoi,
        "metric": "unique_cells_harmonized",
        "resolution_h3": 8,
        "products": PRODUCTS,
        "snapshot_start": dates.min().strftime("%Y-%m-%d"),
        "snapshot_end": dates.max().strftime("%Y-%m-%d"),
        "harmonized_days": int(merged["unique_cells_harmonized"].notna().sum()),
        "cell_days": int(merged["unique_cells_harmonized"].fillna(0).sum()),
        "source": "NASA FIRMS MODIS_SP + VIIRS_SNPP_SP",
        "generated_by": "scripts/build_pipeline.py",
    }
    (out / aoi / "meta.json").write_text(json.dumps(meta, indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--aoi", required=True, choices=sorted(AOI_ALIASES))
    p.add_argument("--rebuild", action="store_true", help="force recompute daily")
    args = p.parse_args()
    process(args.aoi, rebuild=args.rebuild)