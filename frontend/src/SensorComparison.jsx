import React, { useMemo, useState } from "react";
import { Figure, Stat, fmt } from "./Explainer";

const BOUNDARY = "2012-01-01";

const COLORS = {
  modis: "#4cc2ff",
  viirs: "#c77dff",
  harmonized: "#e4572e",
};

function monthAgg(dates, values) {
  const buckets = new Map();
  for (let i = 0; i < dates.length; i++) {
    const v = values[i];
    if (v == null) continue;
    const m = dates[i].slice(0, 7);
    if (!buckets.has(m)) buckets.set(m, []);
    buckets.get(m).push(v);
  }
  return [...buckets.entries()].map(([m, v]) => [m, v.reduce((a, b) => a + b, 0) / v.length]);
}

export default function SensorComparison({ comparison, summary }) {
  const [hover, setHover] = useState(null);
  const [hidden, setHidden] = useState(() => new Set());
  const W = 860, H = 320, P = { l: 52, r: 16, t: 18, b: 34 };
  const pw = W - P.l - P.r, ph = H - P.t - P.b;

  const series = useMemo(() => {
    const d = comparison?.dates;
    if (!d?.length || !comparison?.modis) return null;
    const mm = new Map(monthAgg(d, comparison.modis));
    const vm = new Map(monthAgg(d, comparison.viirs));
    const hm = new Map(monthAgg(d, comparison.harmonized));
    const keys = [...new Set([...mm.keys(), ...vm.keys(), ...hm.keys()])].sort();
    const pick = (m) => keys.map((k) => [k, m.get(k) ?? null]);
    return { keys, modis: pick(mm), viirs: pick(vm), harmonized: pick(hm) };
  }, [comparison]);

  const toggle = (name) =>
    setHidden((prev) => {
      const next = new Set(prev);
      next.has(name) ? next.delete(name) : next.add(name);
      return next;
    });

  if (!series) return <div className="load">Loading comparison…</div>;

  const shown = (n) => !hidden.has(n);
  const all = [
    ...(shown("modis") ? series.modis.map((p) => p[1]) : []),
    ...(shown("viirs") ? series.viirs.map((p) => p[1]) : []),
    ...(shown("harmonized") ? series.harmonized.map((p) => p[1]) : []),
  ].filter((v) => v != null);
  const max = Math.max(...all, 1);
  const x = (i) => P.l + (i / Math.max(1, series.keys.length - 1)) * pw;
  const y = (v) => P.t + ph - (v / max) * ph;
  const path = (arr) =>
    arr
      .map(([k, v], i) =>
        v == null ? null : `${i === 0 || arr[i - 1][1] == null ? "M" : "L"}${x(i)},${y(v)}`
      )
      .filter(Boolean)
      .join(" ");
  const bx = series.keys.findIndex((k) => k >= BOUNDARY);

  const ticks = [];
  for (let i = 0; i <= 4; i++) ticks.push((max * i) / 4);
  const yearTicks = series.keys
    .map((k, i) => [k, i])
    .filter(([k]) => k.endsWith("-01"))
    .filter((_, i) => i % 3 === 0);

  const ov =
    summary && typeof summary === "object" && !Array.isArray(summary) && summary.overlap
      ? summary.overlap
      : {};
  const cal =
    summary && typeof summary === "object" && !Array.isArray(summary) && summary.calibration
      ? summary.calibration
      : {};
  const yr = Array.isArray(summary?.years) ? summary.years : null;
  const gapYears =
    summary?.gap_years && typeof summary.gap_years === "object"
      ? Object.entries(summary.gap_years).sort(([a], [b]) => a - b)
      : [];

  const hv = hover != null && series.keys[hover] ? series.keys[hover] : null;
  const at = (name) => (hv ? series[name][hover][1] : null);
  const legendItem = (name, label, note) => (
    <button
      type="button"
      className={`key key-toggle${hidden.has(name) ? " off" : ""}`}
      onClick={() => toggle(name)}
      aria-pressed={!hidden.has(name)}
    >
      <i
        className="swatch"
        style={{
          background: COLORS[name],
          height: name === "modis" ? 8 : 4,
          opacity: name === "modis" ? 0.55 : 1,
        }}
      />
      {label}
      <em>{note}</em>
    </button>
  );

  return (
    <div className="compare">
      <div className="stat-row">
        <Stat
          label="VIIRS over-reports cells"
          value={ov.cell_inflation ? `${ov.cell_inflation}×` : "—"}
          sub={ov.days ? `measured on ${fmt(ov.days)} shared days, ${ov.from} → ${ov.to}` : ""}
          tone="warn"
        />
        <Stat
          label="Calibration quality (R²)"
          value={cal.r2 ?? "—"}
          sub={cal.slope ? `VIIRS scaled by ${cal.slope}` : ""}
          tone={cal.r2 >= 0.85 ? "good" : "warn"}
        />
        <Stat
          label="Harmonized span"
          value={yr ? `${yr[0]}–${yr[yr.length - 1]}` : "—"}
          sub={summary?.days != null ? `${fmt(summary.days)} days · ${summary.seasons} fire seasons` : ""}
        />
      </div>

      {cal.r2 != null && cal.r2 < 0.7 && (
        <div className="warnbox">
          <b>The harmonization fit is weak for this region (R² = {cal.r2}).</b> The single
          linear VIIRS→MODIS correction explains little of the variance here — activity at
          this region&rsquo;s scale is dominated by short, explosive bursts (crop-residue
          burning in Oct–Nov) that a stable ratio cannot capture. The trend likely still
          reflects real change, but treat the exact harmonized numbers as approximate and
          prefer the raw-satellite comparison in the chart above.
        </div>
      )}

      {gapYears.length > 0 && (
        <div className="warnbox">
          <b>{gapYears.length} year{gapYears.length === 1 ? "" : "s"} of this region are missing data.</b>{" "}
          {gapYears.slice(0, 8).map(([y, d]) => `${y} (${d} days)`).join(", ")}
          {gapYears.length > 8 && ", …"} — far below this region&rsquo;s typical{" "}
          {summary?.typical_days_per_year ? `${summary.typical_days_per_year} ` : ""}
          observed days per year. These years are <b>under-observed, not quiet</b>: a hole in the
          satellite archive, not an absence of fire. Daily rates stay comparable because they are
          averaged over observed days only, but season-length and cumulative statistics for those
          years are unreliable.
        </div>
      )}

      <Figure
        title="The sensor problem, and its removal"
        subtitle="Monthly mean daily fire cells — each satellite on its own, then FireLens's harmonized result"
        explain={
          <>
            <p>
              This is the whole reason FireLens exists. <b>MODIS</b> (1&nbsp;km, 4 views/day) and{" "}
              <b>VIIRS</b> (375&nbsp;m, 2 views/day) watch the <i>same fires</i> but report very
              different numbers of them. Both keep flying after {BOUNDARY.slice(0, 4)}, so for
              over a decade we can measure the disagreement directly: on shared days VIIRS
              counted <b>{ov.cell_inflation ?? "—"}×</b> as many distinct fire cells.
            </p>
            <p>
              Because the two disagree this much, joining them into one timeline without
              correction would invent a climate trend that never happened — and the gap is not
              even constant, since it scales with how much fire is burning.
            </p>
            <p>
              The wide <span className="swatch" style={{ background: COLORS.modis }} /> band is
              MODIS. The thin <span className="swatch" style={{ background: COLORS.harmonized }} />{" "}
              line running down its middle is FireLens's output — it <i>follows</i> MODIS
              wherever MODIS actually observed, and only departs from it on days MODIS missed,
              using VIIRS counts divided onto the MODIS scale by a regression fitted on the
              overlap. Where the two coincide, that is the calibration working, not a bug.
            </p>
            <p>
              That overlap is the honest limitation of this dataset: because MODIS kept flying
              past {BOUNDARY.slice(0, 4)}, most of the "harmonized" record is really{" "}
              <i>measured MODIS</i>. Turn off the harmonized line to see the raw MODIS record
              underneath, or turn off MODIS to see how much the calibration is actually doing.
              Hover any month to read all three values.
            </p>
          </>
        }
        legend={
          <div className="legend-row">
            {legendItem("modis", "MODIS", "1 km, measured")}
            {legendItem("viirs", "VIIRS", "375 m, as reported")}
            {legendItem("harmonized", "Harmonized", "one continuous scale")}
          </div>
        }
      >
        <svg
          viewBox={`0 0 ${W} ${H}`}
          className="main-svg"
          onMouseLeave={() => setHover(null)}
          onMouseMove={(e) => {
            const r = e.currentTarget.getBoundingClientRect();
            const px = ((e.clientX - r.left) / r.width) * W;
            const i = Math.round(((px - P.l) / pw) * (series.keys.length - 1));
            setHover(i >= 0 && i < series.keys.length ? i : null);
          }}
        >
          {ticks.map((t, i) => (
            <g key={i}>
              <line x1={P.l} x2={W - P.r} y1={y(t)} y2={y(t)} stroke="#252d3d" />
              <text x={P.l - 8} y={y(t) + 4} textAnchor="end" fontSize="10" fill="#7d8ba1">
                {fmt(t)}
              </text>
            </g>
          ))}
          {yearTicks.map(([k, i]) => (
            <text key={k} x={x(i)} y={H - 12} fontSize="10" textAnchor="middle" fill="#7d8ba1">
              {k.slice(0, 4)}
            </text>
          ))}

          {bx > 0 && (
            <g>
              <line x1={x(bx)} x2={x(bx)} y1={P.t} y2={P.t + ph} stroke="#5a6b85" strokeDasharray="4 4" />
              <text x={x(bx) + 6} y={P.t + 12} fontSize="10" fill="#8fa0b8">
                2012: VIIRS begins
              </text>
            </g>
          )}

          {/* MODIS is drawn as a wide translucent band underneath. The harmonized
              series equals measured MODIS wherever MODIS observed, so a thin MODIS
              line would be entirely hidden by the orange line on top of it. */}
          {shown("modis") && (
            <path
              d={path(series.modis)}
              fill="none"
              stroke={COLORS.modis}
              strokeWidth="6"
              strokeOpacity="0.4"
              strokeLinejoin="round"
              strokeLinecap="round"
            />
          )}
          {shown("viirs") && (
            <path
              d={path(series.viirs)}
              fill="none"
              stroke={COLORS.viirs}
              strokeWidth="1.8"
              strokeDasharray="6 3"
            />
          )}
          {shown("harmonized") && (
            <path
              d={path(series.harmonized)}
              fill="none"
              stroke={COLORS.harmonized}
              strokeWidth="1.9"
              strokeLinejoin="round"
            />
          )}

          {hover != null && series.keys[hover] && (
            <g>
              <line x1={x(hover)} x2={x(hover)} y1={P.t} y2={P.t + ph} stroke="#4a5568" />
              {shown("modis") && at("modis") != null && (
                <circle cx={x(hover)} cy={y(at("modis"))} r="4.5" fill={COLORS.modis} />
              )}
              {shown("viirs") && at("viirs") != null && (
                <circle cx={x(hover)} cy={y(at("viirs"))} r="4" fill={COLORS.viirs} />
              )}
              {shown("harmonized") && at("harmonized") != null && (
                <circle cx={x(hover)} cy={y(at("harmonized"))} r="4" fill={COLORS.harmonized} />
              )}
            </g>
          )}
        </svg>
        {hv && (
          <div className="tip">
            <b>{hv}</b>
            <span>
              MODIS <b>{fmt(at("modis"))}</b> cells/day
            </span>
            <span>
              VIIRS <b>{fmt(at("viirs"))}</b> cells/day
            </span>
            <span>
              Harmonized <b>{fmt(at("harmonized"))}</b> cells/day
            </span>
          </div>
        )}
        <p className="fig-note">
          Monthly mean of daily counts. One cell ≈ a 1&nbsp;km² grid square containing at least
          one thermal detection that day. Click a legend entry to hide or show that series.
        </p>
      </Figure>
    </div>
  );
}
