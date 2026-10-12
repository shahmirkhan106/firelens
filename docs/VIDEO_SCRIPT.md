# FireLens — demo video script

The silent screencast `docs/firelens_demo.mp4` (**78.8 s**, 1920×1080) is built by
`scripts/build_video.py` from the captured screenshots in `docs/shots/`. This file
is the **narration + shot list** to record against it.

- **Primary cut:** read the narration below at a natural pace — it is sized to the
  on-screen durations (~2.7 words/sec) so it lands on the built video.
- **Want a 2–3 minute cut?** Multiply each scene's `seconds` in the `SCENES` list
  at the top of `scripts/build_video.py` by ~1.8, re-run the script, and read the
  same narration with more pauses (the "expanded" paragraphs are optional add-ons).
- On-screen captions are **already baked into** the video; the table below lists
  them so the voiceover can complement, not duplicate, them.

---

## Shot list & narration

| # | Scene (screenshot) | Dur | On-screen caption | Narration |
|---|---|---|---|---|
| 0 | Title card | 5 s | *One continuous fire record from two satellites* | "Fires have been watched from space for twenty-five years — by two different satellites. FireLens makes their records comparable, so a change you see is real fire, not a change of instrument." |
| 1 | `california_compare` | 13 s | The problem: a 2012 sensor break | "MODIS and VIIRS both see the same fires, but VIIRS's pixels are finer, so it reports two to five times more hotspots. Left uncorrected, switching archives in 2012 looks like a sudden explosion of fire. The two satellites overlap for fourteen years — so we can measure that disagreement and correct for it." |
| 2 | `california_calendar` | 11 s | A burning-activity calendar | "The result is one row per year, one square per day, 2001 to 2026. The fire season shows up as a band that drifts down the calendar — and now it means the same thing on both sides of 2012." |
| 3 | `california_climatology` | 9 s | The typical season | "One view shows the typical season: the weekly median, wrapped in a tenth-to-ninetieth percentile band. A narrow band means a predictable season; a wide one means volatility." |
| 4 | `california_season` | 9 s | When the season starts and peaks | "Another tracks when each year's season starts, peaks, and ends — computed from the cumulative curve — so a shift in fire timing is visible directly." |
| 5 | `california_anomalies` | 9 s | Unusual weeks vs history | "Unusual weeks are ranked in units of the local spread — a robust stand-in for standard deviation that a single extreme week can't fool." |
| 6 | `amazon_calendar` | 8 s | Amazon Basin — equatorial, year-round fire | "The same method runs on five regions across five fire regimes. The Amazon burns year-round." |
| 7 | `australia-nsw_calendar` | 8 s | Australia NSW — temperate, Dec–Feb peak | "New South Wales peaks in the southern-hemisphere summer." |
| 8 | `east-siberia_calendar` | 8 s | East Siberia — boreal, short intense summer | "And East Siberia has a short, intense boreal summer." |
| 9 | End card | 6 s | team scikit · NASA FIRMS | "FireLens: twenty-eight million raw detections, harmonized into one record you can trust — where a change you see is real fire, not a change of instrument. Team scikit." |

Word count: **~212 words** → at a measured pace this fills the 78.8 s cut.

---

## If you expand to 2–3 minutes

Add these sentences (one per pause) and lengthen the scene holds:

- **Problem (scene 1):** "A 375-metre pixel is about seven times finer than a one-kilometre pixel, so a finer sensor mechanically finds more hotspots inside the very same fire. Counting raw detections isn't a fair comparison at all."
- **Method (scene 2):** "Before calibrating anything, we re-grid both sensors onto an identical roughly one-kilometre lattice — that alone collapses most of the gap. The calibration step only absorbs the residual."
- **Auditable (scene 2):** "Every artifact keeps the raw MODIS, raw VIIRS, and harmonized series side by side, so the correction can be checked rather than trusted."
- **Coverage (scene 3):** "In practice the harmonized series prefers measured MODIS wherever it exists — VIIRS fills the dates MODIS missed, which is less than one percent of the total signal."
- **Honesty (scene 5):** "One region is a known weakness: North India's crop-residue burning fits our linear model poorly, R-squared under 0.6. We flagged it rather than hiding it."
- **Closing (scene 9):** "Everything is open — the pipeline, the tests, and the interactive app. Run it yourself."

---

## Recording notes

- The video is **silent** by design: record the voiceover in one take while
  watching it, or A/B against per-scene timestamps.
- Match the dark UI (`#0d1117`) if you add title cards; the built ones already do.
- Rebuild visuals after any pipeline re-run so the numbers stay current:

  ```bash
  # API on :8000 and preview on :4173 must be running (see README)
  .venv/bin/python scripts/capture_shots.py     # refresh docs/shots/
  .venv/bin/python scripts/build_video.py       # refresh docs/firelens_demo.mp4
  ```
