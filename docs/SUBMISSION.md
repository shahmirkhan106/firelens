# FireLens — Space Apps submission text

Copy each section into the matching form field. The short description is under
140 characters; the high-level summary is a few sentences and can be trimmed if
the form has a tighter limit. Every number is drawn from the committed artifacts
in `data/processed/`.

---

## Project Name

**FireLens — one continuous fire record from two satellites**

## High-Level Summary

NASA's MODIS and VIIRS active-fire archives overlap for 14 years but disagree by
2.3–4.9× because VIIRS's pixels are finer. FireLens measures that disagreement on
the shared days, calibrates VIIRS onto the MODIS scale, and publishes one
continuous burning-activity calendar for five fire regimes. Responders,
scientists, and land managers can compare current burning with a consistent
25-year history instead of a record that jumps when the satellite changes.

## Short description (≤ ~140 chars)

One fire record from two satellites: MODIS + VIIRS harmonized across the 2012 sensor change, so a change you see is real change.

## Project Details

NASA FIRMS publishes active-fire hotspots from two instruments with very
different footprints: **MODIS** (1 km, 2001→2026) and **VIIRS** (375 m,
2012→2026). Because VIIRS's pixels are finer, it reports **2.3× to 4.9×** more
distinct H3 fire cells than MODIS for the *same fires*. Left uncorrected, any
long-term fire dataset invents a **fictional spike in 2012**: activity appears to
explode the moment the satellite changes, even when nothing changed on the
ground.

FireLens fixes this the honest way. The two archives **overlap for ~14 years**,
so instead of guessing at a correction, we *measure* it: for every region we fit
VIIRS onto the MODIS scale using only the days both instruments observed the same
ground. The result is a single "MODIS-equivalent" burning-activity series from
2001 through 30 June 2026, where year-over-year change reflects **real change in
detected fire activity**.

We processed **28.3 million** raw detections across **five regions** chosen to
span five fire regimes — California (Mediterranean), North India (monsoon
crop-residue), the Amazon Basin (equatorial), Australia NSW (temperate), and East
Siberia (boreal) — producing **42,949** harmonized region-days and **6,910,569**
cell-days. In-sample calibration R² is **0.90–0.95** for genuine wildfire; the one
weak region (North India crop burning, R² **0.586**) is flagged rather than hidden.

Everything is open: a reproducible Python pipeline, a FastAPI backend, an
interactive React calendar app with five analysis views, and a **24-test suite**.

### Impact

- **Emergency responders** can compare current burning with a consistent
  historical median and see when a region is outside its normal range.
- **Scientists** get an auditable, open, MODIS-equivalent daily series rather
  than an uncorrected splice or a dropped sensor.
- **Land managers** can identify critical periods, unusual weeks, and season
  timing, and export the harmonized data as CSV for their own tools.
- **Next steps:** near-real-time/NOAA-20 ingestion, a true custom-AOI pipeline,
  and a regime-aware calibration for crop-residue burning.

### Validation and honest limits

The headline calibration R² is in-sample. We also report two out-of-sample checks:
leave-one-year-out (refit without each overlap year, predict it) and a forward
holdout (fit 2012–2020, test 2021–2025). Median leave-one-year-out R² ranges from
**0.586 (North India)** to **0.932 (East Siberia)**; the forward R² ranges from
**0.599 to 0.954**. The numbers are committed in each region's `validation.json`
and shown in the app.

Known limits: MODIS is the reference scale, so the output is explicitly
"MODIS-equivalent"; the committed data snapshot ends **30 June 2026**; the map
picker snaps a drawn area to the nearest of five precomputed regions; and the
single linear fit is weakest for North India's crop-residue regime.

## How It Works

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

## The App

Five toggleable views, each with a "What am I looking at?" explainer: **Why
harmonize** (raw vs harmonized across the overlap), **Calendar** (one row per
year), **Typical season** (median + p10–p90 band), **Season timing** (per-year
start/peak/end), and **Unusual weeks** (robust anomalies). A Leaflet map lets a
user draw an area and snap to the nearest processed region; the app says
explicitly that this is not an on-demand custom-area download. Every view has a
view-specific CSV export.

## What's Novel

- The correction is **fitted on measured overlap**, not assumed — and stored
  alongside the raw data so it can be checked, not trusted.
- **Robust statistics** (p10–p90 spread instead of σ) make an "unusual week"
  score mean the same thing in a stable region and a volatile one.
- **Honest scope**: both failure modes (uncorrected splice, dropped sensor) are
  rejected, the weakest region is reported, and out-of-sample validation is
  committed next to the fit.

## NASA Data / Partner Data

- **NASA FIRMS — MODIS C6.1 active fire (1 km):**
  https://firms.modaps.eosdis.nasa.gov/active_fire/ and MOD14 product page
  https://modis.gsfc.nasa.gov/data/dataprod/mod14.php
- **NASA FIRMS — VIIRS S-NPP active fire (375 m):**
  VNP14IMG product page
  https://ladsweb.modaps.eosdis.nasa.gov/missions-and-measurements/products/VNP14IMG/
- **NASA FIRMS API (source of the archives):** https://firms.modaps.eosdis.nasa.gov/api/
- Products used: `MODIS_SP`, `VIIRS_SNPP_SP` (archives 2001–2026; committed
  snapshot through 30 June 2026). The S-NPP archive ended 1 November 2026.
- Meaningful use: both products are downloaded, cleaned, H3-gridded, calibrated
  against each other on their overlap, and published as one auditable record —
  not used as decoration or a token citation.

## Data & Tools

- **Data:** NASA FIRMS — MODIS C6.1 (1 km) and VIIRS S-NPP (375 m), 2001→2026
  (snapshot through 30 June 2026).
- **Stack:** Python (pandas, NumPy, PyArrow, H3), FastAPI, React + Vite.
- **Tests:** 23 passing (`pytest`), plus a raw-data integrity guard.
- **AI/SI:** disclosed below.

## Team

- M. Shahmir Khan

## Use of AI/SI (required disclosure)

This project was developed with AI assistance:

- **Code generation & debugging:** GitHub Copilot / Claude (Anthropic) used for
  writing Python pipeline code, FastAPI endpoints, React components, test suite,
  and build scripts.
- **Documentation:** README, deck, video script, and submission text drafted with
  AI assistance, then reviewed and edited by the team.
- **No AI-generated images or video:** all screenshots, charts, and the demo video
  are captured from the running application (real code output). The video was
  assembled programmatically via `scripts/build_video.py` using real screenshots.
  No visible AI watermark is required because no AI-generated media is included,
  and no NASA branding is used in AI-assisted content.
- **No AI-generated data:** all fire data comes directly from NASA FIRMS (MODIS
  C6.1, VIIRS S-NPP); the pipeline is deterministic and fully reproducible.
- **No personal media:** no photos, voices, addresses, or phone numbers are
  included. Team names are used only for credit.

The team reviewed, tested, and takes full responsibility for all submitted code
and outputs.

## Links

- **Project Demo (hosted video):** https://youtu.be/RYlbIDoLuQQ (28 seconds)
- **Final Project (code):** https://github.com/shahmirkhan106/firelens
- **7-slide demo deck:**
  https://github.com/shahmirkhan106/firelens/blob/main/docs/DEMO_DECK.md
- **Full narrative deck (supplementary):**
  https://github.com/shahmirkhan106/firelens/blob/main/docs/DECK.md
- **License:** MIT — https://github.com/shahmirkhan106/firelens/blob/main/LICENSE

## References

- NASA FIRMS — https://firms.modaps.eosdis.nasa.gov/ · API —
  https://firms.modaps.eosdis.nasa.gov/api/ · active-fire products —
  https://firms.modaps.eosdis.nasa.gov/active_fire/
- NASA MODIS MOD14/MYD14 product — https://modis.gsfc.nasa.gov/data/dataprod/mod14.php
- NASA VIIRS VNP14IMG product —
  https://ladsweb.modaps.eosdis.nasa.gov/missions-and-measurements/products/VNP14IMG/
- NASA Earthdata Login — https://urs.earthdata.nasa.gov/
- Uber H3 geospatial indexing — https://h3geo.org/
- FastAPI — https://fastapi.tiangolo.com/ · Uvicorn — https://www.uvicorn.org/ ·
  Starlette — https://www.starlette.io/ · Pydantic — https://docs.pydantic.dev/
- React — https://react.dev/ · React DOM — https://react.dev/ ·
  Vite — https://vite.dev/ · @vitejs/plugin-react —
  https://github.com/vitejs/vite-plugin-react
- Leaflet — https://leafletjs.com/ · Leaflet.draw —
  https://github.com/Leaflet/Leaflet.draw
- OpenStreetMap tiles — https://www.openstreetmap.org/ · copyright/attribution —
  https://www.openstreetmap.org/copyright · tile usage policy —
  https://operations.osmfoundation.org/policies/tiles/
- pandas — https://pandas.pydata.org/ · NumPy — https://numpy.org/ ·
  PyArrow — https://arrow.apache.org/docs/python/ · requests —
  https://requests.readthedocs.io/
- Playwright — https://playwright.dev/ · FFmpeg — https://ffmpeg.org/ ·
  Pillow — https://python-pillow.org/ · DejaVu fonts —
  https://dejavu-fonts.github.io/
- pytest — https://pytest.org/ · HTTPX — https://www.python-httpx.org/
- NASA Space Apps Challenge — https://www.spaceappschallenge.org/
- AI/SI tools: GitHub Copilot and Claude (Anthropic), used as described in the
  disclosure above.

## Tags

`NASA FIRMS` · `MODIS` · `VIIRS` · `active fire` · `data harmonization` ·
`remote sensing` · `H3 geospatial` · `wildfire` · `time series` · `open data`
