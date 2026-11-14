# FireLens — Space Apps submission text

Copy the sections below into the submission form. Adjust wording to fit any
character limits; the numbers are drawn from the built artifacts in
`data/processed/`.

---

## Title

**FireLens — one continuous fire record from two satellites**

## Short description (≤ ~140 chars)

One fire record from two satellites: MODIS + VIIRS harmonized across the 2012 sensor change, so a change you see is real fire.

## Full project description

NASA FIRMS publishes active-fire hotspots from two instruments with very
different footprints: **MODIS** (1 km, 2001→2026) and **VIIRS** (375 m,
2012→2026). Because VIIRS's pixels are finer, it mechanically reports **2.3×
to 4.9×** more distinct fire cells than MODIS for the *same fires*. Left
uncorrected, any long-term fire dataset invents a **fictional spike in 2012**:
activity appears to explode the moment the satellite changes, even when nothing
changed on the ground.

FireLens fixes this the honest way. The two archives **overlap for ~14 years**,
so instead of guessing at a correction, we *measure* it: for every region we fit
VIIRS onto the MODIS scale using only the days both instruments observed the same
ground. The result is a single "MODIS-equivalent" burning-activity series from
2001 through 30 June 2026, where year-over-year change reflects real fire.

We processed **28.3 million** raw detections across **five regions** chosen to
span five fire regimes — California (Mediterranean), North India (monsoon
crop-residue), the Amazon Basin (equatorial), Australia NSW (temperate), and East
Siberia (boreal) — producing **42,949** harmonized region-days and **6,910,569**
cell-days. Calibration R² is **0.90–0.95** for genuine wildfire; the one weak
region (North India crop burning, R² **0.59**) is flagged rather than hidden.

Everything is open: a reproducible Python pipeline, a FastAPI backend, an
interactive React calendar app with five analysis views, and a 21-test suite.

## How it works

1. **Clean** — confidence thresholds, remove volcano/static-offshore types, drop
   zero/negative FRP.
2. **Grid** — project every detection onto a common **~1 km H3** lattice so pixel
   size no longer drives the count (this alone collapses most of the gap).
3. **Calibrate** — OLS `MODIS ~ a + b·VIIRS` fitted on the 2012–2026 overlap;
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

## NASA Data / Partner Data

- **NASA FIRMS — MODIS C6.1 active fire (1 km):** https://firms.modaps.eosdis.nasa.gov/
- **NASA FIRMS — VIIRS S-NPP active fire (375 m):** https://firms.modaps.eosdis.nasa.gov/
- Products used: `MODIS_SP`, `VIIRS_SNPP_SP` (archives, 2001–2026; snapshot through 30 June 2026).

## Data & tools

- **Data:** NASA FIRMS — MODIS C6.1 (1 km) and VIIRS S-NPP (375 m), 2001→2026 (snapshot through 30 June 2026).
- **Stack:** Python (pandas, numpy, pyarrow, **H3**), FastAPI, React + Vite.
- **Tests:** 21 passing (`pytest`), plus a raw-data integrity guard.

## Team — scikit

- M. Shahmir Khan
- Ahmed Bilal
- Abbas Bajwa
- Azwar Khan
- Sajid Islam

## Use of AI/SI (required disclosure)

This project was developed with AI assistance:

- **Code generation & debugging**: GitHub Copilot / Claude (Anthropic) used for writing Python pipeline code, FastAPI endpoints, React components, test suite, and build scripts.
- **Documentation**: README, deck, video script, and submission text drafted with AI assistance, then reviewed and edited by the team.
- **No AI-generated images or video**: All screenshots, charts, and the demo video are captured from the running application (real code output). The video was assembled programmatically via `scripts/build_video.py` using real screenshots.
- **No AI-generated data**: All fire data comes directly from NASA FIRMS (MODIS C6.1, VIIRS S-NPP); the pipeline is deterministic and fully reproducible.

The team reviewed, tested, and takes full responsibility for all submitted code and outputs.

## Links

- **Final project / code:** https://github.com/shahmirkhan106/firelens
- **30-second demo video:** `docs/firelens_demo.mp4` — upload to YouTube (Unlisted) and paste the URL here. **YouTube URL: TBD**
- **7-slide demo deck:** `docs/DEMO_DECK.md`
- **Full narrative deck:** `docs/DECK.md`

## References

- NASA FIRMS active-fire archive — https://firms.modaps.eosdis.nasa.gov/
- MODIS C6.1 / VIIRS S-NPP standard-processing products (`MODIS_SP`, `VIIRS_SNPP_SP`).
- Uber H3 geospatial indexing — https://h3geo.org/
- FastAPI — https://fastapi.tiangolo.com/ · Uvicorn — https://www.uvicorn.org/
- React — https://react.dev/ · Vite — https://vite.dev/
- Leaflet — https://leafletjs.com/ · OpenStreetMap tiles — https://www.openstreetmap.org/
- pandas — https://pandas.pydata.org/ · NumPy — https://numpy.org/ · PyArrow — https://arrow.apache.org/docs/python/
- Playwright — https://playwright.dev/ · FFmpeg — https://ffmpeg.org/ · Pillow — https://python-pillow.org/
- pytest — https://pytest.org/ · HTTPX — https://www.python-httpx.org/
- AI/SI tools: GitHub Copilot and Claude (Anthropic), used as described in the disclosure above.

## Tags

`NASA FIRMS` · `MODIS` · `VIIRS` · `active fire` · `data harmonization` ·
`remote sensing` · `H3 geospatial` · `wildfire` · `time series` · `open data`
