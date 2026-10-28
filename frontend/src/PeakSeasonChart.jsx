import React from "react";
import { Figure, fmt, weekLabel } from "./Explainer";

const TICKS = [1, 9, 18, 27, 36, 44, 52];

const COLORS = {
  band: "#d9822b",
  median: "#e4572e",
  grid: "#252d3d",
  text: "#7d8ba1",
};

export default function PeakSeasonChart({ data, aoi }) {
  const rows = (Array.isArray(data) ? data : []).filter(
    (r) => r && r.start_week != null && r.peak_week != null && r.end_week != null
  );
  if (!rows.length) return <div className="load">No peak-season data</div>;

  const w = 860, h = 320, P = { l: 54, r: 20, t: 24, b: 42 };
  const pw = w - P.l - P.r, ph = h - P.t - P.b;
  const years = rows.map((r) => r.year);
  const [minY, maxY] = [Math.min(...years), Math.max(...years)];
  const x = (yr) => P.l + ((yr - minY) / Math.max(1, maxY - minY)) * pw;
  const y = (wk) => P.t + ph - (wk / 53) * ph;
  const step = Math.max(1, Math.ceil(rows.length / 12));

  // trend of the peak week over the record
  const n = rows.length;
  const mx = rows.reduce((a, r) => a + r.year, 0) / n;
  const my = rows.reduce((a, r) => a + r.peak_week, 0) / n;
  const denom = rows.reduce((a, r) => a + (r.year - mx) ** 2, 0);
  const slope = denom
    ? rows.reduce((a, r) => a + (r.year - mx) * (r.peak_week - my), 0) / denom
    : 0;
  // Correlation + a rough 2-sigma band, so a "trend" is only claimed when the
  // dots actually line up. Peak week is an argmax, so it is noisy by nature and
  // will drift by a day or two from noise alone.
  const num = rows.reduce((a, r) => a + (r.year - mx) * (r.peak_week - my), 0);
  const ssY = rows.reduce((a, r) => a + (r.peak_week - my) ** 2, 0);
  const r2 = denom && ssY ? (num * num) / (denom * ssY) : 0;
  const resid = rows.reduce(
    (a, r) => a + (r.peak_week - (my + slope * (r.year - mx))) ** 2, 0
  );
  const slopeErr =
    n > 3 && denom
      ? Math.sqrt(resid / (n - 2) / denom) * 2
      : Infinity; // ~2 sigma
  const totalShift = slope * (rows[n - 1].year - rows[0].year);
  const early = rows.slice(0, 5).reduce((a, r) => a + r.peak_week, 0) / Math.min(5, n);
  const late = rows.slice(-5).reduce((a, r) => a + r.peak_week, 0) / Math.min(5, n);
  const shift = late - early;

  const downloadUrl = `/api/aoi/${aoi}/timeseries?sensor=harmonized&format=csv`;

  const trendText =
    Math.abs(totalShift) <= slopeErr
      ? "no clear trend in peak timing"
      : `${totalShift >= 0 ? "later" : "earlier"} by about ${Math.abs(
          totalShift
        ).toFixed(1)} weeks across the record (r² ${r2.toFixed(2)})`;

  return (
    <Figure
      title="Fire season timing and length, year by year"
      subtitle="Bar spans season start → end; the dot marks the busiest week"
      download={{ url: downloadUrl, filename: "peak_season.csv" }}
      explain={
        <>
          <p>
            Each vertical bar is one year's <b>fire season</b>, positioned by week of the
            year. The bar's <b>height = season length</b> (the span holding the middle 70%
            of that year's burning), and the <b>dot = the single busiest week</b>.
          </p>
          <p>
            Moving <b>left or right</b> means the season is arriving earlier or later;
            a <b>longer bar</b> means a longer season. Because all years are harmonized to
            the same scale, the horizontal position of a dot is comparable across the whole
            record — a shift here reflects real change, not a sensor swap.
          </p>
          <p>
            Treat the trend line with care: the busiest week is an <i>argmax</i>, so it
            jumps around by a week or two on noise alone. The summary below reports how
            strong that trend actually is, and says so plainly when there isn't one.
          </p>
        </>
      }
      legend={
        <div className="legend-row">
          <span className="key">
            <i className="swatch band" /> Season span (start → end)
          </span>
          <span className="key">
            <i className="swatch harm" /> Busiest week
          </span>
          <span className="key trend">{trendText}</span>
        </div>
      }
      note={`Season length averaged ${fmt(
        rows.reduce((a, r) => a + (r.end_week - r.start_week + 1), 0) / n
      )} weeks. First five years peaked at week ${early.toFixed(1)}, last five at week ${late.toFixed(
        1
      )} — a ${shift >= 0 ? "+" : "−"}${Math.abs(shift).toFixed(1)} week difference. Linear trend ${slope >= 0 ? "+" : "−"}${Math.abs(
        slope
      ).toFixed(3)} wk/yr (r² ${r2.toFixed(2)}, ±${slopeErr === Infinity ? "n/a" : slopeErr.toFixed(3)} at 2σ).`}
    >
      <svg viewBox={`0 0 ${w} ${h}`} className="main-svg">
        {TICKS.map((wk) => (
          <g key={wk}>
            <line x1={P.l} x2={w - P.r} y1={y(wk)} y2={y(wk)} stroke={COLORS.grid} />
            <text x={P.l - 8} y={y(wk) + 4} textAnchor="end" fontSize="10" fill={COLORS.text}>
              {weekLabel(wk).replace(" ", "\u00a0")}
            </text>
          </g>
        ))}
        {years.map((yr, i) =>
          i % step === 0 || i === n - 1 ? (
            <text key={yr} x={x(yr)} y={h - 16} fontSize="10" textAnchor="middle" fill={COLORS.text}>
              {yr}
            </text>
          ) : null
        )}

        {rows.map((r) => (
          <g key={r.year}>
            <line
              x1={x(r.year)}
              x2={x(r.year)}
              y1={y(r.start_week)}
              y2={y(r.end_week)}
              stroke={COLORS.band}
              strokeWidth="6"
              strokeLinecap="round"
              opacity="0.65"
            />
            <circle cx={x(r.year)} cy={y(r.peak_week)} r="4.5" fill={COLORS.median}>
              <title>{`${r.year}: ${weekLabel(r.start_week)} → ${weekLabel(r.end_week)}, peak ${weekLabel(r.peak_week)}, ${fmt(r.annual_total)} cell-days total over ${r.days ?? "?"} observed days`}</title>
            </circle>
          </g>
        ))}
      </svg>
      <p className="fig-note">Hover any dot for that year's season dates and annual total.</p>
    </Figure>
  );
}
