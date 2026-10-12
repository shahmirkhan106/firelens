#!/usr/bin/env python3
"""Assemble the silent FireLens demo screencast from the captured screenshots.

Narration lives in docs/VIDEO_SCRIPT.md; this renders the visuals (title cards,
captioned screenshots, end card) and crossfades them into one H.264 mp4 so the
team can record a voiceover against it (or use it as a storyboard).

    python scripts/build_video.py      ->  docs/firelens_demo.mp4
"""
import shutil
import subprocess
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
SHOTS = ROOT / "docs" / "shots"
WORK = ROOT / "docs" / "video" / "_work"
OUT = ROOT / "docs" / "firelens_demo.mp4"
W, H, FPS = 1920, 1080, 30
BG = (13, 17, 23)
FG = (230, 237, 243)
MUTED = (139, 148, 158)
ACCENT = (240, 136, 62)
BAR = 170
FONT_B = "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf"
FONT_R = "/usr/share/fonts/TTF/DejaVuSans.ttf"

# (image | "TITLE" | "END", seconds, title, caption)
SCENES = [
    ("TITLE", 5, "", "One continuous fire record from two satellites"),
    ("california_compare", 13, "The problem: a 2012 sensor break",
     "MODIS ends, VIIRS begins; raw counts jump 2-5x with no change on the ground"),
    ("california_calendar", 11, "A burning-activity calendar",
     "One trustworthy row per year, 2001 to 2026"),
    ("california_climatology", 9, "The typical season",
     "Median week-by-week activity with a p10-p90 band"),
    ("california_season", 9, "When the season starts and peaks",
     "Cumulative 20 / 50 / 90 percent timing for every year"),
    ("california_anomalies", 9, "Unusual weeks vs the region's history",
     "Robust p10-p90 spread, not a fragile standard deviation"),
    ("amazon_calendar", 8, "Amazon Basin", "Equatorial, year-round fire"),
    ("australia-nsw_calendar", 8, "Australia NSW", "Temperate, December-February peak"),
    ("east-siberia_calendar", 8, "East Siberia", "Boreal, short intense summer"),
    ("END", 6, "", "M. Shahmir Khan | Ahmed Bilal | Abbas Bajwa | Azwar Khan | Sajid Islam"),
]


def font(path, size):
    return ImageFont.truetype(path, size)


def wrap(draw, text, fnt, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = f"{cur} {w}".strip()
        if draw.textlength(t, font=fnt) <= maxw:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def centered(draw, y, text, fnt, fill):
    tw = draw.textlength(text, font=fnt)
    draw.text(((W - tw) / 2, y), text, font=fnt, fill=fill)


def title_frame():
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    centered(d, 380, "FireLens", font(FONT_B, 160), FG)
    centered(d, 580, "One continuous fire record from two satellites", font(FONT_R, 46), ACCENT)
    centered(d, 660, "MODIS C6.1 + VIIRS S-NPP, harmonized on a ~1 km H3 grid", font(FONT_R, 34), MUTED)
    return im


def end_frame(caption):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    centered(d, 340, "FireLens - team scikit", font(FONT_B, 76), FG)
    centered(d, 450, caption, font(FONT_R, 34), FG)
    centered(d, 540, "Data: NASA FIRMS (MODIS + VIIRS)", font(FONT_R, 34), ACCENT)
    centered(d, 610, "github.com/shahmirkhan106/firelens", font(FONT_R, 30), MUTED)
    return im


def shot_frame(img_name, title, caption):
    im = Image.new("RGB", (W, H), BG)
    shot = Image.open(SHOTS / f"{img_name}.png").convert("RGB")
    avail_w, avail_h = 1840, H - BAR - 40
    scale = min(avail_w / shot.width, avail_h / shot.height)
    shot = shot.resize((int(shot.width * scale), int(shot.height * scale)), Image.LANCZOS)
    im.paste(shot, ((W - shot.width) // 2, 24))
    d = ImageDraw.Draw(im)
    d.rectangle([0, H - BAR, W, H], fill=(10, 14, 20))
    d.rectangle([0, H - BAR, W, H - BAR + 3], fill=ACCENT)
    d.text((60, H - BAR + 26), title, font=font(FONT_B, 44), fill=FG)
    cf = font(FONT_R, 30)
    y = H - BAR + 90
    for line in wrap(d, caption, cf, W - 120):
        d.text((60, y), line, font=cf, fill=MUTED)
        y += 38
    return im


def main():
    if not SHOTS.is_dir():
        raise SystemExit(f"no screenshots at {SHOTS}; run scripts/capture_shots.py first")
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)
    segs = []
    for i, (img, secs, title, caption) in enumerate(SCENES):
        if img == "TITLE":
            frame = title_frame()
        elif img == "END":
            frame = end_frame(caption)
        else:
            frame = shot_frame(img, title, caption)
        png = WORK / f"{i:02d}.png"
        frame.save(png)
        seg = WORK / f"{i:02d}.mp4"
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-loop", "1", "-i", str(png),
             "-t", str(secs), "-r", str(FPS), "-c:v", "libx264",
             "-pix_fmt", "yuv420p", str(seg)], check=True)
        segs.append(seg)
        print(f"  scene {i:02d} {img:22} {secs}s")

    # Crossfade chain: each xfade consumes the previous concat plus one segment.
    dur = [s[1] for s in SCENES]
    inputs = []
    for s in segs:
        inputs += ["-i", str(s)]
    fade = 0.8
    parts, prev, acc = [], "[0:v]", dur[0]
    for j in range(1, len(segs)):
        off = round(acc - fade, 3)
        out = f"[v{j}]"
        parts.append(
            f"{prev}[{j}:v]xfade=transition=fade:duration={fade}:offset={off}{out}")
        prev = out
        acc = round(acc + dur[j] - fade, 3)
    filt = ";".join(parts)
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", filt,
         "-map", prev, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
         str(OUT)], check=True)
    print("wrote", OUT)
    subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                    "format=duration,size", "-of", "default=nw=1", str(OUT)])


if __name__ == "__main__":
    main()