# FireLens — Space Apps submission text

Copy the sections below into the submission form. Adjust wording to fit any
character limits; the numbers are drawn from the built artifacts in
`data/processed/`.

---

## Title

**FireLens — one continuous fire record from two satellites**

## Short description (≤ ~140 chars)

A burning-activity calendar that harmonizes NASA's MODIS and VIIRS fire hotspots
across the 2012 sensor change, so a change you see is real fire — not a change of
satellite.

## Full project description

NASA FIRMS publishes active-fire hotspots from two instruments with very
different footprints: **MODIS** (1 km, 2001→present) and **VIIRS** (375 m,
2012→present). Because VIIRS's pixels are finer, it mechanically reports **2.3×
to 4.9×** more distinct fire cells than MODIS for the *same fires*. Left
uncorrected, any long-term fire dataset invents a **fictional spike in 2012**:
activity appears to explode the moment the satellite changes, even when nothing
changed on the ground.

FireLens fixes this the honest way. The two archives **overlap for ~14 years**,
so instead of guessing at a correction, we *measure* it: for every region we fit
VIIRS onto the MODIS scale using only the days both instruments observed the same
ground. The result is a single "MODIS-equivalent" burning-activity series from
2001 to today, where year-over-year change reflects real fire.

We processed **28.3 million** raw detections across **five regions** chosen to
span five fire regimes — California (Mediterranean), North India (monsoon
crop-residue), the Amazon Basin (equatorial), Australia NSW (temperate), and East
Siberia (boreal) — producing **42,949** harmonized region-days and **6,910,569**
cell-days. Calibration R² is **0.90–0.95** for genuine wildfire; the one weak
region (North India crop burning, R² **0.59**) is flagged rather than hidden.

Everything is open: a reproducible Python pipeline, a FastAPI backend, an
interactive React calendar app with five analysis views, and a 20-test suite.

## How it works

1. **Clean** — confidence thresholds, remove volcano/static-offshore types, drop
   zero/negative FRP.
2. **Grid** — project every detection onto a common **~1 km H3** lattice so pixel
   size no longer drives the count (this alone collapses most of the gap).
3. **Calibrate** — OLS `MODIS ~ a + b·VIIRS` fitted on the 2012→present overlap;
   every day MODIS observed keeps its measured value, MODIS gaps fall back to
   calibrated VIIRS. Raw MODIS, raw VIIRS, and harmonized series are stored side
   by side so the correction stays auditable.
4. **Calendar** — weekly climatology (p10/median/p90), robust anomaly scores in
   units of the local p10–p90 spread, per-year season start/peak/end, and a
   year×day heatmap grid.

## The app

Five toggleable views, each with a "What am I looking at?" explainer: **Why
harmonize** (raw vs harmonized across the overlap), **Calendar** (one row per
year), **Typical season** (median + p10–p90 band), **Season timing** (per-year
start/peak/end), and **Unusual weeks** (robust anomalies).

## What's novel

- The correction is **fitted on measured overlap**, not assumed — and stored
  alongside the raw data so it can be checked, not trusted.
- **Robust statistics** (p10–p90 spread instead of σ) make an "unusual week"
  score mean the same thing in a stable region and a volatile one.
- **Honest scope**: the two failure modes (uncorrected splice, dropped sensor)
  are both rejected, and the weakest region is reported, not buried.

## Data & tools

- **Data:** NASA FIRMS — MODIS C6.1 (1 km) and VIIRS S-NPP (375 m), 2001→present.
- **Stack:** Python (pandas, numpy, pyarrow, **H3**), FastAPI, React + Vite.
- **Tests:** 20 passing (`pytest`), plus a raw-data integrity guard.

## Team — scikit

- M. Shahmir Khan
- Ahmed Bilal
- Abbas Bajwa
- Azwar Khan
- Sajid Islam

## Links

- **Code:** https://github.com/shahmirkhan106/firelens
- **Demo video:** `docs/firelens_demo.mp4` (in repo)
- **Deck:** `docs/DECK.md`

## Tags

`NASA FIRMS` · `MODIS` · `VIIRS` · `active fire` · `data harmonization` ·
`remote sensing` · `H3 geospatial` · `wildfire` · `time series` · `open data`
