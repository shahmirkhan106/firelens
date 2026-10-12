"""Stage 1-2: clean detections, grid to H3, produce daily per-cell aggregates."""
from pathlib import Path

import h3
import pandas as pd

# FIRMS `type`: 0=unknown/vegetation, 2=active volcano, 3=static/offshore
REMOVE_TYPES = {2, 3}
H3_RES = 8

# MODIS confidence is numeric 0-100; drop < 25 (FIRMS recommended for daytime)
MODIS_CONF_MIN = 25
# VIIRS confidence is l/n/h; drop "low"
VIIRS_DROP_CONF = {"l"}


def load_raw(aoi: str, product: str, raw_dir: Path) -> pd.DataFrame:
    frames = []
    for fp in sorted((raw_dir / aoi / product).glob("*.parquet")):
        frames.append(pd.read_parquet(fp))
    if not frames:
        raise FileNotFoundError(f"no raw data for {aoi}/{product}")
    df = pd.concat(frames, ignore_index=True)
    df["acq_date"] = pd.to_datetime(df["acq_date"])
    df["doy"] = df["acq_date"].dt.dayofyear
    df["year"] = df["acq_date"].dt.year
    return df


def clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df[~df["type"].isin(REMOVE_TYPES)]
    conf = df["confidence"]
    if pd.api.types.is_string_dtype(conf):
        df = df[~conf.str.lower().isin(VIIRS_DROP_CONF)]
    elif pd.api.types.is_numeric_dtype(conf):
        df = df[conf.astype(float) >= MODIS_CONF_MIN]
    df = df[df["frp"] > 0]  # some rows carry NaN/0 FRP
    return df.reset_index(drop=True)


def _cell(lat, lon, res=H3_RES):
    return h3.latlng_to_cell(lat, lon, res)


def daily_cells(df: pd.DataFrame, res: int = H3_RES, chunk_days=None) -> pd.DataFrame:
    """Unique fire cells + FRP sum per day (the harmonization base metric).

    Processes in memory-friendly chunks when chunk_days is set (e.g. a year)
    to avoid blowing RAM on very large AOIs (Amazon ~7M detections).
    """
    df = df.copy()
    if chunk_days is None:
        return _daily_cells_one(df, res)
    parts = []
    for _, grp in df.groupby(df["acq_date"].dt.to_period("Y")):
        parts.append(_daily_cells_one(grp, res))
    out = pd.concat(parts, ignore_index=True)
    return out


def _daily_cells_one(df: pd.DataFrame, res: int) -> pd.DataFrame:
    df["cell"] = df.apply(lambda r: h3.latlng_to_cell(r["latitude"], r["longitude"], res), axis=1)
    g = df.groupby(["acq_date", "cell"]).agg(frp_sum=("frp", "sum"))
    out = g.reset_index().groupby("acq_date").agg(
        unique_cells=("cell", "count"),
        frp_mw=("frp_sum", "sum"),
        n_overpasses=("acq_date", "count"),
    )
    return out.reset_index()


def pipeline_to_daily(aoi: str, products, raw_dir: Path) -> dict[str, pd.DataFrame]:
    daily = {}
    for product in products:
        raw = load_raw(aoi, product, raw_dir)
        cl = clean(raw)
        d = daily_cells(cl)
        d["product"] = product
        daily[product] = d
        print(f"{aoi} / {product}: {len(raw):,} raw -> {len(cl):,} clean -> {d.unique_cells.sum():,} cells")
    return daily


def save_daily(daily: dict[str, pd.DataFrame], out_dir: Path, aoi: str):
    dest = out_dir / aoi
    dest.mkdir(parents=True, exist_ok=True)
    for product, df in daily.items():
        df.to_parquet(dest / f"{product}.parquet", index=False)


def load_daily(aoi: str, out_dir: Path) -> dict[str, pd.DataFrame]:
    dest = out_dir / aoi
    return {p.stem: pd.read_parquet(p) for p in sorted(dest.glob("*.parquet"))}