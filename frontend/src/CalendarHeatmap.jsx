import React, { useMemo, useState } from "react";
import { Figure, fmt, robustMax } from "./Explainer";

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

// Single-hue sequential ramp (light -> hot). Readable in greyscale too.
const RAMP = ["#fff5f0", "#fee0d2", "#fcbba1", "#fc9272", "#fb6a4a", "#ef3b2c", "#a50f15"];

// Fraction of the scale a square must reach to count as "hot". The scale is
// capped at p95 (see robustMax), so anything at or above this reads as the
// top colour without needing the axis to extend to the single worst day.
const HOT = 0.45;

function shade(v, max) {
  if (!v) return null;
  const t = Math.min(1, Math.sqrt(Math.min(v, max) / max));
  const i = Math.min(RAMP.length - 1, Math.floor(t * RAMP.length));
  return RAMP[i];
}

/* The grid uses a fixed 366-column leap-year layout so every row lines up, so
   column 60 always means 29 Feb. Resolve a column back to a real calendar date
   for the year being displayed, and return null for 29 Feb in common years
   (that square is genuinely empty in those rows). */
const LEAP_COL_MD = (() => {
  const out = [];
  const d = new Date(Date.UTC(2024, 0, 1));
  for (let i = 0; i < 366; i++) {
    out.push([d.getUTCMonth() + 1, d.getUTCDate()]);
    d.setUTCDate(d.getUTCDate() + 1);
  }
  return out;
})();

const isLeap = (y) => (y % 4 === 0 && y % 100 !== 0) || y % 400 === 0;

/* Month header positions are derived from the leap table itself. Hand-written
   starts silently drift by one column from March onward because 29 Feb pushes
   everything after February along — deriving them makes that impossible. */
const MONTH_STARTS = (() => {
  const starts = [];
  let prev = null;
  LEAP_COL_MD.forEach(([m], i) => {
    if (m !== prev) {
      starts.push(i + 1);
      prev = m;
    }
  });
  return starts;
})();

function doyToDate(col, year) {
  const md = LEAP_COL_MD[col - 1];
  if (!md) return null;
  const [m, day] = md;
  if (m === 2 && day === 29 && !isLeap(year)) return null;
  return `${year}-${String(m).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
}

export default function CalendarHeatmap({ data }) {
  const d = data && typeof data === "object" && !Array.isArray(data) ? data : {};
  const {
    years = [],
    day_of_year: doy = [],
    grid = [],
    last_observed_date = null,
    partial_last_year = false,
  } = d;
  const [hover, setHover] = useState(null);
  const max = useMemo(() => robustMax(grid, 0.95), [grid]);
  if (!grid.length || !years.length) return <div className="load">No calendar data</div>;

  const dim = doy.length;
  const total = grid.flat().reduce((a, b) => a + (Number.isFinite(b) ? b : 0), 0);
  // Rank rows by mean daily rate, not raw total, so the partial first and last
  // years cannot win or lose purely because of how much of the year we have.
  const best = grid
    .map((row, yi) => {
      const vals = row.filter((v) => Number.isFinite(v));
      const active = vals.filter((v) => v > 0);
      return {
        y: years[yi],
        v: vals.reduce((a, b) => a + b, 0),
        rate: active.length ? active.reduce((a, b) => a + b, 0) / active.length : 0,
      };
    })
    .sort((a, b) => b.rate - a.rate)[0];
  const hottest = grid.flat().reduce((a, b) => (Number.isFinite(b) && b > a ? b : a), 0);

  return (
    <Figure
      title="Burning activity calendar"
      subtitle={`${years[0]}–${years[years.length - 1]} · one row per year, one square per day${
        partial_last_year ? ` · ${years[years.length - 1]} is still in progress (record ends ${last_observed_date})` : ""
      }`}
      explain={
        <>
          <p>
            Each square is a single day. The colour encodes{" "}
            <b>how many distinct fire cells were burning that day</b> — darker means more
            of the region was on fire at once.
          </p>
          <p>
            Read it as a heat map of the fire calendar: the horizontal bright band that
            drifts up and down across the rows is <b>when the fire season happens</b>, and
            its thickness shows how long the season lasts. This is what lets you compare a
            region against itself over decades.
          </p>
          <p>
            Because both eras are on one harmonized scale, you can safely read a change
            from one row to the next as <b>real</b> change in fire activity, not a change
            of satellite. Blank squares mean no thermal detections at all.
          </p>
        </>
      }
      legend={
        <div className="legend">
          <span className="lg-label">Fewer</span>
          {RAMP.map((c) => (
            <i key={c} className="sw" style={{ background: c }} />
          ))}
          <span className="lg-label">More</span>
          <span className="lg-max">
            {fmt(max)}+ cells/day
            {hottest > max && (
              <em title={`Scale is capped at the 95th percentile so ordinary days stay legible. Worst single day in the record: ${fmt(hottest)}.`}>
                {" "}(capped; worst day {fmt(hottest)})
              </em>
            )}
          </span>
        </div>
      }
      note={`Total across the record: ${fmt(total)} cell-days. Busiest year by average daily rate: ${best.y} (${fmt(best.rate)} cells/day on days with detections).`}
    >
      <div className="heatmap-scroll">
        <div className="heatmap" style={{ "--cols": dim }}>
          <div className="hm-head">
            <span className="hm-corner" />
            <div className="hm-months">
              {MONTHS.map((m, i) => (
                <span
                  key={m}
                  style={{
                    gridColumn: `${MONTH_STARTS[i]} / span ${
                      Math.min(MONTH_STARTS[i + 1] ?? dim + 1, dim + 1) - MONTH_STARTS[i]
                    }`,
                  }}
                >
                  {m}
                </span>
              ))}
            </div>
          </div>

          {years.map((year, yi) => (
            <div className="hm-row" key={year}>
              <span className={`hm-year${partial_last_year && yi === years.length - 1 ? " partial" : ""}`}>
                {year}
              </span>
              <div className="hm-cells">
                {doy.map((d, di) => {
                  const v = grid[yi]?.[di] || 0;
                  const bg = shade(v, max);
                  const isHot = v >= max * HOT;
                  return (
                    <i
                      key={d}
                      className="hm-cell"
                      style={{ background: bg || "transparent" }}
                      onMouseEnter={() =>
                        setHover({ year, d, v, isHot, date: doyToDate(d, year) })
                      }
                    />
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className={`hm-tip ${hover ? "show" : ""}`}>
        {hover && (
          <>
            <b>
              {hover.date ? hover.date : `${hover.year} · 29 Feb (no such date)`}
            </b>
            <span>
              {hover.v ? `${fmt(hover.v)} fire cells burning` : "no detections"}
            </span>
            {hover.isHot && <span>at or above the top of the colour scale</span>}
          </>
        )}
      </div>
    </Figure>
  );
}
