#!/usr/bin/env python3
"""Quick check: raw detection counts vs unique H3 fire cells per sensor.

Purpose: demonstrate the VIIRS inflation artifact on real data and show
that gridding to a common H3 resolution collapses most of it.
"""

from pathlib import Path

import h3
import pandas as pd

RAW = Path("data/raw")
H3_RES = 8  # ~0.7 km² cells, near MODIS 1 km footprint

rows = []
for product in ["MODIS_SP", "VIIRS_SNPP_SP"]:
    for fp in sorted((RAW / "california" / product).glob("*.parquet")):
        df = pd.read_parquet(fp)
        df = df[df["acq_date"] == df["acq_date"].max()]  # only the test day(s)
        for day, grp in df.groupby("acq_date"):
            cells = grp.apply(
                lambda r: h3.latlng_to_cell(r["latitude"], r["longitude"], H3_RES), axis=1
            )
            rows.append({
                "acq_date": pd.Timestamp(day),
                "product": product,
                "raw_detections": len(grp),
                "unique_fire_cells": cells.nunique(),
                "total_frp_mw": grp["frp"].sum(),
            })

summary = pd.DataFrame(rows).sort_values(["acq_date", "product"])
print(summary.to_string(index=False))
print()

wide = summary.pivot(index="acq_date", columns="product", values="raw_detections")
wide.columns = ["raw_modis", "raw_viirs"]
wide["raw_ratio"] = wide["raw_viirs"] / wide["raw_modis"]

cells = summary.pivot(index="acq_date", columns="product", values="unique_fire_cells")
cells.columns = ["cells_modis", "cells_viirs"]
cells["cell_ratio"] = cells["cells_viirs"] / cells["cells_modis"]

out = wide.join(cells)
print(out.to_string())
print()
print("Inflation (raw detections):  VIIRS ≈ %.2fx MODIS" % out["raw_ratio"].mean())
print("After gridding (unique cells): VIIRS ≈ %.2fx MODIS" % out["cell_ratio"].mean())