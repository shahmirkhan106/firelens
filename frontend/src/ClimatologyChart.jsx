import React, { useState } from "react";
import { Figure, fmt, weekLabel, robustMax } from "./Explainer";

const TICKS = [1, 5, 9, 14, 18, 22, 27, 31, 35, 40, 44, 48, 52];

export default function ClimatologyChart({ data }) {
  const d =
    data && typeof data === "object" && !Array.isArray(data) && Array.isArray(data.weeks)
      ? data
      : {};
  const { weeks = [], p10 = [], median = [], p90 = [] } = d;
  const [hover, setHover] = useState(null);
  const w = 860, h = 300, P = { l: 54, r: 16, t: 18, b: 40 };
  const pw = w - P.l - P.r, ph = h - P.t - P.b;

  if (!weeks.length) return <div className="load">No climatology data</div>;

  // p90 is heavy-tailed -- its peak week can be several times the median peak,
  // which flattens the whole curve into the bottom of the plot. Cap the axis at
  // p90-of-p90 and clamp, so the typical shape stays readable.
  const max = Math.max(robustMax(p90, 0.9), Math.max(...median, 0) * 1.15, 1);
  const clamp = (v) => Math.min(v, max);
  const x = (i) => P.l + (i / Math.max(1, weeks.length - 1)) * pw;
  const y = (v) => P.t + ph - (clamp(v) / max) * ph;
  const line = (arr) => arr.map((v, i) => `${x(i)},${y(v)}`).join(" ");
  const area = [
    ...p90.map((v, i) => `${x(i)},${y(v)}`),
    ...p10.map((v, i) => `${x(weeks.length - 1 - i)},${y(p10[weeks.length - 1 - i])}`),
  ].join(" ");
  const peak = median.indexOf(Math.max(...median));
  const clipped = p90.filter((v) => v > max).length;

  return (
    <Figure
      title="Typical fire season (climatology)"
      subtitle="Median activity per week, shaded between the quiet and busy years"
      explain={
        <>
          <p>
            This is the region's <b>normal</b> year, collapsed across the whole record.
            The red line is the <b>median</b> — half the years burned more, half less.
          </p>
          <p>
            The orange band spans the <b>10th–90th percentile</b>: it shows how much real
            years differ from each other. A <b>narrow band</b> means the fire season is
            predictable; a <b>wide band</b> means years are volatile and a single year's
            anomaly should be read cautiously.
          </p>
          <p>
            This baseline is what every anomaly is scored against, so it is the reference
            that makes 2020 in California or 2019 in NSW recognisable as an outlier
            rather than just a busy-looking year.
          </p>
        </>
      }
      legend={
        <div className="legend-row">
          <span className="key">
            <i className="swatch harm" /> Median (typical week)
          </span>
          <span className="key">
            <i className="swatch band" /> 10th–90th percentile (year-to-year spread)
          </span>
        </div>
      }
      note={`Busiest typical week: ${weekLabel(weeks[peak])} (${fmt(median[peak])} cells/day).`}
    >
      <svg
        viewBox={`0 0 ${w} ${h}`}
        className="main-svg"
        onMouseLeave={() => setHover(null)}
        onMouseMove={(e) => {
          const r = e.currentTarget.getBoundingClientRect();
          const px = ((e.clientX - r.left) / r.width) * w;
          const i = Math.round(((px - P.l) / pw) * (weeks.length - 1));
          setHover(i >= 0 && i < weeks.length ? i : null);
        }}
      >
        {[0, 1, 2, 3, 4].map((i) => (
          <g key={i}>
            <line x1={P.l} x2={w - P.r} y1={y(max * i / 4)} y2={y(max * i / 4)} stroke="#252d3d" />
            <text x={P.l - 8} y={y(max * i / 4) + 4} textAnchor="end" fontSize="10" fill="#7d8ba1">
              {fmt(max * i / 4)}
            </text>
          </g>
        ))}
        {TICKS.filter((wk) => wk <= weeks.length).map((wk) => (
          <text key={wk} x={x(wk - 1)} y={h - 14} fontSize="10" textAnchor="middle" fill="#7d8ba1">
            {weekLabel(weeks[wk - 1]).replace(" ", " ")}
          </text>
        ))}

        <polygon points={area} fill="#e4572e" opacity="0.16" />
        <polyline points={line(p10)} fill="none" stroke="#d9822b" strokeWidth="1" opacity="0.7" />
        <polyline points={line(p90)} fill="none" stroke="#d9822b" strokeWidth="1" opacity="0.7" />
        <polyline points={line(median)} fill="none" stroke="#e4572e" strokeWidth="2.4" />

        {hover != null && (
          <g>
            <line x1={x(hover)} x2={x(hover)} y1={P.t} y2={P.t + ph} stroke="#4a5568" />
            <circle cx={x(hover)} cy={y(median[hover])} r="4.5" fill="#e4572e" />
          </g>
        )}
      </svg>
      {hover != null && (
        <div className="tip">
          <b>{weekLabel(weeks[hover])}</b>
          <span>
            Typical <b>{fmt(median[hover])}</b> cells/day
          </span>
          <span>
            Usual range <b>{fmt(p10[hover])}</b> – <b>{fmt(p90[hover])}
            {p90[hover] > max ? " (off scale)" : ""}
            </b>
          </span>
        </div>
      )}
      {clipped > 0 && (
        <p className="fig-note">
          The vertical scale is capped so the typical shape stays readable;
          {` ${clipped} of ${p90.length} weeks have a p90 above the cap and are drawn at the top edge.`}
        </p>
      )}
    </Figure>
  );
}
