# FireLens — 28-second demo video script

Hosted: https://youtu.be/Iy_iHQV19bk

Submission-compliant cut: **28 seconds**, silent with on-screen captions (within
the 30-second project-demo limit). Narration is optional and is provided below if
a voiceover is added.

## Narration (~70 words, ~28s at a natural pace)

> Two NASA satellites have watched Earth's fires for 25 years. But when VIIRS
> joined MODIS in 2012, raw fire counts jumped two to five times — a sensor
> change, not a fire change. FireLens measures the overlap, fits VIIRS onto the
> MODIS scale, and rebuilds one continuous burning-activity calendar. Five
> regions. One defensible record. A change you see is real change in detected
> fire activity — not a change of instrument.

## Shot list

| Time | Visual | Caption |
|---|---|---|
| 0:00–0:03 | Title card | One continuous fire record from two satellites |
| 0:03–0:09 | `california_compare.png` | The problem: a 2012 sensor break — raw MODIS + VIIRS cells jump 2.3–4.9× when the sensor changes |
| 0:09–0:15 | `california_calendar.png` | A burning-activity calendar: one row per year, one square per day, 2001–June 2026 |
| 0:15–0:20 | `california_anomalies.png` | Unusual weeks vs the region's own history, using robust p10–p90 anomalies |
| 0:20–0:24 | `amazon_calendar.png` | Five fire regimes: Amazon, NSW, Siberia, California, North India |
| 0:24–0:28 | End card | FireLens — M. Shahmir Khan · NASA FIRMS MODIS + VIIRS · GitHub |

## Build

```bash
python scripts/build_video.py
# -> docs/firelens_demo.mp4 (1920x1080, H.264, 28s)
```

The video is assembled from real screenshots captured by
`scripts/capture_shots.py`; no AI-generated imagery or data is used.
