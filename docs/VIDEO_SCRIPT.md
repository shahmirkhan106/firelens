# FireLens — 30-second demo video script

Submission-compliant cut: **28 seconds**, silent with on-screen captions (the
30-second limit applies to the project demo video). Narration is optional and is
provided below if a voiceover is added.

## Narration (~70 words, ~28s at a natural pace)

> Two NASA satellites have watched Earth's fires for 25 years. But when VIIRS
> joined MODIS in 2012, raw fire counts jumped two to five times — a sensor
> change, not a fire change. FireLens measures the overlap, fits VIIRS onto the
> MODIS scale, and rebuilds one continuous burning-activity calendar. Five
> regions. One defensible record. A change you see is real fire — not a change
> of instrument.

## Shot list

| Time | Visual | Caption |
|---|---|---|
| 0:00–0:03 | Title card | One continuous fire record from two satellites |
| 0:03–0:10 | `california_compare.png` | The problem: a 2012 sensor break — raw MODIS + VIIRS counts jump 2–5× when the sensor changes |
| 0:10–0:16 | `california_calendar.png` | A burning-activity calendar: one row per year, one square per day, 2001–2026 |
| 0:16–0:21 | `california_anomalies.png` | Unusual weeks vs the region's own history, using robust p10–p90 anomalies |
| 0:21–0:26 | `amazon_calendar.png` | Five fire regimes: Amazon, NSW, Siberia, California, North India |
| 0:26–0:30 | End card | FireLens — team scikit · NASA FIRMS MODIS + VIIRS · GitHub |

## Build

```bash
python scripts/build_video.py
# -> docs/firelens_demo.mp4 (1920x1080, H.264, 28s)
```

The video is assembled from real screenshots captured by
`scripts/capture_shots.py`; no AI-generated imagery or data is used.
