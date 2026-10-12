import React, { useState } from "react";
import { Figure, fmt, weekLabel } from "./Explainer";

function severity(a) {
  const m = Math.abs(a);
  if (m >= 3) return { label: "extreme", cls: "s3" };
  if (m >= 2) return { label: "strong", cls: "s2" };
  if (m >= 1) return { label: "moderate", cls: "s1" };
  return { label: "mild", cls: "s0" };
}

export default function AnomalyList({ data }) {
  const [sign, setSign] = useState("hot");
  const rows = (Array.isArray(data) ? data : []).filter(
    (r) => r && r.anomaly != null && Number.isFinite(r.anomaly)
  );

  if (!rows.length) return <div className="load">No anomaly data</div>;

  const hot = [...rows].sort((a, b) => b.anomaly - a.anomaly).slice(0, 12);
  const cold = [...rows].sort((a, b) => a.anomaly - b.anomaly).slice(0, 8);
  const list = sign === "hot" ? hot : cold;
  const peakAbs = Math.max(...rows.map((r) => Math.abs(r.anomaly)), 1);
  const extreme = rows.filter((r) => Math.abs(r.anomaly) >= 2).length;

  return (
    <Figure
      title="Unusual weeks vs the region's own history"
      subtitle="Each week compared against the typical activity for that same week"
      explain={
        <>
          <p>
            An <b>anomaly</b> is how far a specific week differed from normal for{" "}
            <i>that same week of the year</i>. Comparing week 30 against week 30 (rather
            than against the whole year) means a winter week is never flagged just for
            being quiet.
          </p>
          <p>
            The number is expressed in units of that week&rsquo;s <b>normal spread</b> —
            specifically the p10&ndash;p90 range of its own history — so{" "}
            <b>+2 means twice that spread above the seasonal median</b>, an unusual event
            rather than merely a busy one. We use the robust p10&ndash;p90 spread instead of a
            standard deviation because fire activity is heavily skewed: a single enormous
            week would inflate &sigma; and mask every other anomaly. Because the score is
            scaled by each week&rsquo;s own spread, +2 means the same thing in a calm region
            and a volatile one.
          </p>
          <p>
            <b>+3 or beyond</b> is the threshold for treating a week as genuinely extreme;
            it happens {extreme} time{extreme === 1 ? "" : "s"} in this record. These are
            the weeks worth investigating for a specific fire or emissions event.
          </p>
        </>
      }
      legend={
        <div className="legend-row">
          <span className="key">
            <i className="swatch harm" /> Busier than normal
          </span>
          <span className="key">
            <i className="swatch cold" /> Quieter than normal
          </span>
          <span className="key">
            Bar length = size of the departure · ≥2 = strong, ≥3 = extreme
          </span>
        </div>
      }
    >
      <div className="seg">
        <button className={sign === "hot" ? "active" : ""} onClick={() => setSign("hot")}>
          Busiest departures
        </button>
        <button className={sign === "cold" ? "active" : ""} onClick={() => setSign("cold")}>
          Quietest departures
        </button>
      </div>

      <div className="anom-list">
        {list.map((r, i) => {
          const s = severity(r.anomaly);
          const w = (Math.abs(r.anomaly) / peakAbs) * 100;
          return (
            <div className="anom" key={i}>
              <span className="anom-yr">{r.year}</span>
              <span className="anom-wk">{weekLabel(r.ywoy)}</span>
              <span className="anom-bar">
                <i
                  className={`fill ${r.anomaly >= 0 ? "up" : "down"} ${s.cls}`}
                  style={{ width: `${w}%` }}
                />
              </span>
              <span className="anom-val">
                {fmt(r.value)}
                <em> cells/day</em>
              </span>
              <span className={`anom-delta ${r.anomaly >= 0 ? "up" : "down"}`}>
                {r.anomaly >= 0 ? "+" : "−"}
                {Math.abs(r.anomaly).toFixed(2)}
                <em> spread</em>
              </span>
              <span className={`tag ${s.cls}`}>{s.label}</span>
            </div>
          );
        })}
      </div>
      <p className="fig-note">
        <b>Units:</b> each score is the week&rsquo;s departure from its seasonal median, in
        multiples of that week&rsquo;s own p10&ndash;p90 spread (0 = exactly typical, 1 =
        one spread above). For the weeks listed, the typical p10&ndash;p90 band ran{" "}
        {fmt(Math.min(...list.map((r) => r.p10)))} &ndash;{" "}
        {fmt(Math.max(...list.map((r) => r.p90)))} cells/day, and the busiest of them
        averaged {fmt(Math.max(...list.map((r) => r.value)))} cells/day.
      </p>
    </Figure>
  );
}
