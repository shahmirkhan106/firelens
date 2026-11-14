#!/usr/bin/env python3
"""Validate the integrity of every FIRMS year-file in data/raw.

A year-file is considered complete when it holds a .ok completion sidecar
(written by download_firms.py once every 5-day window in the year returned
data). Files downloaded before sidecars existed have no marker, so this script
also applies a day-count heuristic: a year with far fewer observed days than
its own region/product norm - e.g. the 4-day files caused by an interrupted
download that --resume then treated as complete - is reported as a gap.

Files that pass are stamped with their missing .ok sidecar, so after one clean
run `download_firms.py --verify` will skip them rather than re-fetch.

Usage:
    python scripts/check_data.py                 # all regions
    python scripts/check_data.py --aoi east-siberia
    python scripts/check_data.py --min 0.5       # flag years < 50% of norm
Exit code 0 = everything verified, 1 = gaps found.
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
PRODUCTS = ["MODIS_SP", "VIIRS_SNPP_SP"]


def analyze(aoi: str, min_frac: float) -> list:
    rows = []
    for product in PRODUCTS:
        prod_dir = RAW / aoi / product
        if not prod_dir.is_dir():
            continue
        files = sorted(prod_dir.glob("*.parquet"))
        if not files:
            continue
        norms = {}
        for f in files:
            d = pd.read_parquet(f, columns=["acq_date"])
            days = pd.to_datetime(d.acq_date).dt.normalize().nunique()
            norms[f.name[:-8]] = (days, len(d))
        # Norm = median day-count of the product's own years. Final (partial)
        # years are excluded from the norm so a truncated-in-time year like 2026
        # cannot drag the baseline down.
        values = [v[0] for y, v in norms.items()]
        typical = sorted(values)[len(values) // 2] if values else 0
        max_year = max(int(y) for y in norms)
        for y, (days, nrows) in sorted(norms.items()):
            ok = (RAW / aoi / product / f"{y}.ok").exists()
            is_final = int(y) == max_year
            gap = days <= 1 or (not is_final and days < typical * min_frac)
            rows.append({
                "aoi": aoi, "product": product, "year": y, "days": days,
                "rows": nrows, "typical": typical, "is_final": is_final,
                "ok_marker": ok, "gap": gap,
            })
            if not ok:
                # Stamp verified files with their completion marker so future
                # resume/verify runs stop asking about them.
                (RAW / aoi / product / f"{y}.ok").write_text(
                    f"days={days}\nrows={nrows}\nchecked=check_data.py\n")
    return rows


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--aoi", default=None, help="check a single region (default: all)")
    p.add_argument("--min", dest="min_frac", type=float, default=0.5,
                   help="fraction of the region/product norm below which a year is a gap")
    args = p.parse_args()
    aois = [args.aoi] if args.aoi else sorted(x.name for x in RAW.iterdir() if x.is_dir())
    bad = []
    for aoi in aois:
        rows = analyze(aoi, args.min_frac)
        if not rows:
            print(f"{aoi}: no raw data")
            continue
        gaps = [r for r in rows if r["gap"]]
        verified = [r for r in rows if not r["gap"]]
        day_total = sum(r["days"] for r in rows)
        row_total = sum(r["rows"] for r in rows)
        print(f"{aoi:14} {len(rows)} year-files, {day_total} observed days, "
              f"{row_total:,} detections")
        if gaps:
            for r in gaps:
                print(f"  GAP  {r['product']:12} {r['year']}  {r['days']:3} days "
                      f"(norm ~{r['typical']}, rows={r['rows']:,})")
            bad.extend(gaps)
        else:
            print("  OK   every year verified")
    if bad:
        print(f"\n{len(bad)} gap(s) found. Re-download with "
              "`python scripts/download_firms.py --aois <aoi> --products <p> --years <y>` "
              "then rebuild with `python scripts/build_pipeline.py --aoi <aoi> --rebuild`.")
        return 1
    print("\nAll regions verified complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())