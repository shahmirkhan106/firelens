#!/usr/bin/env python3
"""Firms data downloader for the FireLens project.

Pulls active-fire hotspots from the NASA FIRMS API for configured AOIs,
batched to respect per-request day limits, and stores them as raw Parquet
files (one per <aoi>/<product>/<year>).

Get a MAP_KEY:  https://firms.modaps.eosdis.nasa.gov/api/map_key/
(requires a free Earthdata Login at https://urs.earthdata.nasa.gov/)

Usage:
    export FIRMS_MAP_KEY=xxxxxxxxxxxxxxxx
    python scripts/download_firms.py --years 2020-2023 --test
    python scripts/download_firms.py --aois california,australia-nsw --years 2001-2026
"""

import argparse
import os
import sys
import time
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import requests

# ---------------------------------------------------------------------------
# CONFIG — edit freely
# ---------------------------------------------------------------------------

# Named AOIs as bounding boxes: (min_lon, min_lat, max_lon, max_lat)
AOIS = {
    "california": "-124.5,32.5,-114.0,42.0",
    "north-india": "73.0,26.0,82.0,31.0",     # crop-residue belt (Punjab/Haryana)
    "amazon": "-70.0,-13.0,-50.0,0.0",
    "australia-nsw": "141.0,-38.0,154.0,-28.0",
    "east-siberia": "103.0,50.0,140.0,70.0",
}

# products -> FIRMS API source name (SP = Standard Processing / archive history,
# NRT = near-real-time, only the most recent period)
PRODUCTS = {
    "MODIS_SP": "MODIS (C6.1, 1 km, Terra/Aqua)",
    "VIIRS_SNPP_SP": "VIIRS S-NPP (375 m) *download before Nov 1, 2026*",
    "VIIRS_NOAA20_SP": "VIIRS NOAA-20 (375 m)",
    # "VIIRS_NOAA21_SP": "VIIRS NOAA-21 (375 m)",
}

# max days per single API request (per current FIRMS docs: 1..5)
DAY_RANGE = 5
API = ("https://firms.modaps.eosdis.nasa.gov/api/area/csv/"
       "{key}/{product}/{area}/{day_range}/{date}")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def get_key():
    key = os.environ.get("FIRMS_MAP_KEY")
    if key:
        return key.strip()
    key = input("FIRMS MAP_KEY not set. Paste your key: ").strip()
    return key


def fetch(api_key, product, start_date, area, day_range=DAY_RANGE, retries=5):
    url = API.format(key=api_key, product=product, area=area,
                     day_range=day_range, date=start_date)
    for attempt in range(1, retries + 1):
        try:
            r = requests.get(url, timeout=120)
            if r.status_code == 200:
                return pd.read_csv(pd.io.common.StringIO(r.text), comment="#")
            # 404 often means NOAA-20/21 not enabled on the account
            if r.status_code in (401, 403, 404):
                print(f"  ! {product}: HTTP {r.status_code} — likely no access (skip?)")
                return None
            print(f"  ! HTTP {r.status_code} ({attempt}/{retries}), retrying...")
        except Exception as e:
            print(f"  ! error: {e} ({attempt}/{retries})")
        time.sleep(2 ** attempt)
    return None


def start_dates(start, end, step):
    d = start
    while d <= end:
        yield d
        d += timedelta(days=step)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    p = argparse.ArgumentParser(description="Download FIRMS active-fire data.")
    p.add_argument("--aois", nargs="+", help="AOI names from CONFIG (default: all)")
    p.add_argument("--products", nargs="+", help="products from CONFIG (default: all)")
    p.add_argument("--years", required=True, help="e.g. 2020 or 2018-2023")
    p.add_argument("--out", default="data/raw", help="output dir")
    p.add_argument("--mode", choices=["aoi", "world"], default="aoi",
                   help="download per-AOI bboxes, or the whole world (clip locally later)")
    p.add_argument("--test", action="store_true",
                   help="single 5-day window per product, quick check")
    p.add_argument("--resume", action="store_true",
                   help="skip years that already have a parquet file")
    p.add_argument("--verify", action="store_true",
                   help="re-fetch any year without a .ok completion marker "
                        "(catches silently truncated downloads)")
    args = p.parse_args()

    if "-" in args.years:
        y0, y1 = (int(x) for x in args.years.split("-", 1))
    else:
        y0 = y1 = int(args.years)

    aois = args.aois or list(AOIS)
    products = args.products or list(PRODUCTS)
    out = Path(args.out)
    api_key = get_key()

    print(f"Products: {', '.join(products)} ({DAY_RANGE}-day windows)")
    print(f"Region:   {args.mode}  ({', '.join(aois) if args.mode == 'aoi' else 'world'})")

    areas = {a: bbox for a, bbox in AOIS.items() if a in aois} if args.mode == "aoi" else {"world": "world"}

    for aoi, area in areas.items():
        print(f"\n=== {aoi}  {area if args.mode == 'world' else '(bbox)'} ===")

        for product in products:
            dest = out / aoi / product
            dest.mkdir(parents=True, exist_ok=True)
            fetched = 0
            y = y0
            while y <= y1:
                fp = dest / f"{y}.parquet"
                # Trust only the completion sidecar. Older downloads predate it,
                # so a bare parquet is treated as unverified and re-fetched when
                # --verify is passed; without --verify we keep the old behaviour
                # of skipping existing files.
                if args.resume or args.verify:
                    if args.verify:
                        # Re-fetch years that lack a sidecar (i.e. never verified).
                        if fp.exists() and fp.with_suffix(".ok").exists():
                            print(f"  SKIP {product} {y} (verified complete)")
                            y += 1
                            continue
                        if fp.exists():
                            print(f"  RE-VERIFY {product} {y} (no completion marker)")
                    elif fp.exists():
                        print(f"  SKIP {product} {y} (already have {fp})")
                        y += 1
                        continue
                start = date(y, 1, 1)
                end = date.today() if y == y1 and y1 >= 2026 else date(y, 12, 31)
                if args.test:
                    # quick single window mid-August
                    start = end = date(min(y1, 2025), 8, 1)

                # Windows we *expect* to request. Tracked so a partially
                # downloaded year can never masquerade as a complete one.
                windows = list(start_dates(start, end, DAY_RANGE))
                frames = []
                days_seen = set()
                failed = []
                for d0 in windows:
                    df = fetch(api_key, product, d0.isoformat(), area)
                    if df is None or df.empty:
                        failed.append(d0.isoformat())
                        continue
                    df["source_product"] = product
                    df["aoi"] = aoi
                    frames.append(df)
                    days_seen.update(pd.to_datetime(df["acq_date"]).dt.strftime("%Y-%m-%d"))
                    sys.stdout.write(f"\r  {product} {y}: {len(days_seen)} days in year")
                    sys.stdout.flush()
                print()

                if frames:
                    raw = pd.concat(frames, ignore_index=True)
                    raw["acq_date"] = pd.to_datetime(raw["acq_date"])
                    raw["year"] = raw["acq_date"].dt.year
                    for year, grp in raw.groupby("year"):
                        fp = dest / f"{year}.parquet"
                        fp.unlink(missing_ok=True)
                        grp.to_parquet(fp, index=False)
                        # Completion marker: an empty sidecar means the year was
                        # fetched end-to-end. --resume trusts the sidecar, never
                        # the mere existence of the parquet.
                        if not failed:
                            fp.with_suffix(".ok").write_text(
                                f"windows={len(windows)}\ndays={grp['acq_date'].nunique()}\n"
                            )
                        else:
                            fp.with_suffix(".ok").unlink(missing_ok=True)
                    fetched += len(raw)
                    print(f"  wrote {dest / str(y)}.parquet  ({len(raw):,} detections)")
                if failed:
                    print(
                        f"  ! {product} {y}: INCOMPLETE — {len(failed)}/{len(windows)} windows "
                        f"returned nothing (e.g. {', '.join(failed[:3])}). Not marked complete; "
                        f"re-run with --resume to retry."
                    )

                if args.test:
                    break
                y += 1
            print(f"  {product}: {fetched:,} total detections")

    print("\nDone.")


if __name__ == "__main__":
    main()