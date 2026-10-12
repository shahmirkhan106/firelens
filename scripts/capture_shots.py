#!/usr/bin/env python3
"""Capture rendered screenshots of every region × tab for the deck and video.

Unlike `firefox --screenshot` (which fires on the load event, before the app's
async data fetch resolves), this drives Playwright, waits for network idle and
for the loading placeholder to clear, then screenshots.

Usage:
    python scripts/capture_shots.py [--url http://127.0.0.1:4173] [--out docs/shots]
"""
import argparse
from pathlib import Path

from playwright.sync_api import sync_playwright

AOIS = ["california", "north-india", "amazon", "australia-nsw", "east-siberia"]
TABS = ["compare", "calendar", "climatology", "season", "anomalies"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:4173")
    ap.add_argument("--out", default="docs/shots")
    ap.add_argument("--width", type=int, default=1440)
    ap.add_argument("--height", type=int, default=900)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.firefox.launch()
        page = browser.new_page(viewport={"width": args.width, "height": args.height},
                                device_scale_factor=2)
        for aoi in AOIS:
            for tab in TABS:
                page.goto(f"{args.url}/?aoi={aoi}&tab={tab}")
                page.wait_for_load_state("networkidle")
                # The app shows a "Loading…" node until its fetch resolves; wait
                # for it to clear and a real child to render into the panel.
                page.wait_for_function(
                    "() => { const l = document.querySelector('.panel .load');"
                    " return !l && document.querySelector('.panel').children.length > 0; }",
                    timeout=30000)
                page.wait_for_timeout(700)  # let chart transitions settle
                fp = out / f"{aoi}_{tab}.png"
                page.screenshot(path=str(fp))
                print(f"  saved {fp}")
        browser.close()
    print(f"done -> {out}")


if __name__ == "__main__":
    main()